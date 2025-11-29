# IoT Device Dashboard - MQTT Packet Reference & Testing Guide

## 📡 MQTT Packet Specifications

### 1. GPS Data Packet

**Topic**: `devices/gps` (or your custom topic)

**Packet Format (JSON)**:
```json
{
  "dID": "device_001",
  "dTS": 1701266400,
  "lat": 12.9352,
  "lon": 77.6245
}
```

**Field Descriptions**:
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| dID | String | Yes | Device unique identifier | "device_001" |
| dTS | Integer | Yes | Unix timestamp (seconds) | 1701266400 |
| lat | Float | Yes | Latitude coordinate | 12.9352 |
| lon | Float | Yes | Longitude coordinate | 77.6245 |

**Validation Rules**:
- dID: Non-empty string, alphanumeric + underscore
- dTS: Unix timestamp in seconds (not milliseconds)
- lat: Float between -90 and 90
- lon: Float between -180 and 180

**Update Frequency**: Every 3-10 seconds recommended

### 2. RFID Scan Packet

**Topic**: `devices/rfid` (or your custom topic)

**Packet Format (JSON)**:
```json
{
  "dID": "device_001",
  "uID": "tag_12345",
  "msg": "Package A - Electronics",
  "lat": 12.9352,
  "lon": 77.6245,
  "dTS": 1701266400
}
```

**Field Descriptions**:
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| dID | String | Yes | Device unique identifier | "device_001" |
| uID | String | Yes | RFID tag unique ID | "tag_12345" |
| msg | String | No | Message/data from tag | "Package A" |
| lat | Float | Yes | Scan location latitude | 12.9352 |
| lon | Float | Yes | Scan location longitude | 77.6245 |
| dTS | Integer | Yes | Unix timestamp (seconds) | 1701266400 |

**Validation Rules**:
- dID: Non-empty string, alphanumeric + underscore
- uID: Non-empty string, any characters allowed
- msg: Can be empty or null
- lat/lon: Valid GPS coordinates
- dTS: Unix timestamp in seconds

**Frequency**: As scans occur (event-driven)

---

## 🧪 Testing Guide

### Option 1: Using mosquitto_pub (Command Line)

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install mosquitto-clients

# macOS
brew install mosquitto

# Windows
# Download from: https://mosquitto.org/download/
```

**Test GPS Data - Single Device**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 \
  -t "devices/gps" \
  -m '{"dID":"device_001","dTS":'$(date +%s)',"lat":12.9352,"lon":77.6245}'
```

**Test RFID Data - Single Scan**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 \
  -t "devices/rfid" \
  -m '{"dID":"device_001","uID":"tag_001","msg":"Test Package","lat":12.9352,"lon":77.6245,"dTS":'$(date +%s)'}'
```

**Test Multiple Devices (GPS)**:
```bash
#!/bin/bash
# Publish GPS for 3 devices

# Device 1 - Bangalore
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_001","dTS":'$(date +%s)',"lat":12.9352,"lon":77.6245}'

# Device 2 - Delhi  
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_002","dTS":'$(date +%s)',"lat":28.6139,"lon":77.2090}'

# Device 3 - Mumbai
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_003","dTS":'$(date +%s)',"lat":19.0760,"lon":72.8777}'
```

**Continuous Testing (Publish every 5 seconds)**:
```bash
#!/bin/bash
# Continuous GPS publishing

while true; do
  mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
    -m '{"dID":"device_001","dTS":'$(date +%s)',"lat":12.9352,"lon":77.6245}'
  sleep 5
done
```

---

### Option 2: Using Python (test_mqtt.py)

**Installation**:
```bash
pip3 install paho-mqtt
```

**Run Test Simulator**:
```bash
# Test for 60 seconds
python3 test_mqtt.py -b test.mosquitto.org -p 1883 -d 60

# Continuous mode
python3 test_mqtt.py -b test.mosquitto.org -p 1883 --continuous

# Custom topics
python3 test_mqtt.py -b localhost -p 1883 \
  -g "sensors/gps" -r "sensors/rfid" -d 120
