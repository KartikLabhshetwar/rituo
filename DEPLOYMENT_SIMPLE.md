# 🚀 Simple Deployment Guide - Rituo Backend

## ✨ What's Different with BYOK (Bring Your Own Key)

- **No Groq API key needed** in backend environment
- **Simplified configuration** - users provide keys in frontend
- **No GitHub Actions** - simpler manual deployment
- **Cost-effective** - users pay for their own AI usage

## 🏃‍♂️ Quick Start (5 minutes)

### 1. Set up Digital Ocean Droplet
```bash
# Create Ubuntu 22.04 droplet (2GB RAM minimum)
# SSH into your droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
```

### 2. Clone and Configure
```bash
# Clone repository
cd /opt
git clone https://github.com/your-username/rituo.git
cd rituo

# Copy environment template
cd server
cp env.production.example .env.production

# Edit with your values
nano .env.production
```

### 3. Required Environment Variables
```bash
# Google OAuth (Required)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# Database (Required)
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/rituo_app

# Server Config (Update with your domain)
WORKSPACE_MCP_BASE_URI=https://your-domain.com
GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.com:8001/oauth2callback

# NO GROQ_API_KEY NEEDED! Users provide their own ✨
```

### 4. Deploy
```bash
# Build and start
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

### 5. Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

## 🔧 Update Frontend Environment

Update your Vercel environment variables:
```bash
# Update API URLs to point to your Digital Ocean droplet
NEXT_PUBLIC_API_URL=https://your-domain.com:8000
```

## 📝 That's It!

Your backend is now running with:
- ✅ **No API key costs** for you
- ✅ **Users control their own usage**
- ✅ **Simple deployment**
- ✅ **Easy updates**

## 🔄 To Update
```bash
cd /opt/rituo
git pull
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build
```
