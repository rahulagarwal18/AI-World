import os
import sys
import traceback
import uvicorn

if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8000"))
        print(f"Starting uvicorn server on port {port}...", flush=True)
        uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
    except Exception as e:
        print(f"FATAL SERVER STARTUP ERROR: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)
