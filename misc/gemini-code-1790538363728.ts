// server/signalingTypes.ts
export type ClientEventType = 
  | 'CLIENT_CAMERA_DISABLED'
  | 'REQUEST_CAMERA_MUTUAL_REENABLE';

export type ServerBroadcastType = 
  | 'PEER_CAMERA_DISABLED'
  | 'ROOM_FORCE_AVATAR_MODE';

export interface RoomSession {
  roomId: string;
  clients: Map<string, WebSocket>;
  cameraActive: boolean;
}