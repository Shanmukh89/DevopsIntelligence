import { io, type Socket } from "socket.io-client";

const DEFAULT_ORIGIN =
  process.env["NEXT_PUBLIC_SOCKET_URL"] ?? "http://localhost:3001";
const SOCKET_PATH = "/ws";

const MAX_DELAY_MS = 30_000;
const INITIAL_DELAY_MS = 500;

export type RealtimeEventMap = {
  "build:completed": (payload: {
    buildId: string;
    repositoryId?: string;
  }) => void;
  "pr:reviewed": (payload: {
    prId: string;
    repositoryId?: string;
  }) => void;
  "alert:new": (payload: { message: string; severity?: string }) => void;
  hello: (payload: { from?: string }) => void;
};

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (socket) {
    return socket;
  }

  socket = io(DEFAULT_ORIGIN, {
    path: SOCKET_PATH,
    transports: ["websocket", "polling"],
    withCredentials: true,
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: INITIAL_DELAY_MS,
    reconnectionDelayMax: MAX_DELAY_MS,
    randomizationFactor: 0.5,
  });

  return socket;
}

export function disconnectSocket(): void {
  socket?.removeAllListeners();
  socket?.disconnect();
  socket = null;
}

export function onRealtimeEvent<K extends keyof RealtimeEventMap>(
  event: K,
  handler: RealtimeEventMap[K],
): () => void {
  const s = getSocket();
  s.on(event as string, handler as (...args: unknown[]) => void);
  return () => {
    s.off(event as string, handler as (...args: unknown[]) => void);
  };
}
