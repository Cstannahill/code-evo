# Ollama Tunnel Setup Guide

This guide explains how to connect your local Ollama instance to the deployed Railway backend, allowing you to use your local models for code analysis without any cost.

## 🚀 Quick Start

### 1. Install the Tunnel Client

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install -f ollama-tunnel-package.json

# Install globally (optional)
npm install -g .
```

### 2. Start Your Local Ollama

Make sure Ollama is running on your local machine:

```bash
# Start Ollama (if not already running)
ollama serve

# Pull some models (optional)
ollama pull codellama:7b
ollama pull devstral
ollama pull gemma3n
```

### 3. Connect the Tunnel

```bash
# Basic connection (as guest user)
ollama-tunnel

# With specific backend URL
ollama-tunnel --backend-url https://backend-production-ee56.up.railway.app

# With custom Ollama URL
ollama-tunnel --ollama-url http://localhost:11434

# With authentication (if you have an account)
ollama-tunnel --user-id your-user-id --token your-auth-token
```

## 🔧 Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-url` | Railway backend URL | `https://backend-production-ee56.up.railway.app` |
| `--ollama-url` | Local Ollama URL | `http://localhost:11434` |
| `--user-id` | Your user ID (optional) | `guest` |
| `--token` | Auth token (optional) | None |

## 📋 How It Works

1. **WebSocket Connection**: The tunnel client establishes a WebSocket connection to the Railway backend
2. **Model Discovery**: Your local Ollama models are automatically discovered and registered
3. **Request Forwarding**: When you select a local model in the frontend, requests are forwarded through the tunnel
4. **Local Processing**: All AI processing happens on your local machine
5. **Privacy**: Your code never leaves your local environment

## 🛠️ Troubleshooting

### Connection Issues

```bash
# Test Ollama connection locally
curl http://localhost:11434/api/tags

# Test backend connection
curl https://backend-production-ee56.up.railway.app/health
```

### Model Not Available

1. Make sure the model is pulled in Ollama:
   ```bash
   ollama list
   ollama pull codellama:7b
   ```

2. Restart the tunnel client after pulling new models

### WebSocket Connection Failed

1. Check if your firewall is blocking WebSocket connections
2. Try using a different backend URL if there are regional issues
3. Check the Railway backend logs for any errors

## 🔒 Security

- **No Data Storage**: Your code is never stored on the Railway backend
- **Local Processing**: All AI analysis happens on your machine
- **Encrypted Connection**: WebSocket connections are encrypted
- **Optional Authentication**: You can use guest mode or authenticate with your account

## 📊 Monitoring

The tunnel client provides real-time status information:

- ✅ **Connected**: Tunnel is active and models are available
- 🔄 **Reconnecting**: Attempting to reconnect after disconnection
- ❌ **Error**: Connection failed or Ollama is not responding

## 🚀 Advanced Usage

### Custom Model Configuration

You can configure custom models by modifying the tunnel client or backend mapping.

### Multiple Users

Each user can have their own tunnel connection with their own models.

### Load Balancing

The system can handle multiple tunnel connections and distribute requests appropriately.

## 📝 Example Output

```
🚀 Starting Ollama Tunnel Client...
   Backend: https://backend-production-ee56.up.railway.app
   Ollama: http://localhost:11434
   User: guest
🔍 Testing Ollama connection...
✅ Ollama connected! Found 3 models:
   - codellama:7b
   - devstral
   - gemma3n
🔌 Connecting to WebSocket: wss://backend-production-ee56.up.railway.app/api/ollama/tunnel?user_id=guest&ollama_url=http://localhost:11434
✅ WebSocket tunnel established!
✅ Tunnel established successfully
📋 Sent model list: 3 models
✅ WebSocket tunnel established!
```

## 🆘 Support

If you encounter any issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the Railway backend logs
3. Ensure Ollama is running and accessible
4. Verify your network connection

The tunnel system is designed to be robust and will automatically reconnect if the connection is lost.
