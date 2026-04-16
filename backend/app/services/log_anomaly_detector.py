"""
LSTM Autoencoder for Log Anomaly Detection

Architecture (per PRD):
  Input (60 timesteps × 4 features)
    → LSTM Encoder (64 units) → Bottleneck (32 units)
    → LSTM Decoder (64 units)
    → Output (reconstructed 60×4 sequence)
  Loss: MSE between input and reconstruction

Generates synthetic training data representing 4 weeks of normal server
metrics, trains the autoencoder (~30s on CPU), then uses reconstruction
error thresholding to flag anomalies.
"""

import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)

# ── Model Definition ───────────────────────────────────────────────────

class LSTMAutoencoder(nn.Module):
    """
    LSTM Autoencoder for time-series anomaly detection.
    Encoder compresses 60×4 input into a 32-dim bottleneck.
    Decoder reconstructs the original sequence.
    High reconstruction error = anomaly.
    """

    def __init__(self, n_features: int = 4, hidden_size: int = 64, bottleneck: int = 32):
        super().__init__()
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.bottleneck = bottleneck

        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            batch_first=True,
        )
        self.encoder_fc = nn.Linear(hidden_size, bottleneck)

        # Decoder
        self.decoder_fc = nn.Linear(bottleneck, hidden_size)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            batch_first=True,
        )
        self.output_layer = nn.Linear(hidden_size, n_features)

    def forward(self, x):
        # x shape: (batch, seq_len, n_features)
        seq_len = x.size(1)

        # Encode — use final hidden state
        _, (h_n, _) = self.encoder_lstm(x)
        # h_n shape: (1, batch, hidden_size)
        bottleneck = torch.relu(self.encoder_fc(h_n.squeeze(0)))
        # bottleneck shape: (batch, bottleneck_size)

        # Decode — repeat bottleneck across timesteps
        decoded = torch.relu(self.decoder_fc(bottleneck))
        # decoded shape: (batch, hidden_size)
        decoded = decoded.unsqueeze(1).repeat(1, seq_len, 1)
        # decoded shape: (batch, seq_len, hidden_size)

        decoded, _ = self.decoder_lstm(decoded)
        output = self.output_layer(decoded)
        # output shape: (batch, seq_len, n_features)
        return output


# ── Synthetic Data Generation ──────────────────────────────────────────

def generate_normal_metrics(n_days: int = 28, interval_minutes: int = 1) -> np.ndarray:
    """
    Generate synthetic 'normal' server metrics for training.

    4 features per timestep:
      0: error_rate (errors/min)      — baseline ~2, daily pattern
      1: response_time_ms             — baseline ~150ms, daily pattern
      2: request_count (reqs/min)     — baseline ~500, daily pattern
      3: 5xx_rate (proportion)        — baseline ~0.002

    Returns shape: (n_timesteps, 4)
    """
    n_points = n_days * 24 * 60 // interval_minutes
    t = np.arange(n_points)

    # Daily cycle (peak during business hours)
    daily_cycle = np.sin(2 * np.pi * t / (24 * 60 / interval_minutes) - np.pi / 2) * 0.3 + 0.7

    error_rate = 2.0 * daily_cycle + np.random.normal(0, 0.3, n_points)
    response_time = 150.0 * daily_cycle + np.random.normal(0, 10, n_points)
    request_count = 500.0 * daily_cycle + np.random.normal(0, 30, n_points)
    five_xx_rate = 0.002 * daily_cycle + np.abs(np.random.normal(0, 0.0005, n_points))

    # Clamp to realistic ranges
    error_rate = np.clip(error_rate, 0, None)
    response_time = np.clip(response_time, 10, None)
    request_count = np.clip(request_count, 1, None)
    five_xx_rate = np.clip(five_xx_rate, 0, 0.1)

    data = np.stack([error_rate, response_time, request_count, five_xx_rate], axis=1)
    return data.astype(np.float32)


def create_sequences(data: np.ndarray, window_size: int = 60) -> np.ndarray:
    """Create rolling windows of `window_size` timesteps."""
    sequences = []
    for i in range(len(data) - window_size):
        sequences.append(data[i : i + window_size])
    return np.array(sequences)


def inject_anomalies(data: np.ndarray, n_anomalies: int = 5, duration: int = 15) -> tuple:
    """
    Inject anomaly spikes into test data.
    Returns (modified_data, anomaly_indices).
    """
    data = data.copy()
    anomaly_mask = np.zeros(len(data), dtype=bool)

    for _ in range(n_anomalies):
        start = np.random.randint(60, len(data) - duration - 60)
        # Spike error rate and response time, drop request count
        data[start : start + duration, 0] *= np.random.uniform(8, 15)   # error spike
        data[start : start + duration, 1] *= np.random.uniform(3, 6)    # latency spike
        data[start : start + duration, 3] *= np.random.uniform(10, 25)  # 5xx spike
        anomaly_mask[start : start + duration] = True

    return data, anomaly_mask


# ── Training & Inference ───────────────────────────────────────────────

_trained_model = None
_threshold = None
_scaler_mean = None
_scaler_std = None

def _normalize(data: np.ndarray) -> np.ndarray:
    """Z-score normalize using training statistics."""
    global _scaler_mean, _scaler_std
    return (data - _scaler_mean) / (_scaler_std + 1e-8)


