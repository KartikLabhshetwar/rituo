# 🚀 Digital Ocean Deployment Guide for Rituo Backend

This guide will help you deploy the Rituo backend to Digital Ocean while keeping the frontend on Vercel.

## 📋 Prerequisites

1. **Digital Ocean Account** with a Droplet (Ubuntu 22.04 LTS recommended)
2. **Domain Name** (optional but recommended for production)
3. **Google Cloud Console** access for OAuth configuration
4. **MongoDB Atlas** account (or self-hosted MongoDB)
5. ✨ **NO GROQ API KEY NEEDED** - Users provide their own keys (BYOK)

## 🛠️ Step 1: Prepare Your Digital Ocean Droplet

### Create Droplet
1. Log in to Digital Ocean
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic plan, 2GB RAM minimum (4GB recommended)
   - **Region**: Choose closest to your users
   - **Authentication**: SSH keys (recommended)

### SSH into Your Droplet
```bash
ssh root@your-droplet-ip
```

### Install Docker and Docker Compose
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Start Docker service
systemctl start docker
systemctl enable docker

# Add user to docker group (optional)
usermod -aG docker root
```

## 🔧 Step 2: Configure Environment Variables

### Create Environment File
```bash
# Create app directory
mkdir -p /opt/rituo
cd /opt/rituo

# Create production environment file
nano .env.production
```

### Environment Configuration
Copy the content from `server/env.production.example` and update these critical values:

```bash
# =============================================================================
# GOOGLE OAUTH CREDENTIALS (REQUIRED)
# =============================================================================
GOOGLE_OAUTH_CLIENT_ID=your-actual-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-actual-google-client-secret

# =============================================================================
# SERVER CONFIGURATION FOR DIGITAL OCEAN
# =============================================================================
# Replace with your domain or droplet IP
WORKSPACE_MCP_BASE_URI=https://your-domain.com
GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.com:8001/oauth2callback

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/rituo_app

# =============================================================================
# AI CONFIGURATION
# =============================================================================
GROQ_API_KEY=your-actual-groq-api-key

# =============================================================================
# CORS CONFIGURATION
# =============================================================================
FRONTEND_URL=https://your-vercel-app.vercel.app
ENVIRONMENT=production
```

## 📁 Step 3: Deploy Your Application

### Option A: Deploy from Git Repository (Recommended)

```bash
# Clone your repository
git clone https://github.com/your-username/rituo.git /opt/rituo
cd /opt/rituo

# Copy environment file
cp server/env.production.example .env.production
# Edit .env.production with your actual values
nano .env.production

# Build and run
docker-compose -f docker-compose.production.yml --env-file .env.production up -d
```

### Option B: Manual File Upload

```bash
# On your local machine, create deployment package
cd /path/to/your/rituo/project
tar -czf rituo-backend.tar.gz server/ docker-compose.production.yml

# Upload to Digital Ocean
scp rituo-backend.tar.gz root@your-droplet-ip:/opt/

# On Digital Ocean droplet
cd /opt
tar -xzf rituo-backend.tar.gz
mv server rituo-backend
cd rituo-backend

# Create environment file and deploy
cp env.production.example .env.production
nano .env.production  # Edit with your values
docker-compose -f ../docker-compose.production.yml --env-file .env.production up -d
```

## 🔒 Step 4: Configure Google OAuth

### Update Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Find your OAuth 2.0 Client ID
4. Add these authorized redirect URIs:
   ```
   https://your-domain.com:8001/oauth2callback
   http://your-droplet-ip:8001/oauth2callback
   ```

### Update Authorized JavaScript Origins
Add these origins:
```
https://your-domain.com
https://your-vercel-app.vercel.app
http://your-droplet-ip
```

## 🌐 Step 5: Configure Domain and SSL (Recommended)

### Point Domain to Droplet
1. In your domain registrar's DNS settings:
   - Create an **A record** pointing to your droplet's IP
   - Example: `api.yourdomain.com` → `your-droplet-ip`

### Install SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Update docker-compose to use SSL
# Edit docker-compose.production.yml to mount certificates
```

## 🔥 Step 6: Configure Firewall

```bash
# Install UFW firewall
ufw enable

# Allow necessary ports
ufw allow ssh
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 8000/tcp # FastAPI
ufw allow 8001/tcp # MCP Server

# Check status
ufw status
```

## 📊 Step 7: Monitor and Manage

### Check Application Status
```bash
# View running containers
docker ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart
```

### Health Check
```bash
# Test API health
curl http://your-domain.com:8000/health

# Expected response:
# {"status":"healthy","service":"rituo-api","version":"1.0.0"}
```

## 🔄 Step 8: Update Frontend Configuration

### Update Vercel Environment Variables
In your Vercel dashboard, set these environment variables:

```bash
NEXT_PUBLIC_API_URL=https://your-domain.com:8000
NEXT_PUBLIC_MCP_URL=https://your-domain.com:8001
```

### Redeploy Frontend
```bash
# In your frontend directory
vercel --prod
```

## 🚨 Troubleshooting

### Common Issues

1. **OAuth Redirect Mismatch**
   - Ensure redirect URIs in Google Console match your deployment URL
   - Check `GOOGLE_OAUTH_REDIRECT_URI` in environment

2. **Database Connection Issues**
   - Verify MongoDB Atlas IP whitelist includes your droplet IP
   - Check `MONGODB_URL` format

3. **CORS Errors**
   - Verify `FRONTEND_URL` matches your Vercel deployment
   - Check CORS origins in logs

4. **Container Won't Start**
   ```bash
   # Check container logs
   docker logs rituo-backend
   
   # Check environment variables
   docker exec rituo-backend env | grep GOOGLE
   ```

### Useful Commands

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs

# Update application
git pull
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# Backup data
docker exec rituo-backend tar -czf /tmp/backup.tar.gz /app

# Monitor resource usage
docker stats
```

## 📈 Performance Optimization

### Enable Log Rotation
```bash
# Add to /etc/logrotate.d/docker-logs
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

### Set Up Monitoring
```bash
# Install htop for monitoring
apt install htop

# Monitor in real-time
htop
```

## 🔐 Security Checklist

- [ ] Use HTTPS in production
- [ ] Configure firewall properly
- [ ] Use strong JWT secrets
- [ ] Regularly update dependencies
- [ ] Monitor logs for suspicious activity
- [ ] Use non-root user in containers
- [ ] Keep Docker images updated

## 🎉 You're Done!

Your Rituo backend is now deployed on Digital Ocean! 

- **API**: `https://your-domain.com:8000`
- **MCP Server**: `https://your-domain.com:8001`
- **Health Check**: `https://your-domain.com:8000/health`

Test the integration by accessing your Vercel frontend and trying to authenticate with Google.
