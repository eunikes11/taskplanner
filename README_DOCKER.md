# 🐳 Docker Deployment Guide

This guide covers deploying the Kid-Friendly Task Planner using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM
- At least 2GB free disk space

### One-Command Deployment
```bash
# Clone the repository (or ensure you have all files)
git clone <your-repo-url>
cd task-planner

# Copy environment template
cp .env.example .env

# Edit environment variables (important!)
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## 📁 Project Structure
```
task-planner/
├── docker-compose.yml          # Main orchestration file
├── .env.example               # Environment template
├── mongo-init.js              # MongoDB initialization
├── nginx.conf                 # Main Nginx config
├── backend/
│   ├── Dockerfile            # Backend container config
│   ├── server.py             # FastAPI application
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── Dockerfile            # Frontend container config
│   ├── nginx.conf            # Frontend Nginx config
│   ├── package.json          # Node.js dependencies
│   └── src/                  # React source code
└── README_DOCKER.md          # This file
```

## 🔧 Configuration

### Environment Variables
Create `.env` file from template:
```bash
cp .env.example .env
```

**Critical variables to change:**
```env
# Strong MongoDB password
MONGO_INITDB_ROOT_PASSWORD=your-secure-password-here

# Long random JWT secret
JWT_SECRET=your-super-long-random-jwt-secret-key-here

# Your server's IP/domain
REACT_APP_BACKEND_URL=http://your-server-ip:8001
```

### Port Configuration
Default ports:
- **80**: Main application (Nginx proxy)
- **3000**: Direct frontend access
- **8001**: Backend API
- **27017**: MongoDB (internal only)

To change ports, edit `docker-compose.yml`:
```yaml
services:
  nginx:
    ports:
      - "8080:80"  # Change main port to 8080
```

## 🏗️ Services Overview

### 🗄️ MongoDB Service
- **Image**: `mongo:7.0`
- **Purpose**: Database storage
- **Data**: Persisted in `mongodb_data` volume
- **Health Check**: Automatic ping test

### ⚡ Backend Service
- **Built from**: `./backend/Dockerfile`
- **Purpose**: FastAPI REST API
- **Dependencies**: MongoDB
- **Health Check**: HTTP GET to `/api/`

### 🎨 Frontend Service
- **Built from**: `./frontend/Dockerfile`
- **Purpose**: React application
- **Build**: Multi-stage (Node.js build + Nginx serve)
- **Dependencies**: Backend service

### 🌐 Nginx Proxy
- **Image**: `nginx:alpine`
- **Purpose**: Reverse proxy and load balancer
- **Features**: Rate limiting, CORS, security headers
- **Optional**: Can be removed to access services directly

## 🚀 Deployment Scenarios

### Development Environment
```bash
# Start with logs visible
docker-compose up

# Start in background
docker-compose up -d

# Follow logs
docker-compose logs -f
```

### Production Environment
```bash
# Set production environment
export ENVIRONMENT=production

# Use production compose file (if you create one)
docker-compose -f docker-compose.prod.yml up -d

# Enable log rotation
docker-compose logs --tail=100 -f
```

### Custom Domain Setup
1. **Update environment:**
```env
REACT_APP_BACKEND_URL=https://yourdomain.com
DOMAIN_NAME=yourdomain.com
```

2. **Add SSL certificates:**
```bash
mkdir ssl
# Copy your cert.pem and key.pem to ssl/
```

3. **Enable HTTPS in nginx.conf** (uncomment SSL section)

## 🔒 Security Best Practices

### 1. Change Default Passwords
```env
MONGO_INITDB_ROOT_PASSWORD=use-strong-password-here
JWT_SECRET=use-very-long-random-string-here
```

### 2. Network Security
- Services communicate on internal Docker network
- Only necessary ports exposed to host
- Nginx provides additional security layer

### 3. Container Security
- Non-root users in containers
- Read-only filesystems where possible
- Health checks for all services

### 4. Data Protection
- MongoDB data persisted in Docker volumes
- Regular backups recommended
- Environment variables not in images

## 📊 Monitoring and Logs

### Check Service Status
```bash
# All services
docker-compose ps

# Detailed status
docker-compose top
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f --tail=100
```

### Resource Usage
```bash
# Container stats
docker stats

# Specific compose project
docker stats $(docker-compose ps -q)
```

## 🛠️ Maintenance

### Update Application
```bash
# Pull latest images
docker-compose pull

# Rebuild custom images
docker-compose build --no-cache

# Restart with new images
docker-compose up -d
```

### Backup Data
```bash
# Create MongoDB backup
docker-compose exec mongodb mongodump \
  --authenticationDatabase admin \
  -u admin \
  -p your-password \
  --out /backup

# Copy backup to host
docker cp task-planner-mongodb:/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Restore Data
```bash
# Copy backup to container
docker cp ./mongodb-backup task-planner-mongodb:/restore

# Restore from backup
docker-compose exec mongodb mongorestore \
  --authenticationDatabase admin \
  -u admin \
  -p your-password \
  /restore
```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (⚠️ DELETES DATA)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker system prune -a
```

## 🔧 Troubleshooting

### Common Issues

**1. Port conflicts**
```bash
# Check what's using ports
netstat -tulpn | grep :80
netstat -tulpn | grep :8001

# Change ports in docker-compose.yml
```

**2. Permission issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker socket permissions
sudo usermod -aG docker $USER
```

**3. Memory issues**
```bash
# Check available memory
free -h

# Add memory limits to services
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 512M
```

**4. Build failures**
```bash
# Clean build
docker-compose build --no-cache

# Check Docker daemon
systemctl status docker

# Check disk space
df -h
```

### Health Check Failures
```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect task-planner-backend --format='{{.State.Health}}'

# Manual health check
docker-compose exec backend curl -f http://localhost:8001/api/
```

## 🔄 Scaling and Performance

### Horizontal Scaling
```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Scale with load balancer updates
# Edit nginx.conf to add multiple backend servers
```

### Resource Limits
```yaml
# Add to docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

### Performance Monitoring
```bash
# Container performance
docker stats

# Application metrics
curl http://localhost:8001/api/health

# Database performance
docker-compose exec mongodb mongo --eval "db.stats()"
```

## 🌐 External Access

### Reverse Proxy Setup (Traefik/Nginx)
```yaml
# Add labels for Traefik
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.taskplanner.rule=Host(`tasks.yourdomain.com`)"
  - "traefik.http.routers.taskplanner.tls=true"
```

### CloudFlare Tunnel
```bash
# Install cloudflared
# Create tunnel pointing to localhost:80
cloudflared tunnel --url http://localhost:80
```

## 📈 Monitoring Setup

### Health Check Endpoints
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8001/api/`
- **Full Stack**: `http://localhost:80`

### Prometheus Metrics (Optional)
Add monitoring to docker-compose.yml:
```yaml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🎯 Success Checklist

✅ **All containers running**: `docker-compose ps`
✅ **Frontend accessible**: Visit `http://localhost:80`
✅ **Backend responding**: `curl http://localhost:8001/api/`
✅ **Database connected**: Check backend logs
✅ **User registration works**: Create test account
✅ **Task creation works**: Add and complete tasks
✅ **Data persists**: Restart containers, data remains

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Test connectivity: `docker-compose exec backend curl http://mongodb:27017`
4. Check resources: `docker stats`

Your Kid-Friendly Task Planner is now ready to run anywhere Docker runs! 🎉