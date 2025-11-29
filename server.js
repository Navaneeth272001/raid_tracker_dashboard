// ============ IoT Dashboard Backend Server ============
// Node.js + Express + MQTT + WebSocket
// Receives MQTT packets and broadcasts to connected clients via WebSocket

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mqtt = require('mqtt');
const path = require('path');
const cors = require('cors');

// ============ CONFIGURATION ============
const PORT = process.env.PORT || 3000;
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// ============ MIDDLEWARE ============
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ============ STATE MANAGEMENT ============
const state = {
    devices: new Map(),
    rfidScans: [],
    mqttConnections: new Map(),
    maxRFIDHistory: 100
};

// ============ REST API ENDPOINTS ============

/**
 * GET /api/devices
 * Returns list of all active devices with their last known location
 */
app.get('/api/devices', (req, res) => {
    const devices = Array.from(state.devices.values()).map(device => ({
        deviceId: device.deviceId,
        latitude: device.latitude,
        longitude: device.longitude,
        timestamp: device.timestamp,
        lastUpdate: device.lastUpdate
    }));

    res.json({
        success: true,
        count: devices.length,
        devices: devices
    });
});

/**
 * GET /api/rfid-scans
 * Returns list of recent RFID scans (last 100)
 */
app.get('/api/rfid-scans', (req, res) => {
    res.json({
        success: true,
        count: state.rfidScans.length,
        scans: state.rfidScans
    });
});

/**
 * GET /api/stats
 * Returns dashboard statistics
 */
app.get('/api/stats', (req, res) => {
    res.json({
        success: true,
        activeDevices: state.devices.size,
        totalScans: state.rfidScans.length,
        mqttConnections: state.mqttConnections.size,
        timestamp: new Date().toISOString()
    });
});

// ============ WebSocket HANDLERS ============

io.on('connection', (socket) => {
    console.log(`[WebSocket] Client connected: ${socket.id}`);

    // Send initial state to newly connected client
    socket.emit('initial_state', {
        devices: Array.from(state.devices.values()),
        rfidScans: state.rfidScans,
        timestamp: new Date().toISOString()
    });

    // Handle MQTT connection request from client
    socket.on('connect_mqtt', (config) => {
        const { clientId, brokerUrl, gpsTopic, rfidTopic } = config;

        console.log(`[MQTT] Connecting to ${brokerUrl} for client ${clientId}`);

        try {
            const mqttClient = mqtt.connect(brokerUrl, {
                protocolVersion: 4,
                reconnectPeriod: 5000,
                connectTimeout: 10000,
                clientId: `dashboard-${clientId}-${Date.now()}`
            });

            mqttClient.on('connect', () => {
                console.log(`[MQTT] Connected to ${brokerUrl}`);
                mqttClient.subscribe([gpsTopic, rfidTopic], (err) => {
                    if (err) {
                        console.error(`[MQTT] Subscribe error: ${err.message}`);
                    } else {
                        console.log(`[MQTT] Subscribed to topics: ${gpsTopic}, ${rfidTopic}`);
                        socket.emit('mqtt_connected', { success: true });
                        io.emit('mqtt_status', { status: 'connected' });
                    }
                });
            });

            mqttClient.on('message', (topic, message) => {
                try {
                    const payload = JSON.parse(message.toString());
                    console.log(`[MQTT] Message on ${topic}:`, payload);

                    if (topic === gpsTopic) {
                        handleGPSMessage(payload, socket);
                    } else if (topic === rfidTopic) {
                        handleRFIDMessage(payload, socket);
                    }
                } catch (error) {
                    console.error(`[MQTT] Error parsing message: ${error.message}`);
                }
            });

            mqttClient.on('error', (error) => {
                console.error(`[MQTT] Error: ${error.message}`);
                socket.emit('mqtt_error', { error: error.message });
                io.emit('mqtt_status', { status: 'error', error: error.message });
            });

            mqttClient.on('offline', () => {
                console.log(`[MQTT] Offline`);
                io.emit('mqtt_status', { status: 'offline' });
            });

            mqttClient.on('close', () => {
                console.log(`[MQTT] Connection closed`);
                state.mqttConnections.delete(clientId);
            });

            // Store connection
            state.mqttConnections.set(clientId, {
                client: mqttClient,
                brokerUrl,
                gpsTopic,
                rfidTopic,
                connectedAt: new Date()
            });

        } catch (error) {
            console.error(`[MQTT] Connection error: ${error.message}`);
            socket.emit('mqtt_error', { error: error.message });
        }
    });

    // Handle disconnection
    socket.on('disconnect', () => {
        console.log(`[WebSocket] Client disconnected: ${socket.id}`);
    });
});

// ============ MESSAGE HANDLERS ============

/**
 * Handle incoming GPS data
 * Expected payload: { dID, dTS, lat, lon, ... }
 */
function handleGPSMessage(payload, socket) {
    const { dID, dTS, lat, lon } = payload;

    // Validate required fields
    if (!dID || lat === undefined || lon === undefined) {
        console.warn(`[GPS] Invalid payload - missing required fields:`, payload);
        return;
    }

    // Update device info
    const device = state.devices.get(dID) || {};
    device.deviceId = dID;
    device.latitude = lat;
    device.longitude = lon;
    device.timestamp = dTS;
    device.lastUpdate = new Date(dTS * 1000).toISOString();
    device.raw = payload;

    state.devices.set(dID, device);

    // Broadcast to all connected WebSocket clients
    io.emit('gps_update', {
        deviceId: dID,
        latitude: lat,
        longitude: lon,
        timestamp: dTS,
        lastUpdate: device.lastUpdate,
        rawPayload: payload
    });

    console.log(`[GPS] Device ${dID} at (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
}

/**
 * Handle incoming RFID scan data
 * Expected payload: { dID, uID, msg, lat, lon, dTS, ... }
 */
function handleRFIDMessage(payload, socket) {
    const { dID, uID, msg, lat, lon, dTS } = payload;

    // Validate required fields
    if (!dID || !uID || lat === undefined || lon === undefined) {
        console.warn(`[RFID] Invalid payload - missing required fields:`, payload);
        return;
    }

    const scanData = {
        deviceId: dID,
        tagUID: uID,
        message: msg || 'N/A',
        latitude: lat,
        longitude: lon,
        timestamp: dTS,
        scannedAt: new Date(dTS * 1000).toISOString(),
        rawPayload: payload
    };

    // Add to scan history (keep last 100)
    state.rfidScans.unshift(scanData);
    if (state.rfidScans.length > state.maxRFIDHistory) {
        state.rfidScans.pop();
    }

    // Broadcast to all connected WebSocket clients
    io.emit('rfid_scan', scanData);

    console.log(`[RFID] Device ${dID} scanned tag ${uID} at (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
}

// ============ ERROR HANDLING ============

process.on('unhandledRejection', (reason, promise) => {
    console.error('[Error] Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('[Error] Uncaught Exception:', error);
    process.exit(1);
});

// ============ SERVER STARTUP ============

server.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════╗
║     IoT Device Dashboard Backend Server      ║
║                                               ║
║  Server running on http://localhost:${PORT}      ║
║                                               ║
║  REST API:                                    ║
║  - GET /api/devices   - Active devices       ║
║  - GET /api/rfid-scans - Recent RFID scans   ║
║  - GET /api/stats     - Dashboard stats      ║
║                                               ║
║  WebSocket: ws://localhost:${PORT}            ║
╚═══════════════════════════════════════════════╝
    `);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully...');
    
    // Close all MQTT connections
    state.mqttConnections.forEach((conn) => {
        conn.client.end();
    });
    
    // Close server
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});
