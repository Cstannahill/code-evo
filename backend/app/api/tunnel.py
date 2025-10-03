"""
API endpoints for Secure Tunnel Management

Provides endpoints for users to:
- Register and enable tunnels
- Check tunnel status
- Disable tunnels
- View tunnel request history (transparency)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
import logging

from app.services.secure_tunnel_service import (
    get_tunnel_service,
    TunnelMethod,
    TunnelStatus,
)
from app.models.repository import User
from app.api.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tunnel", tags=["tunnel"])


class TunnelRegistrationRequest(BaseModel):
    """Request to register a new tunnel"""

    tunnel_url: str
    tunnel_method: TunnelMethod


class TunnelProxyRequest(BaseModel):
    """Request to proxy through tunnel"""

    endpoint: str
    method: str = "POST"
    data: Optional[Dict[str, Any]] = None
    timeout: float = 30.0


@router.post("/register")
async def register_tunnel(
    request: TunnelRegistrationRequest, current_user: User = Depends(get_current_user)
):
    """
    Register a new secure tunnel

    This validates the tunnel URL and creates an authenticated connection.
    Users must have their tunnel running (Cloudflare/ngrok) before calling this.
    """
    try:
        tunnel_service = get_tunnel_service()

        logger.info(f"🔐 Tunnel registration requested by user {current_user.id}")
        logger.info(f"   Method: {request.tunnel_method}")
        logger.info(f"   URL: {request.tunnel_url}")

        result = await tunnel_service.register_tunnel(
            user_id=str(current_user.id),
            tunnel_url=request.tunnel_url,
            tunnel_method=request.tunnel_method,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Tunnel registration failed"),
            )

        return {
            "success": True,
            "message": "Tunnel registered successfully",
            "tunnel": {
                "status": result["status"],
                "expires_at": result["expires_at"],
                "auth_token": result["auth_token"],  # Send once, user should store
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tunnel registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_tunnel_status(current_user: User = Depends(get_current_user)):
    """
    Get current tunnel status for the authenticated user

    Returns connection state, request counts, and expiration info
    """
    try:
        tunnel_service = get_tunnel_service()
        status = tunnel_service.get_tunnel_status(str(current_user.id))

        return {"success": True, "tunnel": status}

    except Exception as e:
        logger.error(f"❌ Error fetching tunnel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable")
async def disable_tunnel(current_user: User = Depends(get_current_user)):
    """
    Disable/disconnect the user's tunnel

    This immediately revokes access and stops all proxied requests
    """
    try:
        tunnel_service = get_tunnel_service()
        result = tunnel_service.disable_tunnel(str(current_user.id))

        if not result["success"]:
            raise HTTPException(status_code=404, detail="No active tunnel found")

        logger.info(f"🔌 Tunnel disabled by user {current_user.id}")

        return {"success": True, "message": "Tunnel disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error disabling tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proxy")
async def proxy_request(
    request: TunnelProxyRequest, current_user: User = Depends(get_current_user)
):
    """
    Proxy a request through the user's tunnel to their local Ollama

    This is the main endpoint used by the backend AI service to access
    the user's local models.
    """
    try:
        tunnel_service = get_tunnel_service()

        result = await tunnel_service.proxy_ollama_request(
            user_id=str(current_user.id),
            endpoint=request.endpoint,
            method=request.method,
            data=request.data,
            timeout=request.timeout,
        )

        if not result["success"]:
            # Return appropriate error based on error code
            error_code = result.get("error_code", "UNKNOWN")
            if error_code == "TUNNEL_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail=result["error"])
            elif error_code == "RATE_LIMIT_EXCEEDED":
                raise HTTPException(status_code=429, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "data": result["data"],
            "duration_ms": result.get("duration_ms"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Proxy request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/recent")
async def get_recent_requests(
    limit: int = 50, current_user: User = Depends(get_current_user)
):
    """
    Get recent tunnel requests for transparency

    Allows users to see exactly what requests are being made through their tunnel
    """
    try:
        tunnel_service = get_tunnel_service()
        requests = tunnel_service.get_recent_requests(
            user_id=str(current_user.id), limit=min(limit, 100)  # Cap at 100
        )

        return {"success": True, "requests": requests, "count": len(requests)}

    except Exception as e:
        logger.error(f"❌ Error fetching request history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def tunnel_health_check():
    """
    Health check endpoint for tunnel service

    Public endpoint to verify service availability
    """
    return {"status": "healthy", "service": "secure_tunnel", "version": "1.0.0"}
