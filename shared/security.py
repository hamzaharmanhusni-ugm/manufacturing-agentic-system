"""Authentication simulation, scope checks from each enterprise's governance policy G_i,
and request logging. Shared by every enterprise API, but each API passes its own policy."""
import time
from collections import deque
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException, Request

from shared.config import API_KEYS


def setup(app: FastAPI, enterprise: str, policy: dict):
    """policy: {principal: set(scopes)} = this enterprise's data-sharing agreement."""
    app.state.request_log = deque(maxlen=500)
    app.state.policy = policy
    app.state.enterprise = enterprise

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        t0 = time.perf_counter()
        principal = API_KEYS.get(request.headers.get("x-api-key", ""), "anonymous")
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            if request.url.path not in ("/logs", "/favicon.ico") and not request.url.path.startswith(("/docs", "/openapi")):
                app.state.request_log.append({
                    "ts": datetime.now().isoformat(timespec="seconds"), "enterprise": enterprise,
                    "method": request.method, "path": request.url.path, "principal": principal,
                    "role": request.headers.get("x-user-role", "-"), "status": status,
                    "ms": round((time.perf_counter() - t0) * 1000, 1)})
        return response

    def require(scope: str):
        def dep(x_api_key: str = Header(default="")):
            principal = API_KEYS.get(x_api_key)
            if not principal:
                raise HTTPException(401, "invalid or missing X-API-Key")
            if scope not in policy.get(principal, set()):
                raise HTTPException(403, f"'{principal}' lacks scope '{scope}' under {enterprise} data-sharing policy")
            return principal
        return dep

    @app.get("/health", tags=["platform"])
    def health():
        return {"enterprise": enterprise, "status": "ok", "ts": datetime.now().isoformat(timespec="seconds")}

    @app.get("/logs", tags=["platform"])
    def logs(limit: int = 100, x_api_key: str = Header(default="")):
        if x_api_key not in API_KEYS:
            raise HTTPException(401, "invalid or missing X-API-Key")
        return list(app.state.request_log)[-limit:][::-1]

    @app.get("/governance", tags=["platform"])
    def governance():
        return {"enterprise": enterprise, "policy": {k: sorted(v) for k, v in policy.items()}}

    return require
