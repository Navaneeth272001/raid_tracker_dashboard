const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const mqtt = require('mqtt');
const path = require('path');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, { cors: { origin: "*" } });

const PORT = 3000;
const MAX_RFID_HISTORY = 100;

// ============ STATE MANAGEMENT ============
class DashboardState {
  constructor() {
    this.devices = new Map();
    this.rfidScans = [];
    this.mqttClient = null;
    this.mqttConnected = false;
    this.gpsTopic = null;
    this.rfidTopic = null;
  }

  addDevice(deviceId, lat, lon, timestamp) {
    this.devices.set(deviceId, {
      deviceId,
      latitude: lat,
      longitude: lon,
      timestamp,
      lastUpdate: new Date(timestamp * 1000).toLocaleTimeString()
    });
  }

  addRFIDScan(deviceId, tagUid, message, lat, lon, timestamp) {
    const scan = {
      deviceId,
      tagUID: tagUid,
      message,
      latitude: lat,
      longitude: lon,
      timestamp,
      scannedAt: new Date(timestamp * 1000).toLocaleTimeString()
    };
    this.rfidScans.unshift(scan);
    if (this.rfidScans.length > MAX_RFID_HISTORY) {
      this.rfidScans.pop();
    }
    return scan;
  }

  getDevices() {
    return Array.from(this.devices.values());
  }

  getRFIDScans() {
    return this.rfidScans;
  }
}

const state = new DashboardState();

// ============ MQTT HANDLERS ============
function onMqttConnect() {
  console.log('✅ [MQTT] Connected to broker');
  state.mqttConnected = true;
  io.emit('mqtt_status', { status: 'connected', message: 'Connected to MQTT broker' });

  // Subscribe to topics
  if (state.gpsTopic) {
    state.mqttClient.subscribe(state.gpsTopic, { qos: 1 }, (err) => {
      if (err) {
        console.error(`❌ [MQTT] Subscribe error: ${err}`);
      } else {
        console.log(`✅ [MQTT] Subscribed to ${state.gpsTopic}`);
      }
    });
  }
  if (state.rfidTopic) {
    state.mqttClient.subscribe(state.rfidTopic, { qos: 1 }, (err) => {
      if (err) {
        console.error(`❌ [MQTT] Subscribe error: ${err}`);
      } else {
        console.log(`✅ [MQTT] Subscribed to ${state.rfidTopic}`);
      }
    });
  }
}

function onMqttDisconnect() {
  console.log('⚠️  [MQTT] Disconnected from broker');
  state.mqttConnected = false;
  io.emit('mqtt_status', { status: 'disconnected' });
}

function onMqttMessage(topic, message) {
  try {
    const payload = JSON.parse(message.toString());
    console.log(`📨 [MQTT] Message on ${topic}:`, payload);

    if (state.gpsTopic && topic === state.gpsTopic) {
      handleGPSMessage(payload);
    } else if (state.rfidTopic && topic === state.rfidTopic) {
      handleRFIDMessage(payload);
    }
  } catch (error) {
    console.error(`❌ [MQTT] Error processing message: ${error.message}`);
  }
}

function onMqttError(error) {
  console.error(`❌ [MQTT] Error: ${error.message}`);
  io.emit('mqtt_status', { status: 'error', message: error.message });
}

