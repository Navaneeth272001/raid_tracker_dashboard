#!/usr/bin/env python3
"""
IoT Device Dashboard - Python Backend
Flask + MQTT + WebSocket
Listens to MQTT broker and broadcasts to connected browsers
"""

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import paho.mqtt.client as mqtt
import json
import threading
import time
from collections import deque

# ============ CONFIGURATION ============
PORT = 3000
MAX_RFID_HISTORY = 100

# ============ FLASK APP ============
app = Flask(__name__)
app.config['SECRET_KEY'] = 'iot-dashboard-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============ STATE MANAGEMENT ============
class DashboardState:
    def __init__(self):
        self.devices = {}  # device_id -> {lat, lon, timestamp, lastUpdate}
        self.rfid_scans = deque(maxlen=MAX_RFID_HISTORY)
        self.mqtt_client = None
        self.mqtt_connected = False
        self.lock = threading.Lock()
    
    def add_device(self, device_id, lat, lon, timestamp):
        with self.lock:
            self.devices[device_id] = {
                'deviceId': device_id,
                'latitude': lat,
                'longitude': lon,
                'timestamp': timestamp,
                'lastUpdate': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            }
    
    def add_rfid_scan(self, device_id, tag_uid, message, lat, lon, timestamp):
        with self.lock:
            scan = {
                'deviceId': device_id,
                'tagUID': tag_uid,
                'message': message,
                'latitude': lat,
                'longitude': lon,
                'timestamp': timestamp,
                'scannedAt': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            }
            self.rfid_scans.appendleft(scan)
            return scan
    
    def get_devices(self):
        with self.lock:
            return list(self.devices.values())
    
    def get_rfid_scans(self):
        with self.lock:
            return list(self.rfid_scans)

state = DashboardState()

# ============ MQTT HANDLERS ============
def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ [MQTT] Connected to broker")
        state.mqtt_connected = True
        socketio.emit('mqtt_status', {'status': 'connected'}, broadcast=True)
    else:
        print(f"❌ [MQTT] Connection failed: {rc}")
        state.mqtt_connected = False
        socketio.emit('mqtt_status', {'status': 'error', 'error': f'Connection code {rc}'}, broadcast=True)

def on_mqtt_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️  [MQTT] Unexpected disconnection: {rc}")
    state.mqtt_connected = False
    socketio.emit('mqtt_status', {'status': 'disconnected'}, broadcast=True)

def on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        # Get topic info from userdata
        gps_topic = userdata.get('gps_topic', 'devices/gps')
        rfid_topic = userdata.get('rfid_topic', 'devices/rfid')
        
        if topic == gps_topic:
            handle_gps_message(payload)
        elif topic == rfid_topic:
            handle_rfid_message(payload)
    except Exception as e:
        print(f"❌ [MQTT] Error processing message: {e}")

def handle_gps_message(payload):
    try:
        device_id = payload.get('dID')
        timestamp = payload.get('dTS', int(time.time()))
        lat = payload.get('lat')
        lon = payload.get('lon')
        
        if not device_id or lat is None or lon is None:
            print(f"⚠️  [GPS] Invalid payload: {payload}")
            return
        
        state.add_device(device_id, lat, lon, timestamp)
        
        # Broadcast to all connected clients
        socketio.emit('gps_update', {
            'deviceId': device_id,
            'latitude': lat,
            'longitude': lon,
            'timestamp': timestamp,
            'lastUpdate': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        }, broadcast=True)
        
        print(f"📍 [GPS] {device_id} at ({lat:.4f}, {lon:.4f})")
    except Exception as e:
        print(f"❌ [GPS] Error: {e}")

def handle_rfid_message(payload):
    try:
        device_id = payload.get('dID')
        tag_uid = payload.get('uID')
        message = payload.get('msg', 'N/A')
        lat = payload.get('lat')
        lon = payload.get('lon')
        timestamp = payload.get('dTS', int(time.time()))
        
        if not device_id or not tag_uid or lat is None or lon is None:
            print(f"⚠️  [RFID] Invalid payload: {payload}")
            return
        
        scan = state.add_rfid_scan(device_id, tag_uid, message, lat, lon, timestamp)
        
        # Broadcast to all connected clients
        socketio.emit('rfid_scan', scan, broadcast=True)
        
        print(f"📡 [RFID] {device_id} scanned {tag_uid} at ({lat:.4f}, {lon:.4f})")
    except Exception as e:
        print(f"❌ [RFID] Error: {e}")