```

**Python Script (Quick Test)**:
```python
import paho.mqtt.client as mqtt
import json
import time

# Connect to broker
client = mqtt.Client()
client.connect("test.mosquitto.org", 1883, 60)
client.loop_start()

# Publish GPS
gps_data = {
    "dID": "device_001",
    "dTS": int(time.time()),
    "lat": 12.9352,
    "lon": 77.6245
}
client.publish("devices/gps", json.dumps(gps_data))
print(f"Published GPS: {gps_data}")

# Publish RFID
rfid_data = {
    "dID": "device_001",
    "uID": "tag_001",
    "msg": "Test Package",
    "lat": 12.9352,
    "lon": 77.6245,
    "dTS": int(time.time())
}
client.publish("devices/rfid", json.dumps(rfid_data))
print(f"Published RFID: {rfid_data}")

time.sleep(1)
client.disconnect()
```

---

### Option 3: Using Node.js

**Installation**:
```bash
npm install mqtt
```

**JavaScript Test**:
```javascript
const mqtt = require('mqtt');

const client = mqtt.connect('mqtt://test.mosquitto.org');

client.on('connect', () => {
  // Publish GPS
  const gps = {
    dID: 'device_001',
    dTS: Math.floor(Date.now() / 1000),
    lat: 12.9352,
    lon: 77.6245
  };
  client.publish('devices/gps', JSON.stringify(gps));
  console.log('GPS published:', gps);

  // Publish RFID
  const rfid = {
    dID: 'device_001',
    uID: 'tag_001',
    msg: 'Test Package',
    lat: 12.9352,
    lon: 77.6245,
    dTS: Math.floor(Date.now() / 1000)
  };
  client.publish('devices/rfid', JSON.stringify(rfid));
  console.log('RFID published:', rfid);

  client.end();
});
```

---

### Option 4: Using Arduino/ESP32

**GPS Publishing (ESP32)**:
```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>

const char* ssid = "your-wifi";
const char* password = "your-password";
const char* mqtt_server = "test.mosquitto.org";

WiFiClient espClient;
PubSubClient client(espClient);
TinyGPSPlus gps;

void publishGPS(const char* deviceId, float lat, float lon) {
  StaticJsonDocument<256> doc;
  doc["dID"] = deviceId;
  doc["dTS"] = (long)time(nullptr);
  doc["lat"] = lat;
  doc["lon"] = lon;

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish("devices/gps", buffer);
}

void publishRFID(const char* deviceId, const char* tagId, 
                 const char* message, float lat, float lon) {
  StaticJsonDocument<512> doc;
  doc["dID"] = deviceId;
  doc["uID"] = tagId;
  doc["msg"] = message;
  doc["lat"] = lat;
  doc["lon"] = lon;
  doc["dTS"] = (long)time(nullptr);

  char buffer[512];
  serializeJson(doc, buffer);
  client.publish("devices/rfid", buffer);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  client.setServer(mqtt_server, 1883);
  while (!client.connected()) client.connect("ESP32");
}

void loop() {
  if (!client.connected()) {
    while (!client.connected()) client.connect("ESP32");
  }
  client.loop();
  
  // Read GPS and publish every 10 seconds
  static unsigned long lastPublish = 0;
  if (millis() - lastPublish > 10000) {
    if (gps.location.isValid()) {
      publishGPS("device_001", gps.location.lat(), gps.location.lng());
    }
    lastPublish = millis();
  }
}
```

---

## 📊 Test Data Examples

### Complete GPS Dataset (4 Devices)

**Device 1 - Bangalore HQ**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_001","dTS":1701266400,"lat":12.9352,"lon":77.6245}'
```

**Device 2 - Delhi Office**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_002","dTS":1701266400,"lat":28.6139,"lon":77.2090}'
```

**Device 3 - Mumbai Hub**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_003","dTS":1701266400,"lat":19.0760,"lon":72.8777}'
```

**Device 4 - Mangalore Port**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_004","dTS":1701266400,"lat":13.3673,"lon":74.7421}'
```

### Complete RFID Dataset (5 Scans)

**Scan 1**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/rfid" \
  -m '{"dID":"device_001","uID":"tag_001","msg":"Package A - Electronics","lat":12.9352,"lon":77.6245,"dTS":1701266400}'
```

