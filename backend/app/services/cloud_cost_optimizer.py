import logging
import random
import pandas as pd
from sqlalchemy import text
from sklearn.cluster import KMeans
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

def generate_mock_cur_data() -> pd.DataFrame:
    """
    Generates a mock AWS Cost and Usage Report (CUR) dataset.
    Features: cost_per_day, utilization_percent
    """
    data = []
    # 1. Idle resources (waste): Low util, varying cost
    for i in range(15):
        data.append({
            "resource_id": f"i-xyz{random.randint(1000, 9999)}_idle",
            "resource_type": "EC2",
            "cost_per_day": random.uniform(5.0, 50.0),
            "utilization_percent": random.uniform(0.1, 5.0)
        })
    
    # 2. Healthy resources: High util, varying cost
    for i in range(40):
        data.append({
            "resource_id": f"db-abc{random.randint(1000, 9999)}_active",
            "resource_type": "RDS",
            "cost_per_day": random.uniform(20.0, 100.0),
            "utilization_percent": random.uniform(60.0, 95.0)
        })
        
    return pd.DataFrame(data)

def analyze_costs():
    """
    Celery task to analyze cloud costs, cluster them with K-Means to find anomalies,
    and save recommendations to the DB.
    """
    logger.info("Starting scheduled cloud cost analysis")
    
    df = generate_mock_cur_data()
    
    if df.empty:
        return
        
    # K-Means clustering on utilization and cost
    # We want to identify the cluster that represents "High cost, Low utilization"
    X = df[["cost_per_day", "utilization_percent"]].values
    
    # 2 clusters: Healthy vs Idle/Waste
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X)
    
    # Find which cluster represents waste (lower average utilization)
    cluster_means = df.groupby("cluster")["utilization_percent"].mean()
    waste_cluster = cluster_means.idxmin()
    
    waste_resources = df[df["cluster"] == waste_cluster]
    
    db = SessionLocal()
    try:
        profile = db.execute(text("SELECT id FROM profiles LIMIT 1")).fetchone()
        if not profile:
            logger.warning("No profiles found to assign cloud costs.")
            return
            
        profile_id = profile[0]
        
        for _, row in waste_resources.iterrows():
            monthly_saving = row["cost_per_day"] * 30
            resource_type = row["resource_type"]
            rec = f"Downsize or terminate this {resource_type} instance. Average utilization is only {row['utilization_percent']:.1f}%."
            
            try:
                db.execute(
                    text(
                        "INSERT INTO cloud_costs (profile_id, resource_id, resource_type, provider, potential_saving_monthly, recommendation, status) "
                        "VALUES (:pid, :rid, :rtype, 'aws', :saving, :rec, 'open') "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "pid": profile_id,
                        "rid": row["resource_id"],
                        "rtype": resource_type,
                        "saving": round(monthly_saving, 2),
                        "rec": rec
                    }
                )
            except Exception as e:
                logger.warning(f"Could not insert cloud cost: {e}")
                db.rollback()
                
        db.commit()
        logger.info(f"Identified {len(waste_resources)} wasteful resources.")
    except Exception as e:
        logger.error(f"Cloud cost analysis failed: {e}")
    finally:
        db.close()
