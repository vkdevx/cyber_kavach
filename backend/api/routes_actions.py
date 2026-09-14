import subprocess
import time
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["Security Actions"])

# In-memory store for active blocked IPs
BLOCKED_IPS: Dict[str, dict] = {}


class BlockIPRequest(BaseModel):
    ip: str
    reason: Optional[str] = "Analyst manual block trigger"


class UnblockIPRequest(BaseModel):
    ip: str


def execute_firewall_block(ip: str) -> bool:
    """Executes Windows Firewall Block Rule via netsh."""
    rule_name = f"CyberKavach_Block_{ip}"
    try:
        cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def execute_firewall_unblock(ip: str) -> bool:
    """Removes Windows Firewall Block Rule via netsh."""
    rule_name = f"CyberKavach_Block_{ip}"
    try:
        cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


@router.get("/api/v1/actions/blocked-ips")
def get_blocked_ips():
    """Returns list of currently active blocked IPs."""
    return list(BLOCKED_IPS.values())


@router.post("/api/v1/actions/block-ip")
def block_ip_action(req: BlockIPRequest):
    """
    Direct Firewall Block Action:
    Adds firewall rule to block the malicious IP and tracks it in CyberKavach active mitigations.
    """
    ip = req.ip.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    fw_applied = execute_firewall_block(ip)

    BLOCKED_IPS[ip] = {
        "ip": ip,
        "reason": req.reason,
        "blocked_at": time.time(),
        "firewall_rule_applied": fw_applied,
        "status": "BLOCKED"
    }

    return {
        "status": "success",
        "message": f"IP {ip} has been blocked successfully in firewall.",
        "ip": ip,
        "firewall_applied": fw_applied
    }


@router.post("/api/v1/actions/unblock-ip")
def unblock_ip_action(req: UnblockIPRequest):
    """
    Direct Firewall Unblock Action:
    Removes firewall rule and clears the IP from CyberKavach blocklist.
    """
    ip = req.ip.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    fw_removed = execute_firewall_unblock(ip)

    if ip in BLOCKED_IPS:
        del BLOCKED_IPS[ip]

    return {
        "status": "success",
        "message": f"IP {ip} has been unblocked successfully.",
        "ip": ip,
        "firewall_removed": fw_removed
    }

