# IoT Device Dashboard - GPS & RFID Real-time Tracking

A full-stack real-time dashboard for tracking IoT devices via GPS coordinates and RFID tag scans. Built with Node.js backend, Express, Socket.io, MQTT, and interactive web frontend using Leaflet.js maps.

## 📋 Features

- **Real-time GPS Tracking**: Visualize device locations on an interactive OpenStreetMap
- **RFID Scan Logging**: View all RFID tag scans in a sortable table with location and timestamp
- **Live Map Updates**: Device markers update in real-time as GPS packets arrive
- **Configurable MQTT**: Connect to any MQTT broker by specifying endpoint and topics
- **Connection Management**: Easy connect/disconnect functionality
- **Dashboard Statistics**: Live device count, total scans, and last update time
- **Responsive Design**: Works on desktop and tablet
- **REST API**: Query devices and RFID scans via HTTP endpoints

## 🚀 Quick Start

### Prerequisites

- Node.js >= 14.0.0
- npm >= 6.0.0
- Access to an MQTT broker (can be local or cloud-based)

### Installation

1. **Extract the project files** to your working directory

2. **Install dependencies**:
```bash
npm install
```

3. **Start the backend server**:
```bash
npm start
```

The server will start on `http://localhost:3000`

You'll see:
```
╔═══════════════════════════════════════════════╗
║     IoT Device Dashboard Backend Server      ║
║                                               ║
║  Server running on http://localhost:3000      ║
║                                               ║
║  REST API:                                    ║
║  - GET /api/devices   - Active devices       ║
║  - GET /api/rfid-scans - Recent RFID scans   ║
║  - GET /api/stats     - Dashboard stats      ║
║                                               ║
║  WebSocket: ws://localhost:3000              ║
╚═══════════════════════════════════════════════╝
```

4. **Access the dashboard**:
- Open browser to `http://localhost:3000`
- Or open `dashboard.html` directly in a browser

### Configuration

1. **MQTT Endpoint**: Enter your MQTT broker URL
   - Example: `ws://localhost:8081` (local)
   - Example: `ws://broker.example.com:8883` (cloud)
   - Most public brokers support WebSocket on port 8883 or 9001

2. **GPS Topic**: Topic where GPS data is published
   - Default: `devices/gps`
   - Your device publishes GPS data here

3. **RFID Topic**: Topic where RFID scans are published
   - Default: `devices/rfid`
   - Your device publishes RFID data here

4. **Click "Connect"** to establish connection

## 📊 Data Packet Format

### GPS Packet (Published on GPS Topic)

```json
{
  "dID": "device_001",
  "dTS": 1701266400,
  "lat": 12.9352,
  "lon": 77.6245
}
```

**Fields:**
- `dID` (string): Unique device identifier
- `dTS` (integer): Unix timestamp in seconds
- `lat` (float): Latitude coordinate
- `lon` (float): Longitude coordinate

### RFID Packet (Published on RFID Topic)

```json
{
  "dID": "device_001",
  "uID": "tag_12345",
  "msg": "Package Information",
  "lat": 12.9352,
  "lon": 77.6245,
  "dTS": 1701266400
}
```

**Fields:**
- `dID` (string): Unique device identifier
- `uID` (string): RFID tag unique ID
- `msg` (string): Message/data stored in tag
- `lat` (float): Scan location latitude
- `lon` (float): Scan location longitude
- `dTS` (integer): Unix timestamp in seconds

## 🔌 REST API Endpoints

### Get All Devices
```
GET /api/devices
```

Response:
```json
{
  "success": true,
  "count": 2,
  "devices": [
    {
      "deviceId": "device_001",
      "latitude": 12.9352,
      "longitude": 77.6245,
      "timestamp": 1701266400,
      "lastUpdate": "2024-11-29T10:30:00.000Z"
    }
  ]
}
```

### Get Recent RFID Scans
```
GET /api/rfid-scans
```

Response:
```json
{
  "success": true,
  "count": 5,
  "scans": [
    {
      "deviceId": "device_001",
      "tagUID": "tag_12345",
      "message": "Package A",
      "latitude": 12.9352,
      "longitude": 77.6245,
      "timestamp": 1701266400,
      "scannedAt": "2024-11-29T10:30:00.000Z"
    }
  ]
}
```

### Get Dashboard Stats
```
GET /api/stats
```

Response:
```json
{
  "success": true,
  "activeDevices": 2,
  "totalScans": 42,
  "mqttConnections": 1,
  "timestamp": "2024-11-29T10:30:15.000Z"
}
```

