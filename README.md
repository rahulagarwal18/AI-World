# Autonomous AI Creation Engine 🚀

An autonomous, self-directed AI creation engine powered by **Groq API**, connected to **GitHub**, **Vercel**, and **5TB Google Drive Storage**.

---

## Features
- 🧠 **Groq API Engine (`llama-3.3-70b-versatile`)**: Autonomous reasoning & decision loop with built-in rate-limiting exponential backoff.
- 📦 **Sandboxed Workspace**: Safe file creation, reading, and execution.
- 🐙 **GitHub Auto-Commit & Push**: Automatically pushes generated code & projects to [`rahulagarwal18/AI-World`](https://github.com/rahulagarwal18/AI-World).
- ☁️ **5TB Google Drive Vault**: Syncs large files, snapshots, and media to shared folder [`16JoYjvINixhs1TRgZLplF9mdIMXl-eP0`](https://drive.google.com/drive/folders/16JoYjvINixhs1TRgZLplF9mdIMXl-eP0).
- 🐳 **24/7 Cloud Ready**: Includes Docker container setup so the engine can run continuously in the cloud even when your PC is turned off.

---

## Quick Start (Local)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Backend Server**:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

3. **Trigger Autonomous Step**:
   * Open `http://localhost:8000/docs` or send POST request to `http://localhost:8000/start` to begin 24/7 continuous creation mode.

---

## 24/7 Cloud Deployment (PC Turned Off)
To keep the engine running when your laptop is closed:
- Deploy this repository to **Railway**, **Render**, **Fly.io**, or **Koyeb** using the included `Dockerfile`.