function handleGPSMessage(payload) {
  try {
    const deviceId = payload.dID;
    const lat = payload.lat;
    const lon = payload.lon;
    const timestamp = payload.dTS || Math.floor(Date.now() / 1000);

    if (!deviceId || lat === undefined || lon === undefined) {
      console.warn(`⚠️  [GPS] Invalid payload:`, payload);
      return;
    }

    state.addDevice(deviceId, lat, lon, timestamp);

    io.emit('gps_update', {
      deviceId,
      latitude: lat,
      longitude: lon,
      timestamp,
      lastUpdate: new Date(timestamp * 1000).toLocaleTimeString()
    });

    console.log(`📍 [GPS] ${deviceId} at (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
  } catch (error) {
    console.error(`❌ [GPS] Error: ${error.message}`);
  }
}

function handleRFIDMessage(payload) {
  try {
    const deviceId = payload.dID;
    const tagUid = payload.uID;
    const message = payload.msg || 'N/A';
    const lat = payload.lat;
    const lon = payload.lon;
    const timestamp = payload.dTS || Math.floor(Date.now() / 1000);

    if (!deviceId || !tagUid || lat === undefined || lon === undefined) {
      console.warn(`⚠️  [RFID] Invalid payload:`, payload);
      return;
    }

    const scan = state.addRFIDScan(deviceId, tagUid, message, lat, lon, timestamp);

    io.emit('rfid_scan', scan);

    console.log(`📡 [RFID] ${deviceId} scanned ${tagUid} at (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
  } catch (error) {
    console.error(`❌ [RFID] Error: ${error.message}`);
  }
}

// ============ MQTT CONNECTION MANAGER ============
function connectMQTT(brokerUrl, gpsTopic, rfidTopic, username = null, password = null) {
  try {
    console.log(`[MQTT] Connecting to ${brokerUrl}...`);

    // Parse broker URL
    let protocol = 'mqtt';
    let hostPort = brokerUrl;

    if (brokerUrl.includes('://')) {
      const parts = brokerUrl.split('://');
      protocol = parts[0];
      hostPort = parts[1];
    }

    let host, port;
    const lastColonIndex = hostPort.lastIndexOf(':');
    if (lastColonIndex > -1) {
      host = hostPort.substring(0, lastColonIndex);
      port = parseInt(hostPort.substring(lastColonIndex + 1));
    } else {
      host = hostPort;
      port = protocol.includes('mqtts') || protocol.includes('wss') ? 8883 : 1883;
    }

    console.log(`[MQTT] Host: ${host}, Port: ${port}, Protocol: ${protocol}`);

    // MQTT connection options
    const options = {
      clientId: `dashboard_${Date.now()}`,
      clean: true,
      reconnectPeriod: 5000,
      connectTimeout: 15000,
      keepaliveInterval: 60,
      protocolVersion: 4
    };

    // Add authentication
    if (username && password) {
      options.username = username;
      options.password = password;
      console.log(`[MQTT] Using authentication: ${username}`);
    }

    // Add TLS options for secure connections
    if (protocol.includes('mqtts') || protocol.includes('wss')) {
      console.log(`[MQTT] Using TLS/SSL`);
      options.rejectUnauthorized = false; // For self-signed certs
    }

    // Create MQTT client
    state.mqttClient = mqtt.connect(`${protocol}://${host}:${port}`, options);

    // Set up event handlers
    state.mqttClient.on('connect', onMqttConnect);
    state.mqttClient.on('disconnect', onMqttDisconnect);
    state.mqttClient.on('message', onMqttMessage);
    state.mqttClient.on('error', onMqttError);

    // Store topics for subscription
    state.gpsTopic = gpsTopic;
    state.rfidTopic = rfidTopic;

    return true;
  } catch (error) {
    console.error(`❌ [MQTT] Connection error: ${error.message}`);
    io.emit('mqtt_status', { status: 'error', message: error.message });
    return false;
  }
}

function disconnectMQTT() {
  if (state.mqttClient) {
    state.mqttClient.end();
    state.mqttClient = null;
    console.log('✅ [MQTT] Disconnected');
  }
}

// ============ ROUTES ============
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/api/devices', (req, res) => {
  res.json({
    devices: state.getDevices(),
    count: state.devices.size
  });
});

app.get('/api/rfid-scans', (req, res) => {
  res.json({
    scans: state.getRFIDScans(),
    count: state.rfidScans.length
  });
});

// ============ WEBSOCKET HANDLERS ============
io.on('connection', (socket) => {
  console.log(`✅ [WebSocket] Client connected: ${socket.id}`);

  // Send initial state
  socket.emit('initial_state', {
    devices: state.getDevices(),
    rfidScans: state.getRFIDScans(),
    connected: state.mqttConnected
  });

  // Handle MQTT connection request
  socket.on('connect_mqtt', (data) => {
    const { broker, gpsTopic, rfidTopic, username, password } = data;
    console.log(`[WebSocket] Connect MQTT requested: ${broker}`);

    // Disconnect existing connection
    if (state.mqttClient && state.mqttConnected) {
      disconnectMQTT();
    }

    // Connect to new broker
    if (connectMQTT(broker, gpsTopic, rfidTopic, username, password)) {
      console.log('✅ [WebSocket] MQTT connection initiated');
    }
  });

  // Handle MQTT disconnection request
  socket.on('disconnect_mqtt', () => {
    console.log('[WebSocket] Disconnect MQTT requested');
    disconnectMQTT();
    io.emit('mqtt_status', { status: 'disconnected' });
  });

  socket.on('disconnect', () => {
    console.log(`✅ [WebSocket] Client disconnected: ${socket.id}`);
  });
});

// ============ START SERVER ============
httpServer.listen(PORT, () => {
  console.log(`
╔═════════════════════════════════════════════╗
║   IoT Device Dashboard - Node.js Backend    ║
║                                             ║
║   Express + Socket.IO + MQTT                ║
║                                             ║
║   Server: http://localhost:${PORT}             ║
╚═════════════════════════════════════════════╝
  `);
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
