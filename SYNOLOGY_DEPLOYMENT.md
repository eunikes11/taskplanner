# 🚀 Synology NAS Deployment Guide

This guide will help you deploy the **Kid-Friendly Task Planner** on your Synology NAS using Docker Compose.

## 📋 Prerequisites

### Synology NAS Requirements
- **DSM 7.0 or later**
- **Docker package installed** (available in Package Center)
- **At least 2GB RAM** (4GB recommended)
- **At least 2GB free storage space**

### Enable SSH (Optional but recommended)
1. Go to **Control Panel** → **Terminal & SNMP**
2. Enable **SSH service**
3. Note the port number (default: 22)

## 🏗️ Installation Steps

### Step 1: Install Docker on Synology

1. Open **Package Center** on your Synology DSM
2. Search for **Docker** and click **Install**
3. Wait for installation to complete
4. Launch **Docker** from the main menu

### Step 2: Prepare the Project Files

#### Option A: Using File Station (GUI Method)
1. Open **File Station**
2. Navigate to `/docker` folder (create if it doesn't exist)
3. Create a new folder called `task-planner`
4. Upload all project files to `/docker/task-planner/`

#### Option B: Using SSH (Command Line Method)
```bash
# Connect to your NAS via SSH
ssh admin@YOUR_NAS_IP

# Navigate to docker directory
cd /volume1/docker

# Clone or create the project directory
mkdir task-planner
cd task-planner

# Copy your project files here
# You can use scp, git, or other methods to transfer files
```

### Step 3: Configure Environment Variables

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your preferred settings:
```bash
# Use vi, nano, or edit through File Station
nano .env
```

**Important:** Change these values for security:
- `MONGO_INITDB_ROOT_PASSWORD`: Strong MongoDB password
- `JWT_SECRET`: Long random string for JWT signing
- `REACT_APP_BACKEND_URL`: Your NAS IP address

Example configuration:
```env
MONGO_INITDB_ROOT_PASSWORD=MySecure123Password!
JWT_SECRET=super-long-random-string-for-jwt-signing-12345678901234567890
REACT_APP_BACKEND_URL=http://192.168.1.100:8001
```

### Step 4: Deploy with Docker Compose

#### Option A: Using Docker GUI
1. Open **Docker** application
2. Go to **Project** tab
3. Click **Create**
4. Set **Project Name**: `task-planner`
5. Set **Path**: `/docker/task-planner`
6. Click **Create**

#### Option B: Using Command Line
```bash
# Navigate to project directory
cd /volume1/docker/task-planner

# Start the services
sudo docker-compose up -d

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f
```

### Step 5: Verify Deployment

1. **Check Docker containers:**
   - Open Docker → Container
   - You should see 4 containers running:
     - `task-planner-mongodb`
     - `task-planner-backend`
     - `task-planner-frontend`
     - `task-planner-nginx`

2. **Test the application:**
   - Open browser and go to: `http://YOUR_NAS_IP:80`
   - You should see the task planner login screen

## 🌐 Accessing Your Task Planner

### Local Network Access
- **Main Application**: `http://YOUR_NAS_IP:80`
- **Direct Frontend**: `http://YOUR_NAS_IP:3000`
- **Backend API**: `http://YOUR_NAS_IP:8001/api`

### Finding Your NAS IP Address
1. Go to **Control Panel** → **Network** → **Network Interface**
2. Note the IP address under your active connection

## 🔒 Security Configuration

### Change Default Passwords
```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Update these sections:
MONGO_INITDB_ROOT_PASSWORD: your-secure-password
JWT_SECRET: your-secure-jwt-secret
```

### Firewall Configuration
1. Go to **Control Panel** → **Security** → **Firewall**
2. Create rules for required ports:
   - Port 80 (HTTP)
   - Port 443 (HTTPS - if using SSL)
   - Port 3000 (Frontend - optional)
   - Port 8001 (Backend API)

### Optional: Enable HTTPS

1. **Get SSL Certificate:**
   - Use **Control Panel** → **Security** → **Certificate**
   - Import or create a certificate

2. **Configure Nginx for HTTPS:**
   - Uncomment HTTPS section in `nginx.conf`
   - Update certificate paths
   - Restart containers: `docker-compose restart`

## 📊 Monitoring and Maintenance

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Update Application
```bash
# Pull latest changes
git pull  # if using git

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup Data
```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --authenticationDatabase admin -u admin -p taskplanner123 --out /backup

# Copy backup from container
docker cp task-planner-mongodb:/backup ./mongodb-backup
```

### Resource Usage
- Monitor in **Resource Monitor** or Docker GUI
- Typical usage: ~500MB RAM, minimal CPU
- Storage: ~1GB for application + data growth

## 🔧 Troubleshooting

### Common Issues

**1. Containers won't start**
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Restart services
docker-compose restart
```

**2. Can't access application**
```bash
# Check if ports are open
netstat -tulpn | grep :80
netstat -tulpn | grep :8001

# Check firewall rules
# Verify IP address in browser
```

**3. Database connection issues**
```bash
# Check MongoDB health
docker-compose exec mongodb mongo --eval "db.adminCommand('ping')"

# Reset database
docker-compose down -v
docker-compose up -d
```

**4. Memory issues**
```bash
# Check memory usage
free -h

# Reduce Docker memory if needed
# Edit docker-compose.yml and add memory limits
```

### Performance Optimization

**For better performance on Synology:**
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

## 📝 Maintenance Schedule

### Weekly
- Check container health in Docker GUI
- Review application logs for errors
- Monitor disk space usage

### Monthly
- Update Docker images: `docker-compose pull`
- Backup MongoDB data
- Review security settings

### As Needed
- Update application code
- Renew SSL certificates
- Scale resources if needed

## 🆘 Support

If you encounter issues:

1. **Check logs first**: `docker-compose logs -f`
2. **Restart services**: `docker-compose restart`
3. **Check Synology forums** for Docker-specific issues
4. **Verify network connectivity** and firewall rules

## 🎉 Success!

Your Kid-Friendly Task Planner is now running on your Synology NAS! 

- **Accessible 24/7** from your local network
- **Data persisted** in MongoDB with automatic backups
- **Secure and private** - no external dependencies
- **Easy to maintain** with Docker Compose

Enjoy helping kids organize their tasks with this awesome planner! 🌟