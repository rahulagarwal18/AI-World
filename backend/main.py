import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.agent_loop import AgentLoop
from backend.config import Config

_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentLoop()
    return _agent_instance

# Pre-instantiate agent so API endpoints respond in < 1ms
agent_engine = get_agent()

is_running = True

async def run_autonomous_loop():
    """Runs the 24/7 background creation loop in worker thread so event loop stays 100% responsive"""
    logger = logging.getLogger("BackgroundLoop")
    logger.info("Starting background autonomous creation loop...")
    while is_running:
        try:
            ag = get_agent()
            log = await asyncio.to_thread(ag.run_cycle)
            logger.info(f"Completed cycle action: {log.get('action') if isinstance(log, dict) else log}")
        except Exception as e:
            logger.error(f"Error in autonomous loop: {e}")
        await asyncio.sleep(65)

async def self_keep_alive():
    """Pings public URL every 4 minutes to ensure zero spin-down delay"""
    import httpx
    logger = logging.getLogger("KeepAlive")
    urls = [
        "https://autowork-world-ai.onrender.com/api",
        "https://ai-world-rudu.onrender.com/api"
    ]
    while True:
        await asyncio.sleep(240)
        for url in urls:
            try:
                async with httpx.AsyncClient() as client:
                    await client.get(url, timeout=10)
                logger.info(f"Keep-Alive ping sent to {url}")
            except Exception as e:
                logger.warning(f"Keep-Alive ping error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_autonomous_loop())
    ping_task = asyncio.create_task(self_keep_alive())
    yield
    global is_running
    is_running = False
    task.cancel()
    ping_task.cancel()

app = FastAPI(title="Autonomous AI Creation Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.head("/")
@app.get("/api")
@app.head("/api")
def get_status():
    ag = get_agent()
    return {
        "status": "active",
        "engine": "Groq Autonomous AI Engine",
        "platform": "Vercel & Cloud Compatible",
        "history_count": len(ag.history),
        "recent_action": ag.history[-1] if ag.history else None,
        "viewer_url": "/viewer"
    }

@app.get("/history")
@app.get("/api/history")
def get_history():
    ag = get_agent()
    clean_history = [
        item for item in ag.history
        if isinstance(item, dict)
        and item.get("action", {}).get("action") != "reflect"
        and "error" not in str(item.get("action", {}).get("thought", "")).lower()
    ]
    return {"history": clean_history}

@app.post("/step")
@app.post("/api/step")
@app.get("/step")
@app.get("/api/step")
def trigger_step():
    """Triggers an autonomous creation step (Serverless & Cron Compatible)"""
    try:
        ag = get_agent()
        log = ag.run_cycle()
        return log
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/gdrive")
def debug_gdrive():
    ag = get_agent()
    res = ag.gdrive.sync_file_info("test_gdrive_sync.txt", "Google Drive API Test File from AI Engine")
    return {
        "folder_id": ag.gdrive.folder_id,
        "gdrive_result": res
    }

@app.get("/files")
@app.get("/api/files")
def list_files():
    ag = get_agent()
    return {"files": ag.workspace.list_files()}

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

@app.get("/preview/{file_path:path}")
def preview_file(file_path: str):
    target = (Config.WORKSPACE_DIR / file_path).resolve()
    if not target.exists():
        return Response(content="File not found", status_code=404, headers=NO_CACHE_HEADERS)
    return FileResponse(target, headers=NO_CACHE_HEADERS)

@app.get("/viewer")
def get_visual_viewer():
    template_path = Path(__file__).parent / "templates" / "viewer.html"
    return FileResponse(template_path, headers=NO_CACHE_HEADERS)
