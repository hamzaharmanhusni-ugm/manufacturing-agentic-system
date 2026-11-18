"""HTTP client for the dashboards. Every number on screen comes from these API calls."""
import sys
from pathlib import Path

import httpx
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import url  # noqa: E402
from shared.rbac import ROLES  # noqa: E402


def role():
    return st.session_state.get("role", "Global Administrator")


def _headers():
    return {"X-API-Key": ROLES[role()]["key"], "X-User-Role": role()}


@st.cache_data(ttl=3, show_spinner=False)
def _get(service, path, headers_key):
    r = httpx.get(url(service) + path, headers=dict(headers_key), timeout=60)
    if r.status_code in (401, 403):
        return {"__denied__": r.json().get("detail", r.text)}
    r.raise_for_status()
    return r.json()


def get(service, path):
    """GET with a short cache. Returns None when the service is unreachable."""
    try:
        return _get(service, path, tuple(sorted(_headers().items())))
    except httpx.HTTPError as e:
        st.error(f"{service} API unreachable ({type(e).__name__}). Start the stack with `python run_all.py`.")
        return None


def post(service, path, body=None):
    r = httpx.post(url(service) + path, json=body or {}, headers=_headers(), timeout=180)
    st.cache_data.clear()
    if not r.is_success:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        raise RuntimeError(f"HTTP {r.status_code}: {detail}")
    return r.json()


def denied(data):
    return isinstance(data, dict) and "__denied__" in data