**Scan 2**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/rfid" \
  -m '{"dID":"device_002","uID":"tag_002","msg":"Package B - Documents","lat":28.6139,"lon":77.2090,"dTS":1701266401}'
```

**Scan 3**:
```bash
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/rfid" \
  -m '{"dID":"device_003","uID":"tag_003","msg":"Package C - Medical","lat":19.0760,"lon":72.8777,"dTS":1701266402}'
```

---

## 🔍 Debugging & Verification

### Verify MQTT Broker Connectivity

```bash
# Test connection to broker
mosquitto_sub -h test.mosquitto.org -p 1883 -t "devices/#"
```

This will display all messages on topics starting with "devices/"

### Monitor GPS Messages

```bash
mosquitto_sub -h test.mosquitto.org -p 1883 -t "devices/gps" -F "%I %t %p"
```

Format: `timestamp topic payload`

### Monitor RFID Messages

```bash
mosquitto_sub -h test.mosquitto.org -p 1883 -t "devices/rfid" -v
```

### Count Messages in Topic

```bash
#!/bin/bash
count=0
mosquitto_sub -h test.mosquitto.org -p 1883 -t "devices/gps" | while read msg; do
  ((count++))
  echo "Messages: $count"
done
```

---

## ⚠️ Common Testing Issues

### Issue: "Connection refused"
**Solution**: Check broker host, port, and firewall
```bash
# Test connectivity
mosquitto_pub -h test.mosquitto.org -p 1883 -t "test" -m "hello"
```

### Issue: "Invalid JSON"
**Solution**: Ensure JSON is properly formatted
```bash
# Validate JSON
echo '{"dID":"device_001","dTS":1701266400,"lat":12.9352,"lon":77.6245}' | jq .
```

### Issue: "Missing fields"
**Solution**: Verify all required fields present
```bash
# Check packet structure
mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
  -m '{"dID":"device_001","dTS":1701266400,"lat":12.9352,"lon":77.6245}'
```

### Issue: "Device not appearing on map"
**Causes**:
- Packet format incorrect (missing lat/lon)
- Topic name mismatch
- Dashboard not connected to broker
- Map not refreshed

**Solution**: Check browser console and server logs

---

## 📈 Load Testing

**Publish 100 GPS packets/second**:
```bash
#!/bin/bash
for i in {1..100}; do
  mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/gps" \
    -m '{"dID":"device_'$((i % 10))'","dTS":'$(date +%s)',"lat":12.9352,"lon":77.6245}' &
done
wait
```

**Publish 50 RFID scans/second**:
```bash
#!/bin/bash
for i in {1..50}; do
  mosquitto_pub -h test.mosquitto.org -p 1883 -t "devices/rfid" \
    -m '{"dID":"device_001","uID":"tag_'$i'","msg":"Package","lat":12.9352,"lon":77.6245,"dTS":'$(date +%s)'}' &
done
wait
```

---

## 🌐 Public MQTT Brokers for Testing

| Broker | Host | Port | WebSocket | Notes |
|--------|------|------|-----------|-------|
| test.mosquitto.org | test.mosquitto.org | 1883 | 8081 | Most popular |
| broker.emqx.io | broker.emqx.io | 1883 | 8083 | Enterprise MQTT |
| mqtt.eclipseprojects.io | mqtt.eclipseprojects.io | 1883 | 80 | Eclipse project |
| broker.hivemq.com | broker.hivemq.com | 1883 | 8000 | HiveMQ |

---

## 📝 Timestamp Reference

**Generate current Unix timestamp**:
```bash
# macOS/Linux
date +%s

# Windows PowerShell
[int][double]::Parse((Get-Date -UFormat %s))

# JavaScript
Math.floor(Date.now() / 1000)

# Python
import time
int(time.time())
```

**Convert Unix timestamp to readable time**:
```bash
date -d @1701266400        # Linux
date -r 1701266400         # macOS
```

---

**Last Updated**: November 29, 2025
