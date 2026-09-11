import os
import tempfile
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from network.pcap_reader import PcapReaderService
from backend.pipeline.orchestrator import orchestrator
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(tags=["PCAP Upload & Replay"])


@router.post("/api/v1/pcaps/upload")
@router.post("/api/pcap/upload")
def upload_pcap(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    # Sanitize filename against path traversal attacks
    safe_filename = os.path.basename(file.filename)
    if not safe_filename.endswith((".pcap", ".pcapng", ".cap")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "Only .pcap, .pcapng, or .cap files are accepted."}
        )

    # Save uploaded bytes to temporary file with max 50MB size limit
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"upload_{safe_filename}")

    try:
        contents = file.file.read(MAX_FILE_SIZE + 1)
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "FILE_TOO_LARGE", "message": "Uploaded PCAP file exceeds 50MB limit."}
            )

        with open(temp_path, "wb") as f:
            f.write(contents)

        # Parse PCAP file
        packets = PcapReaderService.read_pcap(temp_path)
        alerts_generated = []

        for pkt in packets:
            alert = orchestrator.process_packet(pkt, source="pcap")
            if alert:
                alerts_generated.append(alert["payload"])

        # Flush active flow windows
        expired = orchestrator.aggregator.flush_expired_flows(current_ts=1e12)
        for flow in expired:
            alert = orchestrator.process_flow(flow)
            if alert:
                alerts_generated.append(alert["payload"])

        return {
            "status": "success",
            "filename": file.filename,
            "packets_parsed": len(packets),
            "alerts_generated_count": len(alerts_generated),
            "alerts": alerts_generated
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PCAP_PROCESSING_ERROR", "message": f"Failed to process PCAP file: {str(exc)}"}
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
