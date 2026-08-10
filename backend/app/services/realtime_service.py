"""Real-time event abstraction for future WebSocket integration."""


class RealtimeService:
    _subscribers: dict[str, list] = {}

    @classmethod
    def publish(cls, channel: str, event: str, data: dict) -> None:
        """Publish event to channel. In production, replace with Redis pub/sub or WebSocket."""
        payload = {"channel": channel, "event": event, "data": data}
        for callback in cls._subscribers.get(channel, []):
            try:
                callback(payload)
            except Exception:
                pass

    @classmethod
    def subscribe(cls, channel: str, callback) -> None:
        cls._subscribers.setdefault(channel, []).append(callback)

    @classmethod
    def notify_task_update(cls, project_id: str, task_data: dict) -> None:
        cls.publish(f"project:{project_id}", "task.updated", task_data)

    @classmethod
    def notify_comment(cls, task_id: str, comment_data: dict) -> None:
        cls.publish(f"task:{task_id}", "comment.added", comment_data)

    @classmethod
    def notify_notification(cls, user_id: str, notification_data: dict) -> None:
        cls.publish(f"user:{user_id}", "notification.new", notification_data)
