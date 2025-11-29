# IoT Device Dashboard - Complete Deployment Guide

## 📦 Project Structure

```
iot-device-dashboard/
├── dashboard.html         # Frontend (single file, ~300KB)
├── server.js              # Backend server
├── package.json           # Node.js dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose orchestration
├── test_mqtt.py          # Python test data simulator
├── .gitignore            # Git ignore patterns
├── README.md             # Full documentation
├── SETUP.md              # Quick start guide
└── DEPLOYMENT.md         # This file
```

## 🚀 Local Development

### Prerequisites
- Node.js 14+ LTS
- npm 6+

### Quick Start
```bash
# 1. Install dependencies
npm install

# 2. Start server
npm start

# 3. Open dashboard
# Browser: http://localhost:3000
# Or directly: open dashboard.html

# 4. Test with simulator (in another terminal)
pip3 install paho-mqtt
python3 test_mqtt.py -b test.mosquitto.org -d 60
```

### Development with Hot Reload
```bash
npm install -g nodemon
npm run dev
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Easiest)

```bash
# Start the dashboard
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the dashboard
docker-compose down

# Rebuild image
docker-compose build --no-cache
```

### Option 2: Docker Build & Run

```bash
# Build image
docker build -t iot-dashboard:1.0 .

# Run container
docker run -d \
  -p 3000:3000 \
  -e PORT=3000 \
  --name iot-dashboard \
  iot-dashboard:1.0

# View logs
docker logs -f iot-dashboard

# Stop container
docker stop iot-dashboard
docker rm iot-dashboard
```

### Docker Network Setup
```bash
# Create network for multiple containers
docker network create iot-network

# Run dashboard on network
docker run -d \
  -p 3000:3000 \
  --network iot-network \
  --name iot-dashboard \
  iot-dashboard:1.0
