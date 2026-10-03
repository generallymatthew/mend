// server/signalingServer.ts
import { WebSocketServer, WebSocket } from 'ws';

export class VideoParitySignalingServer {
  private rooms: Map<string, RoomSession> = new Map();

  public handleClientMessage(
    ws: WebSocket,
    roomId: string,
    userId: string,
    message: { type: ClientEventType; payload?: unknown }
  ) {
    const session = this.rooms.get(roomId);
    if (!session) return;

    switch (message.type) {
      case 'CLIENT_CAMERA_DISABLED': {
        // Enforce symmetric teardown across the room
        session.cameraActive = false;

        const broadcastPayload = JSON.stringify({
          type: 'PEER_CAMERA_DISABLED',
          roomId,
          timestamp: Date.now(),
        });

        // Broadcast to ALL participants in the room
        session.clients.forEach((clientWs) => {
          if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(broadcastPayload);
          }
        });
        break;
      }
    }
  }
}