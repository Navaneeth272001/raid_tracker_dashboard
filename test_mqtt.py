#!/usr/bin/env python3
"""
IoT Device Dashboard - MQTT Test Data Publisher
Simulates GPS and RFID data from IoT devices for testing the dashboard
"""

import paho.mqtt.client as mqtt
import json
import time
import math
import argparse
from datetime import datetime

class IoTSimulator:
    def __init__(self, broker_host, broker_port, gps_topic, rfid_topic):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.gps_topic = gps_topic
        self.rfid_topic = rfid_topic
        self.client = mqtt.Client(f"iot-simulator-{time.time()}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.running = False
        
        # Simulated device locations (latitude, longitude)
        self.devices = {
            "device_001": {"lat": 12.9352, "lon": 77.6245, "name": "Bangalore HQ"},
            "device_002": {"lat": 28.6139, "lon": 77.2090, "name": "Delhi Office"},
            "device_003": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai Hub"},
            "device_004": {"lat": 13.3673, "lon": 74.7421, "name": "Mangalore Port"},
        }
        
        # Simulated RFID tags
        self.tags = [
            {"uid": "tag_001", "msg": "Package A - Electronics"},
            {"uid": "tag_002", "msg": "Package B - Documents"},
            {"uid": "tag_003", "msg": "Package C - Medical Supplies"},
            {"uid": "tag_004", "msg": "Package D - Food Items"},
            {"uid": "tag_005", "msg": "Package E - Fragile"},
        ]
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.running = True
        else:
            print(f"❌ Connection failed with code {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"⚠️  Unexpected disconnection: {rc}")
        self.running = False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"Connecting to {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            time.sleep(1)
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        return True
    
    def publish_gps_data(self, device_id):
        """Publish GPS data for a device with slight variation"""
        device = self.devices[device_id]
        
        # Add small random variation to simulate movement
        lat_variation = math.sin(time.time() / 10) * 0.01
        lon_variation = math.cos(time.time() / 10) * 0.01
        
        payload = {
            "dID": device_id,
            "dTS": int(time.time()),
            "lat": device["lat"] + lat_variation,
            "lon": device["lon"] + lon_variation
        }
        
        self.client.publish(self.gps_topic, json.dumps(payload))
        print(f"📍 GPS [{device_id}] Lat: {payload['lat']:.6f}, Lon: {payload['lon']:.6f}")
    
    def publish_rfid_data(self, device_id):
        """Publish RFID scan data"""
        import random
        device = self.devices[device_id]
        tag = random.choice(self.tags)
        
        payload = {
            "dID": device_id,
            "uID": tag["uid"],
            "msg": tag["msg"],
            "lat": device["lat"],
            "lon": device["lon"],
            "dTS": int(time.time())
        }
        
        self.client.publish(self.rfid_topic, json.dumps(payload))
        print(f"📡 RFID [{device_id}] Tag: {tag['uid']} - {tag['msg']}")
    
    def run(self, duration=60, gps_interval=3, rfid_interval=10):
        """Run simulator for specified duration"""
        if not self.connect():
            return
        
        print(f"\n🚀 Starting IoT Simulator")
        print(f"   Duration: {duration} seconds")
        print(f"   GPS Interval: {gps_interval}s")
        print(f"   RFID Interval: {rfid_interval}s")
        print(f"   Devices: {len(self.devices)}")
        print(f"   Topics: GPS='{self.gps_topic}', RFID='{self.rfid_topic}'")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            gps_counter = 0
            rfid_counter = 0
            start_time = time.time()
            
            while time.time() - start_time < duration:
                if gps_counter >= gps_interval:
                    for device_id in self.devices.keys():
                        self.publish_gps_data(device_id)
                    gps_counter = 0
                
                if rfid_counter >= rfid_interval:
                    import random
                    device_id = random.choice(list(self.devices.keys()))
                    self.publish_rfid_data(device_id)
                    rfid_counter = 0
                
                time.sleep(1)
                gps_counter += 1
                rfid_counter += 1
                
                elapsed = int(time.time() - start_time)
                remaining = duration - elapsed
                print(f"⏱️  Running... {elapsed}s elapsed, {remaining}s remaining", end='\r')
            
            print("\n✅ Simulation completed")
            
        except KeyboardInterrupt:
            print("\n⛔ Simulation stopped by user")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

def continuous_mode(broker_host, broker_port, gps_topic, rfid_topic):
    """Run in continuous mode (publish indefinitely)"""
    simulator = IoTSimulator(broker_host, broker_port, gps_topic, rfid_topic)
    
    if not simulator.connect():
        return
    
    print(f"\n🚀 Starting IoT Simulator (Continuous Mode)")
    print(f"   GPS Interval: 3s")
    print(f"   RFID Interval: 10s")
    print(f"   Devices: {len(simulator.devices)}")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        gps_counter = 0
        rfid_counter = 0
        
        while True:
            if gps_counter >= 3:
                for device_id in simulator.devices.keys():
                    simulator.publish_gps_data(device_id)
                gps_counter = 0
            
            if rfid_counter >= 10:
                import random
                device_id = random.choice(list(simulator.devices.keys()))
                simulator.publish_rfid_data(device_id)
                rfid_counter = 0
            
            time.sleep(1)
            gps_counter += 1
            rfid_counter += 1
            
    except KeyboardInterrupt:
        print("\n⛔ Simulation stopped by user")
    finally:
        simulator.client.loop_stop()
        simulator.client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="IoT Device Dashboard - MQTT Test Data Publisher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test for 60 seconds
  python3 test_mqtt.py -b test.mosquitto.org -p 1883 -d 60
  
  # Continuous mode (until Ctrl+C)
  python3 test_mqtt.py -b test.mosquitto.org -p 1883 --continuous
  
  # Custom topics
  python3 test_mqtt.py -b localhost -p 1883 -g "sensors/gps" -r "sensors/rfid"
        """
    )
    
    parser.add_argument(
        "-b", "--broker",
        default="test.mosquitto.org",
        help="MQTT broker host (default: test.mosquitto.org)"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    parser.add_argument(
        "-g", "--gps-topic",
        default="devices/gps",
        help="GPS topic name (default: devices/gps)"
    )
    parser.add_argument(
        "-r", "--rfid-topic",
        default="devices/rfid",
        help="RFID topic name (default: devices/rfid)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=60,
        help="Duration in seconds (default: 60). Use with --continuous for infinite"
    )
    parser.add_argument(
        "-c", "--continuous",
        action="store_true",
        help="Run in continuous mode (publish indefinitely)"
    )
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_mode(args.broker, args.port, args.gps_topic, args.rfid_topic)
    else:
        simulator = IoTSimulator(args.broker, args.port, args.gps_topic, args.rfid_topic)
        simulator.run(duration=args.duration)
