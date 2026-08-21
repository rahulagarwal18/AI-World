import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.agent_loop import AgentLoop
from backend.config import Config

_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        try:
            _agent_instance = AgentLoop()
        except Exception as e:
            logging.error(f"Error initializing AgentLoop: {e}")
            _agent_instance = None
    return _agent_instance

class DummyAgent:
    def __init__(self):
        self.history = []
        self.workspace = type('obj', (object,), {'list_files': lambda: []})()
        self.gdrive = type('obj', (object,), {'folder_id': '16JoYjvINixhs1TRgZLplF9mdIMXl-eP0', 'sync_file_info': lambda f, c: {'status': 'initializing'}})()

    def run_cycle(self):
        ag = get_agent()
        if ag:
            return ag.run_cycle()
        return {"status": "initializing", "action": {"action": "reflect", "thought": "Initializing Agent Loop..."}}

agent = DummyAgent()

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
@app.get("/api")
def get_status():
    return {
        "status": "active",
        "engine": "Groq Autonomous AI Engine",
        "platform": "Vercel & Cloud Compatible",
        "history_count": len(agent.history),
        "recent_action": agent.history[-1] if agent.history else None,
        "viewer_url": "/viewer"
    }

@app.get("/history")
@app.get("/api/history")
def get_history():
    return {"history": agent.history}

@app.post("/step")
@app.post("/api/step")
@app.get("/step")
@app.get("/api/step")
def trigger_step():
    """Triggers an autonomous creation step (Serverless & Cron Compatible)"""
    try:
        log = agent.run_cycle()
        return log
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/gdrive")
def debug_gdrive():
    res = agent.gdrive.sync_file_info("test_gdrive_sync.txt", "Google Drive API Test File from AI Engine")
    return {
        "folder_id": agent.gdrive.folder_id,
        "gdrive_result": res
    }

@app.get("/files")
@app.get("/api/files")
def list_files():
    return {"files": agent.workspace.list_files()}

@app.get("/preview/{file_path:path}")
def preview_file(file_path: str):
    target = (Config.WORKSPACE_DIR / file_path).resolve()
    if not target.exists():
        return Response(content="File not found", status_code=404)
    return FileResponse(target)

@app.get("/viewer", response_class=HTMLResponse)
def get_visual_viewer():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Creation Engine - Live Visual Viewer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        </style>
    </head>
    <body class="p-6">
        <div class="max-w-7xl mx-auto space-y-6">
            <!-- Header -->
            <header class="glass p-6 rounded-2xl flex justify-between items-center shadow-2xl">
                <div>
                    <h1 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                        🤖 AI World Creation Hub
                    </h1>
                    <p class="text-slate-400 text-sm mt-1">Self-Directed Creation Engine • Fully Automatic 24/7 Mode Active</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 rounded-xl text-emerald-400 text-xs font-semibold">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                        <span>Auto-Creation Active</span>
                    </div>
                    <a href="https://github.com/rahulagarwal18/AI-World/tree/main/workspace" target="_blank" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs rounded-xl font-semibold transition border border-slate-700">
                        🐙 GitHub
                    </a>
                </div>
            </header>

            <!-- Grid Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left Column: Active Creations & Thoughts -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-xl font-bold text-cyan-400 flex items-center gap-2">
                        <span>⚡</span> Live Action Stream
                    </h2>
                    <div id="actions-list" class="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                        <p class="text-slate-500 text-sm">Loading AI activity stream...</p>
                    </div>
                </div>

                <!-- Middle Column: Generated Files & Workspace Tree -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-xl font-bold text-blue-400 flex items-center gap-2">
                        <span>📁</span> Created Files & Apps
                    </h2>
                    <div id="files-list" class="space-y-2 max-h-[600px] overflow-y-auto">
                        <p class="text-slate-500 text-sm">Loading files...</p>
                    </div>
                </div>

                <!-- Right Column: Interactive Live Preview -->
                <div class="glass p-6 rounded-2xl space-y-4">
                    <h2 class="text-xl font-bold text-emerald-400 flex items-center gap-2">
                        <span>👁️</span> Live Web Preview
                    </h2>
                    <div class="border border-slate-700 rounded-xl overflow-hidden h-[550px] bg-slate-950 flex flex-col">
                        <div class="bg-slate-900 px-4 py-2 border-b border-slate-800 text-xs text-slate-400 flex justify-between">
                            <span id="preview-title">Select a file to preview</span>
                            <span id="preview-status" class="text-emerald-400">Ready</span>
                        </div>
                        <iframe id="preview-frame" class="w-full flex-1 bg-white"></iframe>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let isAutoStepRunning = false;

            async function autoTriggerStep() {
                if (isAutoStepRunning) return;
                isAutoStepRunning = true;
                try {
                    await fetch('/api/step');
                    await loadData();
                } catch(e) {
                    console.error("Auto step error:", e);
                } finally {
                    isAutoStepRunning = false;
                }
            }

            async function loadData() {
                try {
                    const resHist = await fetch('/api/history');
                    const dataHist = await resHist.json();
                    const actionsDiv = document.getElementById('actions-list');
                    
                    if (dataHist.history && dataHist.history.length > 0) {
                        actionsDiv.innerHTML = dataHist.history.slice().reverse().map(item => {
                            const act = item.action || {};
                            return `
                                <div class="bg-slate-800/80 p-4 rounded-xl border border-slate-700/50 space-y-2">
                                    <div class="flex justify-between items-center">
                                        <span class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-blue-500/20 text-blue-400">${act.action || 'Action'}</span>
                                        <span class="text-[10px] text-slate-400">${new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                                    </div>
                                    <p class="text-sm font-medium text-slate-200">${act.thought || 'Autonomous action executed'}</p>
                                    ${act.path ? `<code class="text-xs bg-slate-900 px-2 py-1 rounded text-cyan-300 block font-mono">${act.path}</code>` : ''}
                                </div>
                            `;
                        }).join('');
                    } else {
                        actionsDiv.innerHTML = '<p class="text-slate-500 text-sm">Auto-creation active. Running steps...</p>';
                    }

                    const resFiles = await fetch('/api/files');
                    const dataFiles = await resFiles.json();
                    const filesDiv = document.getElementById('files-list');

                    if (dataFiles.files && dataFiles.files.length > 0) {
                        filesDiv.innerHTML = dataFiles.files.map(f => `
                            <button onclick="preview('${f}')" class="w-full text-left p-3 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 transition flex items-center justify-between group">
                                <span class="text-sm font-mono text-slate-300 group-hover:text-cyan-300">📄 ${f}</span>
                                <span class="text-xs text-blue-400">Preview →</span>
                            </button>
                        `).join('');
                    } else {
                        filesDiv.innerHTML = '<p class="text-slate-500 text-sm">No files created yet in workspace.</p>';
                    }
                } catch(e) {
                    console.error("Error loading data:", e);
                }
            }

            function preview(filePath) {
                document.getElementById('preview-title').innerText = filePath;
                document.getElementById('preview-frame').src = '/preview/' + filePath;
            }

            loadData();
            // Automatically poll and trigger AI steps every 12 seconds
            setInterval(autoTriggerStep, 12000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