## 🧪 Testing with Public MQTT Broker

To test without your own broker:

1. Use public MQTT broker: `wss://test.mosquitto.org:8081`
2. Publish test data using MQTT client:

```bash
# Install mosquitto-clients (Ubuntu/Debian)
sudo apt-get install mosquitto-clients

# Publish GPS data
mosquitto_pub -h test.mosquitto.org -p 1883 \
  -t "devices/gps" \
  -m '{"dID":"device_001","dTS":1701266400,"lat":12.9352,"lon":77.6245}'

# Publish RFID data
mosquitto_pub -h test.mosquitto.org -p 1883 \
  -t "devices/rfid" \
  -m '{"dID":"device_001","uID":"tag_001","msg":"Test Tag","lat":12.9352,"lon":77.6245,"dTS":1701266400}'
```

## 🏗️ Architecture

### Frontend (dashboard.html)
- **Map**: Leaflet.js with OpenStreetMap
- **MQTT**: mqtt.js library for broker communication
- **Real-time**: Direct MQTT connection (WebSocket)
- **UI**: Responsive HTML5 + CSS3 with custom design system

### Backend (server.js)
- **Framework**: Express.js
- **Real-time**: Socket.io for WebSocket communication
- **MQTT**: mqtt.js package for broker integration
- **Data Storage**: In-memory Maps (devices, RFID scans)
- **API**: RESTful endpoints for data retrieval

### Communication Flow

```
IoT Devices
    ↓
MQTT Broker
    ↓
Dashboard (HTML)
    ├─ Direct MQTT-WebSocket connection
    └─ Displays GPS on map & RFID in table
```

## 📁 Project Structure

```
iot-device-dashboard/
├── dashboard.html          # Frontend (single HTML file)
├── server.js               # Backend server
├── package.json            # Node.js dependencies
└── README.md              # This file
```

## 🔧 Development

For development with auto-reload:

```bash
npm install --save-dev nodemon
npm run dev
```

## 🌍 Deploying to Cloud

### Deploy Backend to Heroku

1. Create Heroku app:
```bash
heroku create your-iot-dashboard
```

2. Set environment variables:
```bash
heroku config:set MQTT_BROKER=your-broker-url
```

3. Deploy:
```bash
git push heroku main
```

4. Open dashboard:
```bash
heroku open
```

### Deploy Frontend

- Upload `dashboard.html` to any static hosting (GitHub Pages, Vercel, Netlify, etc.)
- Update MQTT endpoint in HTML to point to your backend/broker

## 🐛 Troubleshooting

### Dashboard shows "Disconnected"
- Verify MQTT broker URL is correct
- Check if broker supports WebSocket (usually port 8883 or 9001)
- Ensure broker allows anonymous connections (if required)

### No GPS markers appear
- Verify GPS packets are being published to correct topic
- Check browser console (F12) for errors
- Ensure packet format matches specification

### RFID table empty
- Verify RFID packets are being published to correct topic
- Check packet format has all required fields
- Monitor server logs for parsing errors

### Port 3000 already in use
```bash
# Change port
PORT=3001 npm start

# Or kill existing process
lsof -ti :3000 | xargs kill -9
```

## 📝 Environment Variables

Set these in your shell or `.env` file:

```bash
PORT=3000                    # Server port (default: 3000)
NODE_ENV=production         # Environment mode
```

## 🔐 Security Notes

- **WebSocket vs WSS**: Use `wss://` for encrypted connections in production
- **Authentication**: For private MQTT brokers, add username/password to connection settings
- **CORS**: Currently allows all origins - restrict in production via CORS configuration
- **Validation**: All incoming packets are validated for required fields

## 📞 Support & Documentation

### MQTT Resources
- [MQTT.js Documentation](https://github.com/mqttjs/MQTT.js)
- [Mosquitto MQTT Broker](https://mosquitto.org/)
- [MQTT Protocol Guide](http://mqtt.org/)

### Map Library
- [Leaflet.js Documentation](https://leafletjs.com/)
- [OpenStreetMap](https://www.openstreetmap.org/)

### Framework Documentation
- [Express.js](https://expressjs.com/)
- [Socket.io](https://socket.io/)
- [Node.js](https://nodejs.org/)

## 📄 License

MIT License - Feel free to use for personal and commercial projects

## ✨ Features Coming Soon

- User authentication
- Data export (CSV/JSON)
- Historical location tracking
- Geofence alerts
- Multi-tenant support
- Database persistence
- Mobile app

---

Built with ❤️ for IoT developers
