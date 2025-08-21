#!/bin/bash

# 🚀 Rituo Backend Deployment Script for Digital Ocean
# This script automates the deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on Digital Ocean droplet
check_environment() {
    print_info "Checking deployment environment..."
    
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot determine OS. This script is designed for Ubuntu/Debian."
        exit 1
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_warning "This script is optimized for Ubuntu/Debian. Proceeding anyway..."
    fi
    
    print_success "Environment check completed"
}

# Install Docker if not present
install_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker is already installed"
        return
    fi
    
    print_info "Installing Docker..."
    
    # Update package index
    apt-get update
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Install Docker Compose
    apt-get install -y docker-compose
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker installed successfully"
}

# Create application directory
setup_app_directory() {
    APP_DIR="/opt/rituo"
    print_info "Setting up application directory: $APP_DIR"
    
    mkdir -p $APP_DIR
    cd $APP_DIR
    
    print_success "Application directory created"
}

# Deploy application
deploy_application() {
    print_info "Deploying Rituo backend..."
    
    # Check if environment file exists
    if [[ ! -f .env.production ]]; then
        print_error "Environment file .env.production not found!"
        print_info "Please create .env.production with your configuration."
        print_info "You can use server/env.production.example as a template."
        exit 1
    fi
    
    # Validate required environment variables
    print_info "Validating environment configuration..."
    
    # Source the environment file
    set -a
    source .env.production
    set +a
    
    # Check critical variables
    if [[ -z "$GOOGLE_OAUTH_CLIENT_ID" ]]; then
        print_error "GOOGLE_OAUTH_CLIENT_ID is not set in .env.production"
        exit 1
    fi
    
    if [[ -z "$GOOGLE_OAUTH_CLIENT_SECRET" ]]; then
        print_error "GOOGLE_OAUTH_CLIENT_SECRET is not set in .env.production"
        exit 1
    fi
    
    if [[ -z "$MONGODB_URL" ]]; then
        print_error "MONGODB_URL is not set in .env.production"
        exit 1
    fi
    
    # GROQ_API_KEY is optional with BYOK (Bring Your Own Key) implementation
    if [[ -z "$GROQ_API_KEY" ]]; then
        print_warning "GROQ_API_KEY not set - using BYOK (users provide their own keys)"
    else
        print_info "GROQ_API_KEY found - will be used as fallback"
    fi
    
    print_success "Environment validation completed"
    
    # Deploy with Docker Compose
    print_info "Starting Docker containers..."
    
    docker-compose -f docker-compose.production.yml --env-file .env.production down || true
    docker-compose -f docker-compose.production.yml --env-file .env.production pull
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d
    
    print_success "Application deployed successfully"
}

# Configure firewall
setup_firewall() {
    print_info "Configuring firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Configure firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow essential services
    ufw allow ssh
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 8000/tcp  # FastAPI
    ufw allow 8001/tcp  # MCP Server
    
    # Enable firewall
    ufw --force enable
    
    print_success "Firewall configured"
}

# Health check
health_check() {
    print_info "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check if containers are running
    if ! docker ps | grep -q rituo-backend; then
        print_error "Backend container is not running!"
        print_info "Checking logs..."
        docker-compose -f docker-compose.production.yml logs rituo-backend
        exit 1
    fi
    
    # Check API health endpoint
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        print_info "Health check attempt $attempt/$max_attempts..."
        
        if curl -f -s http://localhost:8000/health > /dev/null; then
            print_success "Health check passed!"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "Health check failed after $max_attempts attempts"
            print_info "Checking logs..."
            docker-compose -f docker-compose.production.yml logs rituo-backend
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
}

# Display deployment information
show_deployment_info() {
    print_success "🎉 Deployment completed successfully!"
    echo
    print_info "📋 Deployment Information:"
    echo "  • API URL: http://$(curl -s ifconfig.me):8000"
    echo "  • MCP Server: http://$(curl -s ifconfig.me):8001"
    echo "  • Health Check: http://$(curl -s ifconfig.me):8000/health"
    echo
    print_info "📁 Application Directory: /opt/rituo"
    echo
    print_info "🔧 Useful Commands:"
    echo "  • View logs: docker-compose -f /opt/rituo/docker-compose.production.yml logs -f"
    echo "  • Restart: docker-compose -f /opt/rituo/docker-compose.production.yml restart"
    echo "  • Stop: docker-compose -f /opt/rituo/docker-compose.production.yml down"
    echo "  • Update: cd /opt/rituo && git pull && ./deploy.sh"
    echo
    print_warning "🔒 Next Steps:"
    echo "  1. Configure your domain DNS to point to this server"
    echo "  2. Update Google OAuth redirect URIs in Google Cloud Console"
    echo "  3. Set up SSL certificate (recommended for production)"
    echo "  4. Update your Vercel frontend environment variables"
    echo
    print_info "📚 For detailed instructions, see: DEPLOYMENT_DIGITAL_OCEAN.md"
}

# Main deployment function
main() {
    print_info "🚀 Starting Rituo Backend Deployment"
    echo
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    check_environment
    install_docker
    setup_app_directory
    deploy_application
    setup_firewall
    health_check
    show_deployment_info
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
