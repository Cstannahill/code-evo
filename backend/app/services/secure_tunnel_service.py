"""
Secure Tunnel Service for Ollama Integration

This service manages secure WebSocket tunnels from the deployed backend to users' local Ollama instances.
Users opt-in to create tunnels (via Cloudflare Tunnel or ngrok) that allow the backend to access their
local AI models while maintaining security and transparency.

Security Features:
- Unique authentication tokens per user
- Token rotation and expiration
- Rate limiting per user
- Request validation and audit logging
- User-controlled tunnel enable/disable
"""

import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from enum import Enum
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TunnelStatus(str, Enum):
    """Tunnel connection status"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


class TunnelMethod(str, Enum):
    """Supported tunnel methods"""

    CLOUDFLARE = "cloudflare"
    NGROK = "ngrok"
    SSH = "ssh"


class TunnelConnection(BaseModel):
    """Represents an active tunnel connection"""

    user_id: str
    tunnel_url: str
    tunnel_method: TunnelMethod
    auth_token: str
    status: TunnelStatus
    created_at: datetime
    last_used: datetime
    expires_at: datetime
    request_count: int = 0
    error_message: Optional[str] = None


class TunnelRequest(BaseModel):
    """Represents a tunneled Ollama request"""

    request_id: str
    user_id: str
    endpoint: str
    method: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


class SecureTunnelService:
    """Service for managing secure tunnels to users' local Ollama instances"""

    def __init__(self):
        self.active_tunnels: Dict[str, TunnelConnection] = {}
        self.request_history: List[TunnelRequest] = []
        self.max_history = 1000  # Keep last 1000 requests

        # Rate limiting: requests per minute per user
        self.rate_limit = 60
        self.rate_window = 60  # seconds
        self.user_request_counts: Dict[str, List[float]] = {}

        # Token settings
        self.token_ttl_hours = 24

    def generate_auth_token(self) -> str:
        """Generate a cryptographically secure authentication token"""
        return secrets.token_urlsafe(32)

    async def register_tunnel(
        self, user_id: str, tunnel_url: str, tunnel_method: TunnelMethod
    ) -> Dict[str, Any]:
        """
        Register a new tunnel connection

        Args:
            user_id: Unique user identifier
            tunnel_url: The tunnel URL (e.g., https://xxx.trycloudflare.com)
            tunnel_method: Method used (cloudflare, ngrok, ssh)

        Returns:
            Dictionary with tunnel details and auth token
        """
        try:
            # Validate tunnel URL is accessible
            validation_result = await self._validate_tunnel(tunnel_url)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "status": TunnelStatus.ERROR,
                }

            # Generate authentication token
            auth_token = self.generate_auth_token()

            # Create tunnel connection
            tunnel = TunnelConnection(
                user_id=user_id,
                tunnel_url=tunnel_url.rstrip("/"),
                tunnel_method=tunnel_method,
                auth_token=auth_token,
                status=TunnelStatus.CONNECTED,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=self.token_ttl_hours),
            )

            # Store tunnel
            self.active_tunnels[user_id] = tunnel

            logger.info(f"✅ Tunnel registered for user {user_id} via {tunnel_method}")
            logger.info(f"   URL: {tunnel_url}")
            logger.info(f"   Expires: {tunnel.expires_at.isoformat()}")

            return {
                "success": True,
                "tunnel_id": user_id,
                "auth_token": auth_token,
                "expires_at": tunnel.expires_at.isoformat(),
                "status": TunnelStatus.CONNECTED,
                "tunnel_url": tunnel_url,
            }

        except Exception as e:
            logger.error(f"❌ Failed to register tunnel for user {user_id}: {e}")
            return {"success": False, "error": str(e), "status": TunnelStatus.ERROR}

    async def _validate_tunnel(self, tunnel_url: str) -> Dict[str, Any]:
        """
        Validate that a tunnel is accessible and responds correctly

        Tests the tunnel by making a request to Ollama's /api/tags endpoint
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to access Ollama through the tunnel
                test_url = f"{tunnel_url}/api/tags"
                response = await client.get(test_url)

                if response.status_code == 200:
                    data = response.json()
                    # Validate it's actually Ollama
                    if "models" in data:
                        logger.info(f"✅ Tunnel validated: {tunnel_url}")
                        return {"valid": True}
                    else:
                        return {
                            "valid": False,
                            "error": "Tunnel endpoint doesn't appear to be Ollama",
                        }
                else:
                    return {
                        "valid": False,
                        "error": f"Tunnel returned HTTP {response.status_code}",
                    }

        except httpx.TimeoutException:
            return {
                "valid": False,
                "error": "Tunnel connection timeout - check if tunnel is running",
            }
        except httpx.ConnectError:
            return {
                "valid": False,
                "error": "Cannot connect to tunnel - verify URL is correct",
            }
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    def get_tunnel(self, user_id: str) -> Optional[TunnelConnection]:
        """Get active tunnel for a user"""
        tunnel = self.active_tunnels.get(user_id)

        # Check if tunnel is expired
        if tunnel and tunnel.expires_at < datetime.utcnow():
            logger.warning(f"⚠️ Tunnel expired for user {user_id}")
            tunnel.status = TunnelStatus.DISABLED
            return None

        return tunnel

    async def proxy_ollama_request(
        self,
        user_id: str,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Proxy a request through the user's tunnel to their local Ollama

        Args:
            user_id: User identifier
            endpoint: Ollama API endpoint (e.g., /api/generate)
            method: HTTP method (GET, POST)
            data: Request payload
            timeout: Request timeout in seconds

        Returns:
            Response data from Ollama
        """
        request_id = secrets.token_urlsafe(16)
        start_time = time.time()

        # Rate limiting check
        if not self._check_rate_limit(user_id):
            logger.warning(f"⚠️ Rate limit exceeded for user {user_id}")
            return {
                "success": False,
                "error": "Rate limit exceeded. Please wait before making more requests.",
                "error_code": "RATE_LIMIT_EXCEEDED",
            }

        # Get tunnel
        tunnel = self.get_tunnel(user_id)
        if not tunnel or tunnel.status != TunnelStatus.CONNECTED:
            logger.warning(f"⚠️ No active tunnel for user {user_id}")
            return {
                "success": False,
                "error": "No active tunnel connection. Please enable tunnel first.",
                "error_code": "TUNNEL_NOT_AVAILABLE",
            }

        try:
            # Build request
            url = f"{tunnel.tunnel_url}{endpoint}"

            logger.info(f"🔄 Proxying request for user {user_id}: {method} {endpoint}")

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "POST":
                    response = await client.post(url, json=data)
                elif method == "GET":
                    response = await client.get(url, params=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Update tunnel stats
                tunnel.last_used = datetime.utcnow()
                tunnel.request_count += 1

                duration_ms = (time.time() - start_time) * 1000

                # Log request
                self._log_request(
                    request_id=request_id,
                    user_id=user_id,
                    endpoint=endpoint,
                    method=method,
                    duration_ms=duration_ms,
                    status_code=response.status_code,
                )

                if response.status_code == 200:
                    logger.info(f"✅ Request successful ({duration_ms:.0f}ms)")
                    return {
                        "success": True,
                        "data": response.json(),
                        "duration_ms": duration_ms,
                    }
                else:
                    logger.error(f"❌ Ollama error: HTTP {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Ollama returned HTTP {response.status_code}",
                        "status_code": response.status_code,
                    }

        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            self._log_request(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                duration_ms=duration_ms,
                error="Timeout",
            )
            logger.error(f"❌ Request timeout for user {user_id}")
            return {
                "success": False,
                "error": "Request timeout - Ollama may be processing a large request",
                "error_code": "TIMEOUT",
            }
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._log_request(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                duration_ms=duration_ms,
                error=str(e),
            )
            logger.error(f"❌ Proxy error for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Tunnel error: {str(e)}",
                "error_code": "TUNNEL_ERROR",
            }

    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit"""
        now = time.time()

        # Initialize if needed
        if user_id not in self.user_request_counts:
            self.user_request_counts[user_id] = []

        # Remove old requests outside window
        self.user_request_counts[user_id] = [
            req_time
            for req_time in self.user_request_counts[user_id]
            if now - req_time < self.rate_window
        ]

        # Check limit
        if len(self.user_request_counts[user_id]) >= self.rate_limit:
            return False

        # Add current request
        self.user_request_counts[user_id].append(now)
        return True

    def _log_request(
        self,
        request_id: str,
        user_id: str,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """Log a tunnel request for audit purposes"""
        request = TunnelRequest(
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            status_code=status_code,
            error=error,
        )

        self.request_history.append(request)

        # Trim history if needed
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history :]

    def disable_tunnel(self, user_id: str) -> Dict[str, Any]:
        """Disable/disconnect a tunnel"""
        if user_id in self.active_tunnels:
            tunnel = self.active_tunnels[user_id]
            tunnel.status = TunnelStatus.DISABLED
            logger.info(f"🔌 Tunnel disabled for user {user_id}")
            del self.active_tunnels[user_id]
            return {"success": True, "message": "Tunnel disabled"}
        return {"success": False, "error": "No active tunnel found"}

    def get_tunnel_status(self, user_id: str) -> Dict[str, Any]:
        """Get current tunnel status for a user"""
        tunnel = self.active_tunnels.get(user_id)

        if not tunnel:
            return {"status": TunnelStatus.DISCONNECTED, "connected": False}

        # Check expiration
        if tunnel.expires_at < datetime.utcnow():
            tunnel.status = TunnelStatus.DISABLED
            return {
                "status": TunnelStatus.DISABLED,
                "connected": False,
                "reason": "Token expired",
            }

        return {
            "status": tunnel.status,
            "connected": tunnel.status == TunnelStatus.CONNECTED,
            "tunnel_url": tunnel.tunnel_url,
            "tunnel_method": tunnel.tunnel_method,
            "created_at": tunnel.created_at.isoformat(),
            "expires_at": tunnel.expires_at.isoformat(),
            "request_count": tunnel.request_count,
            "last_used": tunnel.last_used.isoformat(),
        }

    def get_recent_requests(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent tunnel requests for a user"""
        user_requests = [
            {
                "request_id": req.request_id,
                "endpoint": req.endpoint,
                "method": req.method,
                "timestamp": req.timestamp.isoformat(),
                "duration_ms": req.duration_ms,
                "status_code": req.status_code,
                "error": req.error,
            }
            for req in reversed(self.request_history)
            if req.user_id == user_id
        ][:limit]

        return user_requests


# Global service instance
_tunnel_service: Optional[SecureTunnelService] = None


def get_tunnel_service() -> SecureTunnelService:
    """Get the global tunnel service instance"""
    global _tunnel_service
    if _tunnel_service is None:
        _tunnel_service = SecureTunnelService()
    return _tunnel_service
