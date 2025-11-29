#!/usr/bin/env python3
"""
IoT Device Dashboard - MQTT Test Publisher
Publishes GPS and RFID data directly to MQTT broker
Works with any broker (Kaatru, test.mosquitto.org, etc.)
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import argparse
import sys
from datetime import datetime

# ============ CONFIGURATION ============

# Default test data
TEST_DEVICES = [
    {"id": "device_001", "lat": 12.9352, "lon": 77.6245},  # Bangalore
    {"id": "device_002", "lat": 28.6139, "lon": 77.2090},  # Delhi
    {"id": "device_003", "lat": 19.0760, "lon": 72.8777},  # Mumbai
]

TEST_TAGS = [
    {"uid": "tag_001", "msg": "Package A - Electronics"},
    {"uid": "tag_002", "msg": "Package B - Documents"},
    {"uid": "tag_003", "msg": "Package C - Medical"},
    {"uid": "tag_004", "msg": "Package D - Food"},
    {"uid": "tag_005", "msg": "Package E - Fragile"},
]

# ============ MQTT CLIENT ============

class MQTTPublisher:
    def __init__(self, broker, port, username=None, password=None):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to {self.broker}:{self.port}")
            self.connected = True
        else:
            print(f"❌ Connection failed with code {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"⚠️  Unexpected disconnection: {rc}")
        self.connected = False

    def on_publish(self, client, userdata, mid):
        pass  # Silent on publish

    def connect(self):
        """Connect to MQTT broker"""
        print(f"\n[MQTT] Connecting to {self.broker}:{self.port}...")
        
        self.client = mqtt.Client(client_id=f"test_publisher_{int(time.time())}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        if self.username and self.password:
            print(f"[MQTT] Using authentication: {self.username}")
            self.client.username_pw_set(self.username, self.password)

        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                print("❌ Failed to connect within timeout")
                return False
            
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("✅ Disconnected")

    def publish_gps(self, device_id, gps_topic, lat, lon, timestamp=None):
        """Publish GPS data"""
        if timestamp is None:
            timestamp = int(time.time())

        payload = {
            "dID": device_id,
            "dTS": timestamp,
            "lat": lat,
            "lon": lon
        }

        try:
            self.client.publish(gps_topic, json.dumps(payload), qos=1)
            print(f"📍 GPS: {device_id} at ({lat:.4f}, {lon:.4f})")
            return True
        except Exception as e:
            print(f"❌ GPS Publish error: {e}")
            return False

    def publish_rfid(self, device_id, tag_uid, message, lat, lon, rfid_topic, timestamp=None):
        """Publish RFID scan data"""
        if timestamp is None:
            timestamp = int(time.time())

        payload = {
            "dID": device_id,
            "uID": tag_uid,
            "msg": message,
            "lat": lat,
            "lon": lon,
            "dTS": timestamp
        }

        try:
            self.client.publish(rfid_topic, json.dumps(payload), qos=1)
            print(f"📡 RFID: {device_id} scanned {tag_uid} at ({lat:.4f}, {lon:.4f})")
            return True
        except Exception as e:
            print(f"❌ RFID Publish error: {e}")
            return False


# ============ TEST SCENARIOS ============

def test_single_gps(publisher, gps_topic):
    """Publish a single GPS packet"""
    device = TEST_DEVICES[0]
    publisher.publish_gps(device["id"], gps_topic, device["lat"], device["lon"])


def test_single_rfid(publisher, gps_topic, rfid_topic):
    """Publish a single RFID packet"""
    device = TEST_DEVICES[0]
    tag = TEST_TAGS[0]
    publisher.publish_rfid(device["id"], tag["uid"], tag["msg"], device["lat"], device["lon"], rfid_topic)


def test_all_devices(publisher, gps_topic):
    """Publish GPS for all devices"""
    print("\n[TEST] Publishing GPS for all devices...")
    for device in TEST_DEVICES:
        publisher.publish_gps(device["id"], gps_topic, device["lat"], device["lon"])
        time.sleep(0.5)


def test_all_tags(publisher, gps_topic, rfid_topic):
    """Publish RFID scans for all tags"""
    print("\n[TEST] Publishing RFID scans for all tags...")
    for i, tag in enumerate(TEST_TAGS):
        device = TEST_DEVICES[i % len(TEST_DEVICES)]
        publisher.publish_rfid(device["id"], tag["uid"], tag["msg"], device["lat"], device["lon"], rfid_topic)
        time.sleep(0.5)


def test_continuous_gps(publisher, gps_topic, duration=60):
    """Publish GPS data continuously"""
    print(f"\n[TEST] Publishing GPS data continuously for {duration} seconds...")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    count = 0

    try:
        while (time.time() - start_time) < duration:
            for device in TEST_DEVICES:
                # Add small random variation to coordinates
                lat = device["lat"] + random.uniform(-0.01, 0.01)
                lon = device["lon"] + random.uniform(-0.01, 0.01)
                
                publisher.publish_gps(device["id"], gps_topic, lat, lon)
                count += 1
            
            time.sleep(3)  # Publish every 3 seconds
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    elapsed = time.time() - start_time
    print(f"\n✅ Published {count} GPS packets in {elapsed:.1f} seconds")


def test_continuous_rfid(publisher, gps_topic, rfid_topic, duration=60):
    """Publish RFID scans continuously"""
    print(f"\n[TEST] Publishing RFID scans continuously for {duration} seconds...")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    count = 0

    try:
        while (time.time() - start_time) < duration:
            device = random.choice(TEST_DEVICES)
            tag = random.choice(TEST_TAGS)
            
            # Add small random variation to coordinates
            lat = device["lat"] + random.uniform(-0.01, 0.01)
            lon = device["lon"] + random.uniform(-0.01, 0.01)
            
            publisher.publish_rfid(device["id"], tag["uid"], tag["msg"], lat, lon, rfid_topic)
            count += 1
            
            time.sleep(random.uniform(2, 5))  # Random intervals between scans
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    elapsed = time.time() - start_time
    print(f"\n✅ Published {count} RFID scans in {elapsed:.1f} seconds")


def test_mixed_continuous(publisher, gps_topic, rfid_topic, duration=60):
    """Publish both GPS and RFID data continuously"""
    print(f"\n[TEST] Publishing GPS + RFID data continuously for {duration} seconds...")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    gps_count = 0
    rfid_count = 0

    try:
        while (time.time() - start_time) < duration:
            # Publish GPS every 3 seconds
            for device in TEST_DEVICES:
                lat = device["lat"] + random.uniform(-0.01, 0.01)
                lon = device["lon"] + random.uniform(-0.01, 0.01)
                publisher.publish_gps(device["id"], gps_topic, lat, lon)
                gps_count += 1
            
            # Publish random RFID scan
            device = random.choice(TEST_DEVICES)
            tag = random.choice(TEST_TAGS)
            lat = device["lat"] + random.uniform(-0.01, 0.01)
            lon = device["lon"] + random.uniform(-0.01, 0.01)
            publisher.publish_rfid(device["id"], tag["uid"], tag["msg"], lat, lon, rfid_topic)
            rfid_count += 1
            
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    elapsed = time.time() - start_time
    print(f"\n✅ Published {gps_count} GPS + {rfid_count} RFID in {elapsed:.1f} seconds")


# ============ MAIN ============

def main():
    parser = argparse.ArgumentParser(
        description="IoT Device Dashboard - MQTT Test Publisher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with public broker
  python3 mqtt_publisher.py -b test.mosquitto.org -p 1883

  # Test with Kaatru broker
  python3 mqtt_publisher.py -b node.kaatru.org -p 1883

  # Test with authentication
  python3 mqtt_publisher.py -b broker.com -u username -w password

  # Publish continuously for 60 seconds
  python3 mqtt_publisher.py -b test.mosquitto.org -d 60 -m continuous

  # Test RFID only
  python3 mqtt_publisher.py -b test.mosquitto.org -m rfid

  # Custom topics
  python3 mqtt_publisher.py -b test.mosquitto.org -g sensors/gps -r sensors/rfid
        """
    )

    parser.add_argument("-b", "--broker", default="test.mosquitto.org", 
                        help="MQTT broker address (default: test.mosquitto.org)")
    parser.add_argument("-p", "--port", type=int, default=1883, 
                        help="MQTT broker port (default: 1883)")
    parser.add_argument("-u", "--username", help="MQTT username (optional)")
    parser.add_argument("-w", "--password", help="MQTT password (optional)")
    parser.add_argument("-g", "--gps-topic", default="devices/gps",
                        help="GPS topic (default: devices/gps)")
    parser.add_argument("-r", "--rfid-topic", default="devices/rfid",
                        help="RFID topic (default: devices/rfid)")
    parser.add_argument("-m", "--mode", default="single",
                        choices=["single", "all", "gps", "rfid", "continuous", "mixed"],
                        help="Test mode (default: single)")
    parser.add_argument("-d", "--duration", type=int, default=60,
                        help="Duration for continuous modes in seconds (default: 60)")

    args = parser.parse_args()

    print("""
╔═════════════════════════════════════════════╗
║   IoT Device Dashboard - MQTT Publisher     ║
║                                             ║
║   Test different MQTT brokers and topics    ║
╚═════════════════════════════════════════════╝
    """)

    print(f"[CONFIG]")
    print(f"  Broker: {args.broker}:{args.port}")
    print(f"  GPS Topic: {args.gps_topic}")
    print(f"  RFID Topic: {args.rfid_topic}")
    print(f"  Mode: {args.mode}")
    if args.username:
        print(f"  Username: {args.username}")

    # Create publisher
    publisher = MQTTPublisher(args.broker, args.port, args.username, args.password)

    # Connect
    if not publisher.connect():
        print("\n❌ Failed to connect to broker")
        sys.exit(1)

    # Run test
    try:
        if args.mode == "single":
            print("\n[MODE] Single test - Publishing 1 GPS + 1 RFID")
            test_single_gps(publisher, args.gps_topic)
            time.sleep(1)
            test_single_rfid(publisher, args.gps_topic, args.rfid_topic)

        elif args.mode == "all":
            print("\n[MODE] All devices and tags")
            test_all_devices(publisher, args.gps_topic)
            time.sleep(1)
            test_all_tags(publisher, args.gps_topic, args.rfid_topic)

        elif args.mode == "gps":
            print("\n[MODE] GPS only - All devices")
            test_all_devices(publisher, args.gps_topic)

        elif args.mode == "rfid":
            print("\n[MODE] RFID only - All tags")
            test_all_tags(publisher, args.gps_topic, args.rfid_topic)

        elif args.mode == "continuous":
            print("\n[MODE] Continuous GPS (mixed with RFID)")
            test_continuous_gps(publisher, args.gps_topic, args.duration)

        elif args.mode == "mixed":
            print("\n[MODE] Continuous GPS + RFID")
            test_mixed_continuous(publisher, args.gps_topic, args.rfid_topic, args.duration)

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        publisher.disconnect()
        print("\n✅ Test completed")


if __name__ == "__main__":
    main()
