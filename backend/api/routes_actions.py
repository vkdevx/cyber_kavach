from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import require_role, CurrentUser, assert_no_active_response_action

router = APIRouter(tags=["Security Actions"])


class BlockIPRequest(BaseModel):
    ip: str
    reason: Optional[str] = "Analyst manual block trigger"


@router.post("/api/v1/actions/block-ip")
def block_ip_action(
    req: BlockIPRequest,
    current_user: CurrentUser = Depends(require_role(["admin"]))
):
    """
    Firewall / Quarantine action trigger endpoint.
    Strictly asserts zero-outbound diode constraints per rules.md §20, returning HTTP 400 Bad Request.
    """
    assert_no_active_response_action("block-ip")
