# 🌐 Vercel Frontend Deployment Guide

This guide helps you deploy the Rituo frontend to Vercel while connecting it to your Digital Ocean backend.

## 📋 Prerequisites

- Vercel account
- GitHub repository with your Rituo code
- Digital Ocean backend deployed and running

## 🚀 Step 1: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"New Project"**
3. Import your GitHub repository
4. Select the **root directory** (not `/src`)
5. Vercel will auto-detect Next.js settings
6. Click **"Deploy"**

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from your project root
cd /path/to/rituo
vercel

# Follow the prompts:
# - Set up and deploy: Y
# - Which scope: Your account
# - Link to existing project: N
# - Project name: rituo-frontend (or your choice)
# - In which directory: ./ (root)
# - Want to override settings: N

# For production deployment
vercel --prod
```

## ⚙️ Step 2: Configure Environment Variables

### Add Environment Variables in Vercel

1. Go to your project in Vercel Dashboard
2. Navigate to **Settings > Environment Variables**
3. Add these variables:

```bash
# Backend API Configuration
NEXT_PUBLIC_API_URL=https://your-domain.com:8000
# OR if using IP: NEXT_PUBLIC_API_URL=http://your-droplet-ip:8000

# MCP Server Configuration
NEXT_PUBLIC_MCP_URL=https://your-domain.com:8001
# OR if using IP: NEXT_PUBLIC_MCP_URL=http://your-droplet-ip:8001

# Environment
NEXT_PUBLIC_ENVIRONMENT=production

# Optional: Analytics/Monitoring
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Environment Variable Settings
- **Environment**: Production, Preview, Development (choose Production)
- **Branch**: All branches (or specify main/master)

## 🔄 Step 3: Update Backend CORS

### Update Digital Ocean Backend
SSH into your Digital Ocean droplet and update the environment:

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Edit environment file
cd /opt/rituo
nano .env.production

# Add your Vercel URL
FRONTEND_URL=https://your-vercel-app.vercel.app
ENVIRONMENT=production

# Restart the backend
docker-compose -f docker-compose.production.yml restart
```

## 🔒 Step 4: Update Google OAuth Configuration

### Add Vercel Domain to Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add to **Authorized JavaScript origins**:
   ```
   https://your-vercel-app.vercel.app
   https://your-custom-domain.com  (if using custom domain)
   ```

5. Add to **Authorized redirect URIs**:
   ```
   https://your-vercel-app.vercel.app/oauth-success
   https://your-custom-domain.com/oauth-success  (if using custom domain)
   ```

## 🌐 Step 5: Custom Domain (Optional)

### Add Custom Domain in Vercel

1. In Vercel Dashboard, go to **Settings > Domains**
2. Add your custom domain (e.g., `app.yourdomain.com`)
3. Configure DNS in your domain registrar:
   - **CNAME record**: `app` → `cname.vercel-dns.com`
   - Or follow Vercel's specific instructions

### Update Environment Variables
If using a custom domain, update:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com:8000
NEXT_PUBLIC_MCP_URL=https://api.yourdomain.com:8001
```

## 🔧 Step 6: Optimize for Production

### Update Next.js Configuration

Create or update `next.config.ts`:

```typescript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Optimize for production
  compress: true,
  poweredByHeader: false,
  
  // Environment-specific settings
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  
  // Handle API routes
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
  
  // CORS headers for embedded usage
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

## 📊 Step 7: Monitoring and Analytics

### Add Vercel Analytics

1. In Vercel Dashboard, go to **Analytics**
2. Enable Vercel Analytics for your project
3. Add the analytics script to your app

### Environment-Specific Logging

Update your frontend code to handle different environments:

```typescript
// utils/logger.ts
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NEXT_PUBLIC_ENVIRONMENT === 'production';

export const logger = {
  log: (message: string, ...args: any[]) => {
    if (!isProduction) {
      console.log(message, ...args);
    }
  },
  error: (message: string, ...args: any[]) => {
    console.error(message, ...args);
    // In production, you might want to send to error tracking service
  },
};
```

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Errors**
   ```bash
   # Check if backend is accessible
   curl https://your-domain.com:8000/health
   
   # Verify CORS configuration
   # Check browser network tab for CORS errors
   ```

2. **OAuth Redirect Issues**
   - Verify redirect URIs in Google Cloud Console match exactly
   - Ensure URLs use HTTPS in production
   - Check for trailing slashes

3. **Environment Variables Not Loading**
   ```bash
   # Redeploy after adding environment variables
   vercel --prod
   
   # Check environment variables are set
   vercel env ls
   ```

### Useful Commands

```bash
# View deployment logs
vercel logs your-deployment-url

# Check environment variables
vercel env ls

# Redeploy
vercel --prod

# Check domain configuration
vercel domains ls

# Remove deployment
vercel remove your-project-name
```

## 🔄 Step 8: Continuous Deployment

### Automatic Deployments

Vercel automatically deploys when you push to your main branch. To configure:

1. Go to **Settings > Git**
2. Configure auto-deployment settings
3. Set production branch (usually `main` or `master`)

### Preview Deployments

Vercel creates preview deployments for every push to non-production branches:
- Each PR gets a unique preview URL
- Great for testing before merging
- Automatically cleaned up when PR is closed

## ✅ Final Checklist

- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Backend CORS updated with Vercel URL
- [ ] Google OAuth configured with new domains
- [ ] Custom domain configured (if desired)
- [ ] HTTPS enforced
- [ ] Analytics enabled
- [ ] Error monitoring configured

## 🎉 You're Done!

Your Rituo application is now fully deployed:

- **Frontend**: `https://your-vercel-app.vercel.app`
- **Backend**: `https://your-domain.com:8000`
- **Authentication**: OAuth flow working end-to-end

Test the complete flow by accessing your frontend and signing in with Google!
