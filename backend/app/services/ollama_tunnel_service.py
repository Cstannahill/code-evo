# app/services/ollama_tunnel_service.py
import asyncio
import json
import logging
import websockets
import requests
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TunnelStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class OllamaTunnel:
    """Represents a WebSocket tunnel to a user's local Ollama instance"""
    user_id: str
    websocket: websockets.WebSocketServerProtocol
    ollama_url: str
    status: TunnelStatus
    connected_at: datetime
    last_ping: datetime
    available_models: Set[str] = None
    
    def __post_init__(self):
        if self.available_models is None:
            self.available_models = set()


class OllamaTunnelService:
    """Service for managing WebSocket tunnels to user's local Ollama instances"""
    
    def __init__(self):
        self.tunnels: Dict[str, OllamaTunnel] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.ping_interval = 30  # 30 seconds
        self.timeout_threshold = 120  # 2 minutes
        
    async def register_tunnel(self, user_id: str, websocket: websockets.WebSocketServerProtocol, ollama_url: str = "http://localhost:11434") -> bool:
        """Register a new WebSocket tunnel for a user"""
        try:
            # Test the Ollama connection first
            test_url = f"{ollama_url}/api/tags"
            response = requests.get(test_url, timeout=5)
            if response.status_code != 200:
                logger.warning(f"Ollama test failed for user {user_id}: {response.status_code}")
                return False
                
            # Parse available models
            models_data = response.json()
            available_models = set()
            if 'models' in models_data:
                for model in models_data['models']:
                    if 'name' in model:
                        available_models.add(model['name'])
            
            tunnel = OllamaTunnel(
                user_id=user_id,
                websocket=websocket,
                ollama_url=ollama_url,
                status=TunnelStatus.CONNECTED,
                connected_at=datetime.utcnow(),
                last_ping=datetime.utcnow(),
                available_models=available_models
            )
            
            self.tunnels[user_id] = tunnel
            logger.info(f"✅ Ollama tunnel registered for user {user_id} with {len(available_models)} models")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register Ollama tunnel for user {user_id}: {e}")
            return False
    
    async def unregister_tunnel(self, user_id: str):
        """Unregister a WebSocket tunnel"""
        if user_id in self.tunnels:
            tunnel = self.tunnels[user_id]
            try:
                await tunnel.websocket.close()
            except:
                pass
            del self.tunnels[user_id]
            logger.info(f"🔌 Ollama tunnel unregistered for user {user_id}")
    
    def get_tunnel(self, user_id: str) -> Optional[OllamaTunnel]:
        """Get tunnel for a specific user"""
        return self.tunnels.get(user_id)
    
    def get_available_models(self, user_id: str) -> Set[str]:
        """Get available models for a user's Ollama instance"""
        tunnel = self.get_tunnel(user_id)
        if tunnel and tunnel.status == TunnelStatus.CONNECTED:
            return tunnel.available_models
        return set()
    
    async def ping_tunnel(self, user_id: str) -> bool:
        """Ping a tunnel to check if it's still alive"""
        tunnel = self.get_tunnel(user_id)
        if not tunnel:
            return False
            
        try:
            # Send ping message
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await tunnel.websocket.send(json.dumps(ping_message))
            tunnel.last_ping = datetime.utcnow()
            return True
        except Exception as e:
            logger.warning(f"Ping failed for user {user_id}: {e}")
            tunnel.status = TunnelStatus.ERROR
            return False
    
    async def send_ollama_request(self, user_id: str, model: str, prompt: str, **kwargs) -> Optional[Dict]:
        """Send a request to user's Ollama instance via WebSocket"""
        tunnel = self.get_tunnel(user_id)
        if not tunnel or tunnel.status != TunnelStatus.CONNECTED:
            return None
            
        try:
            request_data = {
                "type": "ollama_request",
                "model": model,
                "prompt": prompt,
                "options": kwargs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await tunnel.websocket.send(json.dumps(request_data))
            
            # Wait for response (with timeout)
            response = await asyncio.wait_for(
                tunnel.websocket.recv(),
                timeout=30.0
            )
            
            response_data = json.loads(response)
            return response_data
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timeout for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Ollama request failed for user {user_id}: {e}")
            return None
    
    async def cleanup_stale_tunnels(self):
        """Clean up stale/disconnected tunnels"""
        current_time = datetime.utcnow()
        stale_users = []
        
        for user_id, tunnel in self.tunnels.items():
            time_since_ping = current_time - tunnel.last_ping
            if time_since_ping > timedelta(seconds=self.timeout_threshold):
                stale_users.append(user_id)
        
        for user_id in stale_users:
            logger.info(f"🧹 Cleaning up stale tunnel for user {user_id}")
            await self.unregister_tunnel(user_id)
    
    async def start_cleanup_task(self):
        """Start the background cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_stale_tunnels()
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    def get_tunnel_status(self, user_id: str) -> Optional[Dict]:
        """Get status information for a user's tunnel"""
        tunnel = self.get_tunnel(user_id)
        if not tunnel:
            return None
            
        return {
            "user_id": user_id,
            "status": tunnel.status,
            "connected_at": tunnel.connected_at.isoformat(),
            "last_ping": tunnel.last_ping.isoformat(),
            "available_models": list(tunnel.available_models),
            "ollama_url": tunnel.ollama_url
        }
    
    def get_all_tunnels_status(self) -> Dict[str, Dict]:
        """Get status for all tunnels"""
        return {
            user_id: self.get_tunnel_status(user_id)
            for user_id in self.tunnels.keys()
        }


# Global instance
_tunnel_service: Optional[OllamaTunnelService] = None


def get_tunnel_service() -> OllamaTunnelService:
    """Get the global tunnel service instance"""
    global _tunnel_service
    if _tunnel_service is None:
        _tunnel_service = OllamaTunnelService()
    return _tunnel_service
