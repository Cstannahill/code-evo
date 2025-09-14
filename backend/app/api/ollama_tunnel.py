# app/api/ollama_tunnel.py
import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.ollama_tunnel_service import get_tunnel_service, TunnelStatus
from app.api.auth import get_current_user, oauth2_scheme

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ollama", tags=["ollama-tunnel"])
security = HTTPBearer()


async def get_user_from_websocket(websocket: WebSocket) -> str:
    """Extract user ID from WebSocket query parameters or headers"""
    # Try to get user_id from query parameters first
    user_id = websocket.query_params.get("user_id")
    if user_id:
        return user_id
    
    # Try to get from headers
    authorization = websocket.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            # For WebSocket, we'll validate the token manually
            from app.api.auth import verify_token
            user = await verify_token(token)
            return str(user.id)
        except Exception as e:
            logger.warning(f"Failed to extract user from WebSocket token: {e}")
    
    # Fallback to guest user
    return "guest"


@router.websocket("/tunnel")
async def websocket_tunnel(websocket: WebSocket):
    """WebSocket endpoint for Ollama tunnel connections"""
    await websocket.accept()
    
    try:
        # Get user ID
        user_id = await get_user_from_websocket(websocket)
        logger.info(f"🔌 WebSocket tunnel connection from user: {user_id}")
        
        # Get tunnel service
        tunnel_service = get_tunnel_service()
        
        # Register the tunnel
        ollama_url = websocket.query_params.get("ollama_url", "http://localhost:11434")
        success = await tunnel_service.register_tunnel(user_id, websocket, ollama_url)
        
        if not success:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to connect to Ollama instance"
            }))
            await websocket.close()
            return
        
        # Send success message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Tunnel established successfully",
            "user_id": user_id,
            "ollama_url": ollama_url
        }))
        
        # Handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "pong":
                    # Update last ping time
                    tunnel = tunnel_service.get_tunnel(user_id)
                    if tunnel:
                        tunnel.last_ping = datetime.utcnow()
                
                elif message.get("type") == "ollama_response":
                    # Forward Ollama response to the backend
                    logger.debug(f"Received Ollama response for user {user_id}")
                
                elif message.get("type") == "model_list_update":
                    # Update available models
                    tunnel = tunnel_service.get_tunnel(user_id)
                    if tunnel and "models" in message:
                        tunnel.available_models = set(message["models"])
                        logger.info(f"Updated models for user {user_id}: {len(tunnel.available_models)} models")
                
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket tunnel disconnected for user: {user_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message from user {user_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Internal error: {str(e)}"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket tunnel error: {e}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        # Clean up tunnel
        tunnel_service = get_tunnel_service()
        await tunnel_service.unregister_tunnel(user_id)


@router.get("/tunnel/status")
async def get_tunnel_status(current_user = Depends(get_current_user)):
    """Get the status of the current user's Ollama tunnel"""
    try:
        tunnel_service = get_tunnel_service()
        
        status = tunnel_service.get_tunnel_status(str(current_user.id))
        if not status:
            raise HTTPException(status_code=404, detail="No active tunnel found")
        
        return status
    except Exception as e:
        logger.error(f"Error getting tunnel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tunnel/models")
async def get_tunnel_models(current_user = Depends(get_current_user)):
    """Get available models from the user's Ollama tunnel"""
    try:
        tunnel_service = get_tunnel_service()
        
        models = tunnel_service.get_available_models(str(current_user.id))
        return {
            "models": list(models),
            "count": len(models)
        }
    except Exception as e:
        logger.error(f"Error getting tunnel models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tunnel/request")
async def send_ollama_request(
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Send a request to the user's Ollama instance via tunnel"""
    try:
        tunnel_service = get_tunnel_service()
        
        model = request_data.get("model")
        prompt = request_data.get("prompt")
        options = request_data.get("options", {})
        
        if not model or not prompt:
            raise HTTPException(status_code=400, detail="Model and prompt are required")
        
        response = await tunnel_service.send_ollama_request(
            str(current_user.id), model, prompt, **options
        )
        
        if not response:
            raise HTTPException(status_code=503, detail="Tunnel not available or request failed")
        
        return response
    except Exception as e:
        logger.error(f"Error sending Ollama request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tunnel/all")
async def get_all_tunnels_status():
    """Get status of all active tunnels (admin endpoint)"""
    try:
        tunnel_service = get_tunnel_service()
        return tunnel_service.get_all_tunnels_status()
    except Exception as e:
        logger.error(f"Error getting all tunnels status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
