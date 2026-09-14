import time
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from storage.db import init_db
from backend.api.routes_auth import router as auth_router
from backend.api.routes_telemetry import router as telemetry_router
from backend.api.routes_dashboard import router as dashboard_router
from backend.api.routes_threats import router as threats_router
from backend.api.routes_intel import router as intel_router
from backend.api.routes_actions import router as actions_router
from backend.api.routes_pcaps import router as pcaps_router
from backend.api.schemas import SystemStatusResponse
from backend.api.ws_manager import ws_manager

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from network.passive_capture import PassiveCaptureService
from backend.pipeline.orchestrator import orchestrator

capture_service = PassiveCaptureService(
    packet_callback=lambda pkt: orchestrator.process_packet(pkt, source="live")
)

import threading

_worker_running = False

def _background_flow_worker():
    while _worker_running:
        try:
            time.sleep(0.1)
            expired_flows = orchestrator.aggregator.flush_expired_flows()
            for flow in expired_flows:
                orchestrator.process_flow(flow)
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_running
    init_db()
    _worker_running = True
    worker_thread = threading.Thread(target=_background_flow_worker, daemon=True, name="FlowFlushWorker")
    worker_thread.start()
    try:
        capture_service.start()
    except Exception:
        pass
    yield
    _worker_running = False
    capture_service.stop()

app = FastAPI(
    title="CyberKavach API",
    description="AI-Based Cyber Threat Detection & Defence System (SIH26145)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix="/api")
app.include_router(telemetry_router)
app.include_router(dashboard_router)
app.include_router(threats_router)
app.include_router(intel_router)
app.include_router(actions_router)
app.include_router(pcaps_router)

# Mount Static Frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse("frontend/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/api/status", response_model=SystemStatusResponse, tags=["System"])
def get_status():
    return SystemStatusResponse(
        status="healthy",
        listening=True,
        degraded=False,
        interface=f"{settings.CAPTURE_INTERFACE} (promisc, read-only)",
        zero_outbound_guarantee=True,
        timestamp=time.time()
    )


@app.websocket("/ws/alerts")
@app.websocket("/ws/live-traffic")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client pings/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/live-traffic")
async def websocket_live_traffic(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client pings/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
