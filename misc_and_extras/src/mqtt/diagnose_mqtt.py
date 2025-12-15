#!/usr/bin/env python3
"""
MQTT Diagnostic Tool
Checks what's actually being published to the broker
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime
import sys

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        print("📡 Subscribing to ALL topics (#)")
        client.subscribe("#")  # Subscribe to EVERYTHING
    else:
        print(f"❌ Connection failed with code {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback when message is received"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    print("\n" + "="*80)
    print(f"⏰ {timestamp}")
    print(f"📍 Topic: {topic}")
    print(f"📦 Payload: {payload}")
    
    # Try to parse as JSON
    try:
        data = json.loads(payload)
        print(f"✅ Valid JSON")
        print(f"📊 Parsed Data:")
        for key, value in data.items():
            print(f"   - {key}: {value} (type: {type(value).__name__})")
        
        # Check for device0 issue
        if "device_id" in data:
            device_id = data["device_id"]
            if device_id == 0:
                print(f"⚠️  WARNING: device_id is 0!")
            elif device_id in [1, 2, 3]:
                print(f"✅ Valid device_id: {device_id}")
            else:
                print(f"❌ Invalid device_id: {device_id}")
                
    except json.JSONDecodeError:
        print(f"⚠️  Not valid JSON")
    
    print("="*80)

def main():
    """Main function"""
    print("\n" + "="*80)
    print("🔍 MQTT DIAGNOSTIC TOOL")
    print("="*80)
    print("This tool will show ALL messages on the MQTT broker")
    print("Press Ctrl+C to stop\n")
    
    # Create MQTT client
    client = mqtt.Client(client_id="mqtt_diagnostic", clean_session=True)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to broker
        print(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping diagnostic tool...")
        client.disconnect()
        print("✅ Stopped\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
