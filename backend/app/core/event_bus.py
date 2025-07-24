import redis
from app.config import settings
import json
from fastapi import FastAPI

class EventBus:
    def __init__(self):
        self.redis = None

    def connect(self):
        if self.redis is None:
            self.redis = redis.Redis.from_url(settings.EVENT_BUS_URL)
            try:
                # Test the connection
                self.redis.ping()
            except redis.ConnectionError:
                self.redis = None
                raise

    def publish(self, task_id: str, event: dict):
        if self.redis is None:
            self.connect()
        channel = f"events:{task_id}"
        self.redis.publish(channel, json.dumps(event))

    def get_pubsub(self):
        if self.redis is None:
            self.connect()
        return self.redis.pubsub()

event_bus = EventBus()

def connect_event_bus(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        event_bus.connect()

    @app.on_event("shutdown")
    async def shutdown_event():
        if event_bus.redis:
            event_bus.redis.close()