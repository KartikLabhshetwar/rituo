# 🚀 Rituo Deployment Guide

## Architecture Overview

Rituo is a **Google Workspace AI Assistant** with the following architecture:

```
Frontend (Next.js) → FastAPI Server → MCP Server → Google APIs
                           ↓
                      MongoDB Database
```

## 📋 Prerequisites

### 1. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable these APIs:
   - Google Calendar API
   - Gmail API
   - Google Tasks API
4. Create OAuth 2.0 credentials:
   - Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
   - Application type: Web application
   - Authorized redirect URIs:
     - `http://localhost:8001/auth/callback` (for MCP server)
     - `http://localhost:3000/oauth-success` (for frontend)

### 2. Get API Keys
- **Groq API Key**: Get from [Groq Console](https://console.groq.com/)
- **MongoDB**: Install locally or use [MongoDB Atlas](https://www.mongodb.com/atlas)

## 🛠️ Development Setup

### 1. Environment Configuration
```bash
cd server
python setup_environment.py
```

This creates a `.env` file. Update it with your actual credentials:

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GROQ_API_KEY=your_groq_api_key
MONGODB_URL=mongodb://localhost:27017/rituo
```

### 2. Install Dependencies

**Backend:**
```bash
cd server
pip install uv
uv sync
```

**Frontend:**
```bash
npm install
```

### 3. Start Development Servers

**Option A: Start All at Once**
```bash
cd server
python start_simple.py
```

Then in another terminal:
```bash
npm run dev
```

**Option B: Start Individually**
```bash
# Terminal 1: MCP Server
cd server
python mcp_server_simple.py

# Terminal 2: FastAPI Server  
cd server
python app.py

# Terminal 3: Frontend
npm run dev
```

### 4. Test the Setup
```bash
cd server
python test_mcp_integration.py
```

## 🌐 Production Deployment

### Using Docker Compose
```bash
# Create .env file in project root with your credentials
cp server/.env .env

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Manual Production Setup

1. **Set up reverse proxy** (nginx/Apache) for HTTPS
2. **Configure environment variables** for production URLs
3. **Set up monitoring** and logging
4. **Configure database backups**
5. **Set up CI/CD pipeline**

## 🔧 How It Works

### Authentication Flow
1. User visits frontend → redirected to login
2. User clicks "Sign in with Google" → redirected to Google OAuth
3. Google redirects to MCP server → MCP server handles OAuth
4. MCP server creates session → redirects to frontend success page
5. Frontend gets tokens → user can now chat

### Chat Flow
1. User types message in frontend
2. Frontend sends to FastAPI `/api/ai/chat`
3. FastAPI processes with Groq AI
4. AI determines if MCP tools needed
5. FastAPI calls MCP server tools
6. MCP server calls Google APIs
7. Response flows back to user

### Available Commands
Users can say things like:
- "Schedule a meeting with John tomorrow at 2 PM"
- "What meetings do I have today?"
- "Create a task to review the project proposal"
- "Check my unread emails"

## 🐛 Troubleshooting

### Common Issues

**"MCP server not connecting"**
- Check if port 8001 is available
- Verify Google OAuth credentials
- Check logs: `docker-compose logs mcp-server`

**"Authentication failed"**
- Verify Google OAuth redirect URIs
- Check client ID/secret in .env
- Ensure MongoDB is running

**"AI not responding"**
- Check Groq API key
- Verify MCP server is running
- Check FastAPI logs

### Debug Commands
```bash
# Check server health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Check MCP tools
python -c "from fastmcp import Client; import asyncio; asyncio.run(Client('http://localhost:8001/mcp').list_tools())"

# Check database
python -c "from database.connection import connect_to_mongo; import asyncio; asyncio.run(connect_to_mongo())"
```

## 🚀 Scaling for Production

### Performance Optimizations
1. **Use Redis** for session storage
2. **Add rate limiting** to API endpoints
3. **Implement caching** for Google API responses
4. **Use connection pooling** for database
5. **Add monitoring** with Prometheus/Grafana

### Security Considerations
1. **Use HTTPS** in production
2. **Implement CSRF protection**
3. **Add request validation**
4. **Use secure cookie settings**
5. **Implement proper logging**

### Deployment Platforms
- **AWS**: ECS/EKS with RDS
- **Google Cloud**: Cloud Run with Cloud SQL
- **Vercel**: Frontend + Railway/Render for backend
- **DigitalOcean**: App Platform or Droplets

## 📊 Monitoring

### Health Checks
- FastAPI: `GET /health`
- MCP Server: `GET /health` 
- Frontend: `GET /`

### Key Metrics
- Response times
- Error rates
- Google API quota usage
- Database connection pool
- Memory/CPU usage

## 🎯 Next Steps

1. **Add more Google services** (Drive, Docs, Sheets)
2. **Implement real-time notifications**
3. **Add user preferences and settings**
4. **Create mobile app** using React Native
5. **Add team collaboration features**