def train_model(epochs: int = 30, window_size: int = 60) -> Dict[str, Any]:
    """
    Train the LSTM Autoencoder on synthetic normal data.
    Computes the anomaly threshold from training reconstruction errors.
    """
    global _trained_model, _threshold, _scaler_mean, _scaler_std

    logger.info("Generating 28 days of synthetic normal log metrics …")
    raw_data = generate_normal_metrics(n_days=28)

    # Fit normalizer
    _scaler_mean = raw_data.mean(axis=0)
    _scaler_std = raw_data.std(axis=0)
    normalized = _normalize(raw_data)

    sequences = create_sequences(normalized, window_size)
    logger.info(f"Created {len(sequences)} training sequences of shape {sequences.shape}")

    dataset = TensorDataset(torch.FloatTensor(sequences))
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    model = LSTMAutoencoder(n_features=4, hidden_size=64, bottleneck=32)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    model.train()
    losses = []
    for epoch in range(epochs):
        epoch_loss = 0.0
        for (batch,) in loader:
            optimizer.zero_grad()
            output = model(batch)
            loss = criterion(output, batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        avg_loss = epoch_loss / len(loader)
        losses.append(avg_loss)
        if (epoch + 1) % 10 == 0:
            logger.info(f"  Epoch {epoch+1}/{epochs} — loss: {avg_loss:.6f}")

    # Compute threshold from training data reconstruction errors
    model.eval()
    all_errors = []
    with torch.no_grad():
        for (batch,) in loader:
            output = model(batch)
            error = torch.mean((output - batch) ** 2, dim=(1, 2)).numpy()
            all_errors.extend(error)

    _threshold = float(np.percentile(all_errors, 99))
    _trained_model = model

    logger.info(f"Training complete. Anomaly threshold (99th pctl): {_threshold:.6f}")
    return {
        "epochs": epochs,
        "final_loss": round(losses[-1], 6),
        "threshold": round(_threshold, 6),
        "training_sequences": len(sequences),
    }


def detect_anomalies(window_size: int = 60) -> Dict[str, Any]:
    """
    Generate test data with injected anomalies, run inference,
    and return a timeline of detections.
    """
    global _trained_model, _threshold

    if _trained_model is None:
        logger.info("Model not trained yet — training now …")
        train_info = train_model()
    else:
        train_info = None

    # Generate 2 days of test data with anomalies
    test_raw = generate_normal_metrics(n_days=2)
    test_data, ground_truth = inject_anomalies(test_raw, n_anomalies=4, duration=12)

    normalized = _normalize(test_data)
    sequences = create_sequences(normalized, window_size)

    _trained_model.eval()
    reconstruction_errors = []
    with torch.no_grad():
        tensor_seq = torch.FloatTensor(sequences)
        # Process in batches for memory efficiency
        for i in range(0, len(tensor_seq), 128):
            batch = tensor_seq[i : i + 128]
            output = _trained_model(batch)
            errors = torch.mean((output - batch) ** 2, dim=(1, 2)).numpy()
            reconstruction_errors.extend(errors)

    reconstruction_errors = np.array(reconstruction_errors)

    # Build timeline
    base_time = datetime.utcnow() - timedelta(days=2)
    timeline = []
    detected_count = 0
    total_ground_truth = int(ground_truth[window_size:].sum())

    for i, error in enumerate(reconstruction_errors):
        timestamp = base_time + timedelta(minutes=i)
        is_anomaly = float(error) > _threshold
        is_ground_truth = bool(ground_truth[i + window_size]) if (i + window_size) < len(ground_truth) else False

        if is_anomaly:
            detected_count += 1

        timeline.append({
            "timestamp": timestamp.isoformat(),
            "reconstruction_error": round(float(error), 6),
            "threshold": round(_threshold, 6),
            "is_anomaly": is_anomaly,
            "is_ground_truth_anomaly": is_ground_truth,
            # Raw metric values for display
            "error_rate": round(float(test_data[i + window_size][0]), 2) if (i + window_size) < len(test_data) else 0,
            "response_time_ms": round(float(test_data[i + window_size][1]), 1) if (i + window_size) < len(test_data) else 0,
            "request_count": round(float(test_data[i + window_size][2]), 0) if (i + window_size) < len(test_data) else 0,
            "five_xx_rate": round(float(test_data[i + window_size][3]), 4) if (i + window_size) < len(test_data) else 0,
        })

    # Downsample timeline for API response (every 5 minutes instead of every 1)
    sampled_timeline = timeline[::5]

    # Collect detected anomaly windows
    anomaly_windows = []
    in_window = False
    window_start = None
    for point in timeline:
        if point["is_anomaly"] and not in_window:
            in_window = True
            window_start = point["timestamp"]
        elif not point["is_anomaly"] and in_window:
            in_window = False
            anomaly_windows.append({
                "start": window_start,
                "end": point["timestamp"],
                "severity": "critical" if point.get("error_rate", 0) > 15 else "warning",
                "description": f"Reconstruction error exceeded threshold — error rate spike detected",
            })

    return {
        "model_info": train_info or {"status": "using_cached_model"},
        "threshold": round(_threshold, 6),
        "total_points": len(timeline),
        "anomalies_detected": detected_count,
        "ground_truth_anomalies": total_ground_truth,
        "anomaly_windows": anomaly_windows,
        "timeline": sampled_timeline,
    }
