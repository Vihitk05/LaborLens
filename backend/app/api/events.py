from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.core.event_bus import event_bus
import json
import asyncio

router = APIRouter()

@router.get("/stream/{task_id}")
async def stream_events(request: Request, task_id: str):
    pubsub = event_bus.get_pubsub()
    pubsub.subscribe(f"events:{task_id}")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
                if message:
                    try:
                        data = message['data'].decode('utf-8')
                        yield f"data: {data}\n\n"
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in event stream: {e}")
        finally:
            pubsub.unsubscribe(f"events:{task_id}")
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")