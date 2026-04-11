import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";

const app = express();
const httpServer = createServer(app);

const io = new Server(httpServer, {
  path: "/ws",
  cors: {
    origin: [
      "http://localhost",
      "http://localhost:80",
      "http://localhost:3000",
      "http://127.0.0.1",
      "http://127.0.0.1:3000",
    ],
    methods: ["GET", "POST"],
    credentials: true,
  },
});

io.on("connection", (socket) => {
  console.log("client connected", socket.id);
  socket.emit("hello", { from: "auditr-realtime" });
});

const port = Number(process.env.PORT || 3001);
httpServer.listen(port, "0.0.0.0", () => {
  console.log(`Socket.IO listening on ${port} (path /ws)`);
});