# ============ MQTT CONNECTION MANAGER ============
def connect_mqtt(broker_url, gps_topic, rfid_topic, username=None, password=None):
    """Connect to MQTT broker"""
    try:
        print(f"[MQTT] Connecting to {broker_url}...")
        
        # Parse broker URL
        if '://' in broker_url:
            protocol, broker_url = broker_url.split('://', 1)
        
        if ':' in broker_url:
            host, port = broker_url.rsplit(':', 1)
            port = int(port)
        else:
            host = broker_url
            port = 1883
        
        print(f"[MQTT] Host: {host}, Port: {port}")
        
        # Create MQTT client
        state.mqtt_client = mqtt.Client(client_id=f"dashboard_{int(time.time())}")
        state.mqtt_client.on_connect = on_mqtt_connect
        state.mqtt_client.on_disconnect = on_mqtt_disconnect
        state.mqtt_client.on_message = on_mqtt_message
        
        # Store topic info in userdata
        state.mqtt_client.user_data_set({
            'gps_topic': gps_topic,
            'rfid_topic': rfid_topic
        })
        
        # Set authentication if provided
        if username and password:
            print(f"[MQTT] Using authentication: {username}")
            state.mqtt_client.username_pw_set(username, password)
        
        # Connect
        state.mqtt_client.connect(host, port, keepalive=60)
        
        # Subscribe to topics
        state.mqtt_client.subscribe([(gps_topic, 1), (rfid_topic, 1)])
        print(f"[MQTT] Subscribed to: {gps_topic}, {rfid_topic}")
        
        # Start background loop
        state.mqtt_client.loop_start()
        
        return True
    except Exception as e:
        print(f"❌ [MQTT] Connection error: {e}")
        return False

def disconnect_mqtt():
    """Disconnect from MQTT broker"""
    if state.mqtt_client:
        state.mqtt_client.loop_stop()
        state.mqtt_client.disconnect()
        print("✅ [MQTT] Disconnected")

