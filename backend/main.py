import asyncio
import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.agent_loop import AgentLoop

app = FastAPI(title="Autonomous AI Creation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = AgentLoop()
is_running = False

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/")
def get_status():
    return {
        "status": "active",
        "engine_running": is_running,
        "history_count": len(agent.history)
    }

@app.post("/start")
async def start_engine():
    global is_running
    if not is_running:
        is_running = True
        asyncio.create_task(run_autonomous_loop())
    return {"status": "started", "is_running": is_running}

@app.post("/stop")
def stop_engine():
    global is_running
    is_running = False
    return {"status": "stopped", "is_running": is_running}

@app.post("/step")
async def step_engine():
    log = agent.run_cycle()
    await manager.broadcast(log)
    return log

async def run_autonomous_loop():
    global is_running
    while is_running:
        try:
            log = agent.run_cycle()
            await manager.broadcast(log)
            # Sleep between cycles to manage Groq rate limits
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"Error in agent loop: {e}")
            await asyncio.sleep(10)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
