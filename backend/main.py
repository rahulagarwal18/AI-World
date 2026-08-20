import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.agent_loop import AgentLoop

agent = AgentLoop()
is_running = True

async def run_autonomous_loop():
    global is_running
    logger = logging.getLogger("AutoLoop")
    logger.info("Starting autonomous 24/7 background creation loop...")
    while is_running:
        try:
            log = agent.run_cycle()
            logger.info(f"Completed cycle: {log.get('action', {}).get('action')}")
            # Sleep 15 seconds between cycles to manage Groq rate limits cleanly
            await asyncio.sleep(15)
        except Exception as e:
            logger.error(f"Error in agent loop: {e}")
            await asyncio.sleep(20)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch autonomous 24/7 background task
    task = asyncio.create_task(run_autonomous_loop())
    yield
    # Shutdown
    global is_running
    is_running = False
    task.cancel()

app = FastAPI(title="Autonomous AI Creation Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
def get_status():
    return {
        "status": "active",
        "engine": "Groq Autonomous AI Engine",
        "mode": "24/7 Continuous Cloud Creation",
        "history_count": len(agent.history),
        "recent_action": agent.history[-1] if agent.history else None
    }

@app.get("/history")
@app.get("/api/history")
def get_history():
    return {"history": agent.history}