# ============ FLASK ROUTES ============

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoT Device Dashboard - GPS & RFID Tracking</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-primary: #208090;
            --color-primary-hover: #1a6673;
            --color-success: #2bb875;
            --color-error: #dc3545;
            --color-bg: #fafaf8;
            --color-surface: #ffffff;
            --color-text: #133b3b;
            --color-text-secondary: #666666;
            --color-border: #e0e0e0;
            --space-4: 4px;
            --space-8: 8px;
            --space-12: 12px;
            --space-16: 16px;
            --radius-base: 8px;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
        }

        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            background: var(--color-surface);
            border-bottom: 1px solid var(--color-border);
            padding: var(--space-16);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            max-height: 200px;
            overflow-y: auto;
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: var(--space-12);
            color: var(--color-primary);
        }

        .config-panel {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: var(--space-12);
            align-items: end;
        }

        .config-group {
            display: flex;
            flex-direction: column;
        }

        .config-group label {
            font-size: 11px;
            font-weight: 600;
            margin-bottom: var(--space-4);
            text-transform: uppercase;
            color: var(--color-text-secondary);
        }

        .config-group input {
            padding: var(--space-8) var(--space-12);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-base);
            font-size: 13px;
            background: var(--color-surface);
            color: var(--color-text);
        }

        .config-group input:focus {
            outline: none;
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(32, 128, 144, 0.1);
        }

        .status-group {
            display: flex;
            gap: var(--space-8);
            align-items: center;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #999;
            animation: pulse 2s infinite;
        }

        .status-indicator.connected {
            background: var(--color-success);
            animation: pulse-green 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes pulse-green {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px var(--color-success); }
            50% { opacity: 0.8; }
        }

        .status-text {
            font-size: 12px;
            color: var(--color-text-secondary);
        }

        .status-text.connected {
            color: var(--color-success);
            font-weight: 600;
        }

        .btn {
            padding: var(--space-8) var(--space-16);
            border: none;
            border-radius: var(--radius-base);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 200ms;
            text-transform: uppercase;
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--color-primary-hover);
        }

        .btn-primary:disabled {
            background: #999;
            cursor: not-allowed;
            opacity: 0.6;
        }

        .btn-disconnect {
            background: var(--color-error);
            color: white;
            display: none;
        }

        .btn-disconnect.show {
            display: block;
        }

        .btn-row {
            display: flex;
            gap: var(--space-8);
        }

        .content {
            display: flex;
            flex: 1;
            gap: var(--space-12);
            padding: var(--space-12);
            overflow: hidden;
        }

        .map-section {
            flex: 0 0 70%;
            background: var(--color-surface);
            border-radius: var(--radius-base);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        #map {
            width: 100%;
            height: 100%;
        }

        .table-section {
            flex: 0 0 30%;
            display: flex;
            flex-direction: column;
            background: var(--color-surface);
            border-radius: var(--radius-base);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .table-header {
            padding: var(--space-16);
            border-bottom: 1px solid var(--color-border);
            background: linear-gradient(135deg, #f0f7f8, #ffffff);
        }

        .table-header h3 {
            font-size: 14px;
            font-weight: 600;
            color: var(--color-primary);
            margin: 0;
        }

        .table-wrapper {
            flex: 1;
            overflow-y: auto;
        }

        .rfid-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }

        .rfid-table thead th {
            position: sticky;
            top: 0;
            background: var(--color-bg);
            padding: var(--space-8) var(--space-12);
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--color-border);
            font-size: 11px;
            text-transform: uppercase;
        }

        .rfid-table tbody tr {
            border-bottom: 1px solid #f0f0f0;
        }

        .rfid-table tbody tr:hover {
            background: rgba(32, 128, 144, 0.05);
        }

        .rfid-table td {
            padding: var(--space-8) var(--space-12);
        }

        .rfid-table .device-id {
            font-weight: 600;
            color: var(--color-primary);
        }

        .rfid-table .tag-uid {
            font-family: monospace;
            background: rgba(32, 128, 144, 0.1);
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 11px;
        }

        .empty-message {
            padding: var(--space-16);
            text-align: center;
            color: var(--color-text-secondary);
            font-style: italic;
        }

        .stats-bar {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--space-12);
            padding: var(--space-12);
            background: rgba(32, 128, 144, 0.05);
            border-top: 1px solid var(--color-border);
        }

        .stat-item {
            text-align: center;
        }

        .stat-value {
            font-size: 20px;
            font-weight: 700;
            color: var(--color-primary);
        }

        .stat-label {
            font-size: 11px;
            color: var(--color-text-secondary);
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 IoT Device Dashboard</h1>
            <div class="config-panel">
                <div class="config-group">
                    <label>MQTT Broker Address</label>
                    <input type="text" id="broker" placeholder="192.168.1.100:1883" value="localhost:1883">
                </div>
                <div class="config-group">
                    <label>GPS Topic</label>
                    <input type="text" id="gpsTopic" placeholder="devices/gps" value="devices/gps">
                </div>
                <div class="config-group">
                    <label>RFID Topic</label>
                    <input type="text" id="rfidTopic" placeholder="devices/rfid" value="devices/rfid">
                </div>
                <div class="config-group">
                    <label>Username (optional)</label>
                    <input type="text" id="username" placeholder="Leave blank">
                </div>
                <div class="config-group">
                    <label>Password (optional)</label>
                    <input type="password" id="password" placeholder="Leave blank">
                </div>
                <div style="grid-column: span 1;"></div>
                <div class="status-group">
                    <div class="status-indicator" id="status"></div>
                    <span class="status-text" id="statusText">Disconnected</span>
                </div>
                <div class="btn-row">
                    <button class="btn btn-primary" onclick="connect()">Connect</button>
                    <button class="btn btn-disconnect" id="disconnectBtn" onclick="disconnect()">Disconnect</button>
                </div>
            </div>
        </div>

        <div class="content">
            <div class="map-section">
                <div id="map"></div>
            </div>

            <div class="table-section">
                <div class="table-header">
                    <h3>📡 RFID Scans</h3>
                </div>
                <div class="table-wrapper">
                    <table class="rfid-table">
                        <thead>
                            <tr>
                                <th>Device</th>
                                <th>Tag UID</th>
                                <th>Message</th>
                                <th>Location</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody id="rfidBody">
                            <tr><td colspan="5" class="empty-message">Waiting for data...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div class="stats-bar">
                    <div class="stat-item">
                        <div class="stat-value" id="deviceCount">0</div>
                        <div class="stat-label">Active Devices</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="scanCount">0</div>
                        <div class="stat-label">Total Scans</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="lastUpdate">--</div>
                        <div class="stat-label">Last Update</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const state = {
            devices: new Map(),
            rfidScans: [],
            markers: new Map(),
            map: null,
            socket: null
        };

        function initMap() {
            state.map = L.map('map').setView([20.5937, 78.9629], 5);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap',
                maxZoom: 19
            }).addTo(state.map);
        }

        function connect() {
            const broker = document.getElementById('broker').value.trim();
            const gpsTopic = document.getElementById('gpsTopic').value.trim();
            const rfidTopic = document.getElementById('rfidTopic').value.trim();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();

            if (!broker || !gpsTopic || !rfidTopic) {
                alert('Fill in all required fields');
                return;
            }

            if (!state.socket) {
                state.socket = io();
                
                state.socket.on('gps_update', handleGPS);
                state.socket.on('rfid_scan', handleRFID);
                state.socket.on('mqtt_status', handleStatus);
                state.socket.on('connect', () => {
                    state.socket.emit('connect_mqtt', {
                        broker: broker,
                        gpsTopic: gpsTopic,
                        rfidTopic: rfidTopic,
                        username: username || null,
                        password: password || null
                    });
                });
            }
        }

        function disconnect() {
            if (state.socket) {
                state.socket.emit('disconnect_mqtt');
                updateStatus('Disconnected', false);
                document.getElementById('disconnectBtn').classList.remove('show');
                document.querySelectorAll('.btn-primary').forEach(b => b.style.display = 'block');
            }
        }

        function handleGPS(data) {
            state.devices.set(data.deviceId, data);
            updateMarker(data.deviceId, data.latitude, data.longitude);
            updateStats();
        }

        function handleRFID(data) {
            state.rfidScans.unshift(data);
            if (state.rfidScans.length > 100) state.rfidScans.pop();
            updateRFIDTable();
            updateStats();
        }

        function handleStatus(data) {
            if (data.status === 'connected') {
                updateStatus('Connected', true);
                document.getElementById('disconnectBtn').classList.add('show');
                document.querySelectorAll('.btn-primary').forEach(b => b.style.display = 'none');
            } else {
                updateStatus(data.status, false);
            }
        }

        function updateMarker(deviceId, lat, lon) {
            if (state.markers.has(deviceId)) {
                state.markers.get(deviceId).setLatLng([lat, lon]);
            } else {
                const marker = L.marker([lat, lon]).addTo(state.map)
                    .bindPopup(`<b>${deviceId}</b><br>Lat: ${lat.toFixed(6)}<br>Lon: ${lon.toFixed(6)}`);
                state.markers.set(deviceId, marker);
                fitBounds();
            }
        }

        function fitBounds() {
            if (state.markers.size === 0) return;
            const group = L.featureGroup([...state.markers.values()]);
            state.map.fitBounds(group.getBounds().pad(0.1), { maxZoom: 15 });
        }

        function updateRFIDTable() {
            const tbody = document.getElementById('rfidBody');
            if (state.rfidScans.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-message">Waiting for data...</td></tr>';
                return;
            }
            tbody.innerHTML = state.rfidScans.slice(0, 50).map(s => `
                <tr>
                    <td class="device-id">${s.deviceId}</td>
                    <td class="tag-uid">${s.tagUID}</td>
                    <td>${s.message}</td>
                    <td>${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}</td>
                    <td>${new Date(s.scannedAt).toLocaleTimeString()}</td>
                </tr>
            `).join('');
        }

        function updateStats() {
            document.getElementById('deviceCount').textContent = state.devices.size;
            document.getElementById('scanCount').textContent = state.rfidScans.length;
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        }

        function updateStatus(text, connected) {
            const indicator = document.getElementById('status');
            const statusText = document.getElementById('statusText');
            statusText.textContent = text;
            if (connected) {
                indicator.classList.add('connected');
                statusText.classList.add('connected');
            } else {
                indicator.classList.remove('connected');
                statusText.classList.remove('connected');
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            initMap();
            updateStats();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/devices')
def api_devices():
    return {'devices': state.get_devices(), 'count': len(state.devices)}

@app.route('/api/rfid-scans')
def api_rfid():
    return {'scans': state.get_rfid_scans(), 'count': len(state.rfid_scans)}

@app.route('/api/stats')
def api_stats():
    return {
        'activeDevices': len(state.devices),
        'totalScans': len(state.rfid_scans),
        'connected': state.mqtt_connected
    }

# ============ WEBSOCKET HANDLERS ============

@socketio.on('connect')
def handle_connect():
    print(f"✅ [WebSocket] Client connected")
    emit('initial_state', {
        'devices': state.get_devices(),
        'rfidScans': state.get_rfid_scans(),
        'connected': state.mqtt_connected
    })

@socketio.on('connect_mqtt')
def handle_connect_mqtt(data):
    broker = data.get('broker')
    gps_topic = data.get('gpsTopic')
    rfid_topic = data.get('rfidTopic')
    username = data.get('username')
    password = data.get('password')
    
    print(f"[WebSocket] Connect MQTT requested: {broker}")
    
    # Disconnect existing connection
    if state.mqtt_client and state.mqtt_connected:
        disconnect_mqtt()
    
    # Connect to new broker
    if connect_mqtt(broker, gps_topic, rfid_topic, username, password):
        print("✅ [WebSocket] MQTT connection initiated")
    else:
        emit('mqtt_error', {'error': 'Failed to connect to broker'})

@socketio.on('disconnect_mqtt')
def handle_disconnect_mqtt():
    print("[WebSocket] Disconnect MQTT requested")
    disconnect_mqtt()
    state.mqtt_connected = False
    emit('mqtt_status', {'status': 'disconnected'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"✅ [WebSocket] Client disconnected")

# ============ MAIN ============

if __name__ == '__main__':
    print("""
╔═════════════════════════════════════════════╗
║   IoT Device Dashboard - Python Backend     ║
║                                             ║
║   Flask + MQTT + WebSocket                  ║
║                                             ║
║   Server: http://localhost:3000             ║
╚═════════════════════════════════════════════╝
    """)
    
    print(f"Starting server on port {PORT}...")
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)
