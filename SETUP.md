# IoT Device Dashboard - Setup & Quick Reference

## 📦 What You Get

This package includes everything needed for a complete real-time IoT tracking dashboard:

1. **dashboard.html** - Complete frontend (single file, no build needed)
2. **server.js** - Node.js backend server
3. **package.json** - Dependencies configuration
4. **README.md** - Full documentation

## ⚡ 5-Minute Setup

### Step 1: Install Node.js
Download from https://nodejs.org/ (LTS version recommended)

### Step 2: Extract Files
```bash
mkdir iot-dashboard
cd iot-dashboard
# Extract all files here
```

### Step 3: Install Dependencies
```bash
npm install
```

This installs:
- express (web server)
- socket.io (real-time updates)
- mqtt (MQTT client)
- cors (cross-origin support)

### Step 4: Start Server
```bash
npm start
```

Expected output:
```
╔═══════════════════════════════════════════════╗
║     IoT Device Dashboard Backend Server      ║
║                                               ║
║  Server running on http://localhost:3000      ║
╚═══════════════════════════════════════════════╝
```

### Step 5: Open Dashboard
- Open browser: `http://localhost:3000`
- Or: Double-click `dashboard.html`

## 🔌 Connect Your MQTT Broker

1. In the dashboard, fill in:
   - **MQTT Endpoint**: `ws://your-broker.com:8883`
   - **GPS Topic**: `devices/gps` (or your topic)
   - **RFID Topic**: `devices/rfid` (or your topic)

2. Click **"Connect"**

3. Start publishing MQTT packets from your IoT devices

## 📝 Publishing Test Data

### Using mosquitto_pub (Linux/Mac)

**Publish GPS data:**
```bash
mosquitto_pub -h your-broker.com -p 1883 \
  -t "devices/gps" \
  -m '{"dID":"device_001","dTS":1701266400,"lat":12.9352,"lon":77.6245}'
```

**Publish RFID data:**
```bash
mosquitto_pub -h your-broker.com -p 1883 \
  -t "devices/rfid" \
  -m '{"dID":"device_001","uID":"tag_001","msg":"Package A","lat":12.9352,"lon":77.6245,"dTS":1701266400}'
```

### Using Python

```python
import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect("your-broker.com", 1883, 60)

# Publish GPS
gps_data = {
    "dID": "device_001",
    "dTS": int(time.time()),
    "lat": 12.9352,
    "lon": 77.6245
}
client.publish("devices/gps", json.dumps(gps_data))

# Publish RFID
rfid_data = {
    "dID": "device_001",
    "uID": "tag_001",
    "msg": "Package A",
    "lat": 12.9352,
    "lon": 77.6245,
    "dTS": int(time.time())
}
client.publish("devices/rfid", json.dumps(rfid_data))

client.disconnect()
```

### Using Arduino/ESP32

```cpp
#include <ArduinoJson.h>
#include <PubSubClient.h>

// Publish GPS
StaticJsonDocument<256> doc;
doc["dID"] = "device_001";
doc["dTS"] = (long)time(nullptr);
doc["lat"] = 12.9352;
doc["lon"] = 77.6245;

char buffer[256];
serializeJson(doc, buffer);
client.publish("devices/gps", buffer);
```

## 📊 Dashboard Layout

```
┌─────────────────────────────────────────────────┐
│  Config Panel (MQTT endpoint, topics)           │
├─────────────────────────┬───────────────────────┤
│                         │                       │
│   Interactive Map       │   RFID Scan Table     │
│   (GPS Locations)       │   (Recent Tags)       │
│                         │                       │
│   - Device Markers      │   - Device ID         │
│   - Click for Details   │   - Tag UID           │
│   - Auto-fit View       │   - Message           │
│                         │   - Location          │
│                         │   - Timestamp         │
│                         │                       │
├─────────────────────────┴───────────────────────┤
│  Stats: Active Devices | Total Scans | Last Update │
└─────────────────────────────────────────────────┘
```

## 🚀 API Endpoints

Access these from any application:

**Get all devices:**
```
GET http://localhost:3000/api/devices
```

**Get RFID scans:**
```
GET http://localhost:3000/api/rfid-scans
```

**Get statistics:**
```
GET http://localhost:3000/api/stats
```

## 🌐 Test MQTT Brokers

Free public brokers for testing:

1. **test.mosquitto.org**
   ```
   Host: test.mosquitto.org
   Port: 1883 (MQTT) or 8081 (WebSocket)
   URL: ws://test.mosquitto.org:8081
   ```

2. **broker.emqx.io**
   ```
   Host: broker.emqx.io
   Port: 1883 (MQTT) or 8083 (WebSocket)
   URL: ws://broker.emqx.io:8083/mqtt
   ```

3. **mqtt.eclipseprojects.io**
   ```
   Host: mqtt.eclipseprojects.io
   Port: 1883 (MQTT) or 80 (WebSocket)
   URL: ws://mqtt.eclipseprojects.io:80
   ```

## 💡 Common Issues & Solutions

### Issue: "Disconnected" status
**Solution:** Check MQTT endpoint URL and port - most require WebSocket on 8083 or 8081

### Issue: "Failed to connect"
**Solution:** Verify broker supports WebSocket - use `ws://` not `http://`

### Issue: No markers on map
**Solution:** Ensure GPS packets have correct format with dID, lat, lon fields

### Issue: Port 3000 already in use
**Solution:** Use different port
```bash
PORT=3001 npm start
```

### Issue: Dependencies won't install
**Solution:** Clear npm cache and reinstall
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## 🔧 Customization

### Change Map Center
Edit `dashboard.html`, find:
```javascript
state.map = L.map('map').setView([20.5937, 78.9629], 5);
```

Change coordinates (currently set to India center)

### Change Server Port
```bash
PORT=8000 npm start
```

### Modify Marker Colors
Edit CSS variables in `dashboard.html`:
```css
--color-primary: #208090;  /* Marker color */
--color-secondary: #FFB84D; /* Highlight color */
```

## 📱 Remote Access

### Via SSH Tunnel (Local Network)
```bash
ssh -L 3000:localhost:3000 user@remote-machine
# Then access: http://localhost:3000
```

### Deploy to Cloud
1. Use Heroku, Railway, or DigitalOcean
2. Set environment: `PORT` variable
3. Push code to deploy

## 🔐 Production Checklist

Before going live:
- [ ] Use WSS:// (encrypted WebSocket) for MQTT
- [ ] Enable authentication on MQTT broker
- [ ] Add CORS restrictions in server.js
- [ ] Use HTTPS for web server
- [ ] Monitor server logs for errors
- [ ] Set up database for historical data
- [ ] Add rate limiting to API endpoints

## 📞 Quick Reference

| Component | Purpose | Default |
|-----------|---------|---------|
| dashboard.html | Frontend UI | Port 3000 |
| server.js | Backend API | Port 3000 |
| MQTT Connection | Data streaming | WebSocket |
| Max RFID History | Recent scans stored | 100 |
| Map Library | OpenStreetMap | Leaflet.js |
| Real-time Updates | WebSocket | Socket.io |

## 🎯 Next Steps

1. ✅ Start backend server
2. ✅ Open dashboard in browser
3. ✅ Configure MQTT settings
4. ✅ Publish test data
5. ✅ See real-time updates
6. ✅ Deploy to cloud (optional)

---

Questions? Check README.md for detailed documentation