```

## ☁️ Cloud Deployment

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   curl https://cli.heroku.com/install.sh | sh
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-iot-dashboard
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **View Logs**
   ```bash
   heroku logs --tail
   ```

5. **Set Environment Variables**
   ```bash
   heroku config:set MQTT_BROKER=your-broker-url
   heroku config:set PORT=3000
   ```

### Railway.app Deployment

1. **Connect GitHub Repository**
   - Push code to GitHub
   - Go to railway.app
   - Create new project
   - Select GitHub repository

2. **Configure Environment**
   - Set PORT=3000
   - Railway automatically detects Node.js

3. **Deploy**
   - Push to main branch
   - Railway auto-deploys

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   ```bash
   # Use Ubuntu 22.04 LTS AMI
   # Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 3000
   ```

2. **SSH into Instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install Node.js**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

4. **Clone and Run**
   ```bash
   git clone your-repo.git
   cd iot-device-dashboard
   npm install
   npm start
   ```

5. **Use PM2 for Process Management**
   ```bash
   sudo npm install -g pm2
   pm2 start server.js --name "iot-dashboard"
   pm2 startup
   pm2 save
   ```

6. **Setup Nginx Reverse Proxy**
   ```bash
   sudo apt-get install nginx
   ```
   
   Edit `/etc/nginx/sites-available/default`:
   ```nginx
   server {
       listen 80 default_server;
       server_name _;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```
   
   ```bash
   sudo systemctl restart nginx
   ```

7. **Setup SSL with Certbot**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### DigitalOcean App Platform

1. **Connect Repository**
   - Go to DigitalOcean App Platform
   - Click "Create App"
   - Select GitHub repository

2. **Configure**
   - Source: Automatic detection (Node.js)
   - Environment: Add any required variables
   - HTTP Port: 3000

3. **Deploy**
   - Review and create app
   - App automatically deployed

### Google Cloud Run

```bash
# Install gcloud CLI
# Authenticate
gcloud auth login

# Create service account
gcloud iam service-accounts create iot-dashboard

# Deploy
gcloud run deploy iot-dashboard \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PORT=3000
```

## 🔒 Production Checklist

- [ ] Use HTTPS/WSS for all connections
- [ ] Enable CORS restrictions (not `*`)
- [ ] Add authentication to MQTT broker
- [ ] Setup proper logging and monitoring
- [ ] Use environment variables for secrets
- [ ] Set up database for data persistence
- [ ] Configure rate limiting
- [ ] Setup automated backups
- [ ] Enable GZIP compression
- [ ] Setup CDN for static files
- [ ] Monitor CPU, memory, disk usage
- [ ] Setup health checks and alerts
- [ ] Use load balancer for high availability
- [ ] Implement graceful shutdown
- [ ] Setup auto-scaling policies

## 📊 Production Configuration

### Environment Variables

Create `.env` file:
```bash
NODE_ENV=production
PORT=3000
MQTT_TIMEOUT=10000
RFID_MAX_HISTORY=1000
LOG_LEVEL=info
CORS_ORIGIN=https://your-domain.com
```

### Performance Tuning

Edit `server.js` for production:
```javascript
// Increase RFID history
const maxRFIDHistory = process.env.RFID_MAX_HISTORY || 1000;

// Add compression
const compression = require('compression');
app.use(compression());

// Add rate limiting
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
app.use(limiter);
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Deploy to Heroku
        env:
          HEROKU_API_KEY: ${{ secrets.HEROKU_API_KEY }}
        run: |
          git push heroku main
```

## 📈 Monitoring & Logging

### Application Logs

```bash
# View logs in real-time
npm start | tee app.log

# Archive logs
gzip app.log
```

### System Monitoring

Use PM2 Monitoring:
```bash
pm2 web  # Starts web dashboard on http://localhost:9615

# Monitor specific process
pm2 monit
```

### Health Check Endpoint

```bash
curl http://localhost:3000/api/stats
```

### External Monitoring

Setup with tools like:
- **New Relic**
- **Datadog**
- **CloudWatch** (AWS)
- **Stackdriver** (Google Cloud)

## 🚨 Troubleshooting Production

### High Memory Usage
```bash
# Check memory
ps aux | grep node

# Increase Node heap size
NODE_OPTIONS=--max-old-space-size=4096 npm start
```

### Connection Timeouts
```javascript
// Increase timeouts in server.js
mqtt.connect(brokerUrl, {
  connectTimeout: 30000,  // 30 seconds
  reconnectPeriod: 10000  // 10 seconds
});
```

### MQTT Broker Connection Lost
- Check broker health
- Verify network connectivity
- Review firewall rules
- Check MQTT credentials

### Dashboard Not Responding
```bash
# Restart server
pm2 restart iot-dashboard

# Check port conflicts
lsof -i :3000

# Check error logs
pm2 logs iot-dashboard --err
```

## 🔧 Maintenance Tasks

### Regular Backups

```bash
# Backup configuration
tar czf backup-$(date +%Y%m%d).tar.gz \
  server.js \
  package.json \
  dashboard.html

# Automated backup with cron
0 2 * * * tar czf /backups/backup-$(date +\%Y\%m\%d).tar.gz /app
```

### Update Dependencies

```bash
# Check for updates
npm outdated

# Update packages
npm update

# Update major versions
npm install package@latest
```

### Cleanup Old Logs

```bash
# Setup log rotation with logrotate
cat > /etc/logrotate.d/iot-dashboard <<EOF
/var/log/iot-dashboard.log {
  daily
  missingok
  rotate 14
  compress
  delaycompress
  notifempty
  create 0640 www-data www-data
}
EOF
```

## 📝 Scaling Strategies

### Horizontal Scaling

Using load balancer (Nginx):
```nginx
upstream iot_backend {
  server localhost:3000;
  server localhost:3001;
  server localhost:3002;
}

server {
  listen 80;
  location / {
    proxy_pass http://iot_backend;
  }
}
```

### Database Persistence

Add MongoDB:
```bash
docker-compose.yml
version: '3.8'
services:
  app:
    # ... app config
  mongodb:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db
volumes:
  mongo-data:
```

### Message Queue

For high-volume data:
```bash
# Add RabbitMQ
docker run -d \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

## 📞 Support Resources

- **Documentation**: See README.md
- **Logs**: Check server output and logs/
- **Health Check**: GET /api/stats
- **MQTT Debug**: Use mqtt.fx tool
- **Browser DevTools**: F12 for frontend debugging

---

Last Updated: November 29, 2025
