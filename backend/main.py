import asyncio
import logging
from typing import List
from fastapi import FastAPI, Request
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

@app.get("/")
@app.get("/api")
def get_status():
    return {
        "status": "active",
        "engine": "Groq Autonomous AI Engine",
        "history_count": len(agent.history)
    }

@app.post("/step")
@app.post("/api/step")
def step_engine():
    """Triggers a single autonomous AI creation step (Serverless Compatible)"""
    try:
        log = agent.run_cycle()
        return log
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/history")
@app.get("/api/history")
def get_history():
    return {"history": agent.history}
