import { io } from 'socket.io-client';
let socket;
const socketUrl = () => import.meta.env.DEV ? 'http://localhost:5000' : window.location.origin;
export function connectRealtime(token, onStatus) { if (socket?.connected) return socket; socket?.disconnect(); socket = io(socketUrl(), { auth: { token }, transports: ['websocket', 'polling'], reconnection: true }); socket.on('connect', () => onStatus?.('connected')); socket.on('disconnect', () => onStatus?.('offline')); socket.io.on('reconnect_attempt', () => onStatus?.('reconnecting')); socket.on('connect_error', () => onStatus?.('offline')); return socket; }
export function disconnectRealtime() { socket?.disconnect(); socket = undefined; }
export function joinRoom(type, id) { socket?.emit('room.join', { type, id }); }
export function leaveRoom(type, id) { socket?.emit('room.leave', { type, id }); }
export function onRealtime(event, handler) { socket?.on(event, handler); return () => socket?.off(event, handler); }
