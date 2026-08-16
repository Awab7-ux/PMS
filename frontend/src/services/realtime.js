import { io } from 'socket.io-client';

let socket;
const rooms = new Set();
const socketUrl = () => import.meta.env.DEV ? 'http://localhost:5000' : window.location.origin;
const roomKey = (type, id) => `${type}:${id}`;

function rejoinRooms() {
  rooms.forEach(room => {
    const [type, ...parts] = room.split(':');
    socket?.emit('room.join', { type, id: parts.join(':') });
  });
}

export function connectRealtime(token, onStatus) {
  if (socket?.connected) return socket;
  socket?.disconnect();
  socket = io(socketUrl(), { auth: { token }, transports: ['websocket', 'polling'], reconnection: true });
  socket.on('connect', () => { rejoinRooms(); onStatus?.('connected'); });
  socket.on('disconnect', () => onStatus?.('offline'));
  socket.io.on('reconnect_attempt', () => onStatus?.('reconnecting'));
  socket.on('connect_error', () => onStatus?.('offline'));
  return socket;
}

export function disconnectRealtime() { rooms.clear(); socket?.disconnect(); socket = undefined; }
export function joinRoom(type, id) { if (!type || !id) return; rooms.add(roomKey(type, id)); socket?.emit('room.join', { type, id }); }
export function leaveRoom(type, id) { if (!type || !id) return; rooms.delete(roomKey(type, id)); socket?.emit('room.leave', { type, id }); }
export function onRealtime(event, handler) { socket?.on(event, handler); return () => socket?.off(event, handler); }
