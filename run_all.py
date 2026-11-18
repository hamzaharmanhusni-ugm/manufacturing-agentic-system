"""Start the whole prototype: Docker databases, 4 enterprise APIs, Global Orchestrator, Streamlit UI.
Usage: python run_all.py [--no-ui] [--no-docker]   (Ctrl+C stops everything)"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
SERVICES = [("manufacturer", "backend.manufacturer_api.main:app", 8001), ("shipping", "backend.shipping_api.main:app", 8002),
            ("distribution", "backend.distribution_api.main:app", 8003), ("supplier", "backend.supplier_api.main:app", 8004),
            ("orchestrator", "backend.global_orchestrator.main:app", 8000)]


def main():
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    if "--no-docker" in sys.argv:
        env["MAS_STORAGE"] = "local"
    else:
        r = subprocess.run(["docker", "compose", "up", "-d", "--wait"], cwd=ROOT)
        if r.returncode:
            print("Docker not available: falling back to local SQLite/JSON stores (MAS_STORAGE=local)")
            env["MAS_STORAGE"] = "local"
    procs = []
    (ROOT / "logs").mkdir(exist_ok=True)
    for name, app, port in SERVICES:
        log = open(ROOT / "logs" / f"{name}.log", "w")
        procs.append(subprocess.Popen([PY, "-m", "uvicorn", app, "--port", str(port), "--host", "127.0.0.1"],
                                      cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT))
        print(f"started {name:13s} http://127.0.0.1:{port}/docs")
    if "--no-ui" not in sys.argv:
        procs.append(subprocess.Popen([PY, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "3000",
                                       "--server.headless", "true"], cwd=ROOT, env=env))
        print("started streamlit     http://localhost:3000")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
        print("a service exited; see logs/*.log")
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
