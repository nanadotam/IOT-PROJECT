#!/usr/bin/env python3
"""
MQTT Topic Monitor - Real-time Data Viewer
Subscribes to all poultry topics and displays incoming data
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime
import sys

# MQTT Configuration (matches your config.py)
MQTT_BROKER = "localhost"  # Change to your broker IP if different
MQTT_PORT = 1883
MQTT_TOPICS = [
    "poultry/device1/sensors",
    "poultry/device2/sensors",
    "poultry/device3/sensors",
    "poultry/#"  # Subscribe to all poultry topics
]

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"\n{Colors.GREEN}✅ Connected to MQTT Broker!{Colors.END}")
        print(f"{Colors.CYAN}Broker: {MQTT_BROKER}:{MQTT_PORT}{Colors.END}\n")
        print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}Subscribing to topics:{Colors.END}")
        
        # Subscribe to all topics
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"  📡 {topic}")
        
        print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")
        print(f"{Colors.GREEN}🎧 Listening for messages... (Press Ctrl+C to stop){Colors.END}\n")
    else:
        print(f"{Colors.RED}❌ Connection failed with code {rc}{Colors.END}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback when message is received"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    # Print header
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}📨 Message Received{Colors.END}")
    print(f"{Colors.YELLOW}Time:{Colors.END} {timestamp}")
    print(f"{Colors.YELLOW}Topic:{Colors.END} {topic}")
    print(f"{Colors.YELLOW}{'─'*60}{Colors.END}")
    
    # Try to parse as JSON
    try:
        data = json.loads(payload)
        print(f"{Colors.GREEN}JSON Data:{Colors.END}")
        for key, value in data.items():
            if key == "device_id":
                print(f"  🔢 {key}: {Colors.BOLD}{value}{Colors.END}")
            elif key == "temperature":
                print(f"  🌡️  {key}: {Colors.BOLD}{value}°C{Colors.END}")
            elif key == "humidity":
                print(f"  💧 {key}: {Colors.BOLD}{value}%{Colors.END}")
            elif key == "ldr":
                print(f"  💡 {key}: {Colors.BOLD}{value}%{Colors.END}")
            elif key == "heater":
                status = "ON" if value == 1 else "OFF"
                color = Colors.RED if value == 1 else Colors.BLUE
                print(f"  🔥 {key}: {color}{Colors.BOLD}{status}{Colors.END}")
            else:
                print(f"  📊 {key}: {value}")
    except json.JSONDecodeError:
        # Not JSON, print raw payload
        print(f"{Colors.YELLOW}Raw Data:{Colors.END} {payload}")
    
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"\n{Colors.RED}⚠️  Unexpected disconnection (code: {rc}){Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}🔌 Disconnected from MQTT broker{Colors.END}")

def main():
    """Main function"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}🐔 Smart Poultry MQTT Monitor{Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")
    
    # Create MQTT client
    client = mqtt.Client(client_id="mqtt_monitor", clean_session=True)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        print(f"\n{Colors.CYAN}🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...{Colors.END}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Stopping monitor...{Colors.END}")
        client.disconnect()
        print(f"{Colors.GREEN}✅ Monitor stopped{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
