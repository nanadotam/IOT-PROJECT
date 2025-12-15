"""
MQTT Test Publisher - Simulates ESP32 Gateway
Publishes test sensor data to MQTT broker for testing the bridge
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# ============================================
# Configuration
# ============================================

MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
PUBLISH_INTERVAL = 5  # seconds

# ============================================
# Test Data Generator
# ============================================

def generate_sensor_data(device_id):
    """Generate realistic sensor data"""
    # Temperature: 18-38°C (realistic poultry range)
    temperature = round(random.uniform(18.0, 38.0), 2)
    
    # Humidity: 60-100% (poultry farms tend to be humid)
    humidity = round(random.uniform(60.0, 100.0), 2)
    
    # LDR: 0-100 (light intensity)
    ldr = round(random.uniform(0.0, 100.0), 2)
    
    # Heater state: Simple logic (ON if temp < 25°C or humidity > 85%)
    heater = 1 if (temperature < 25.0 or humidity > 85.0) else 0
    
    # ML confidence: 0.70-0.99
    confidence = round(random.uniform(0.70, 0.99), 3)
    
    return {
        "device_id": device_id,
        "temperature": temperature,
        "humidity": humidity,
        "ldr": ldr,
        "heater": heater,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# MQTT Publisher
# ============================================

class TestPublisher:
    def __init__(self):
        self.client = mqtt.Client(client_id="test_publisher")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("✅ Connected to MQTT broker")
        else:
            print(f"❌ Connection failed with code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        print(f"📤 Message published (mid: {mid})")
    
    def connect(self):
        try:
            print(f"🔌 Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                return True
            else:
                print("❌ Connection timeout")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def publish_sensor_data(self, device_id):
        """Publish sensor data for a device"""
        data = generate_sensor_data(device_id)
        topic = f"poultry/device{device_id}/sensors"
        payload = json.dumps(data)
        
        result = self.client.publish(topic, payload, qos=1)
        
        print(f"\n📊 Published to {topic}:")
        print(f"   Device: {data['device_id']}")
        print(f"   Temperature: {data['temperature']}°C")
        print(f"   Humidity: {data['humidity']}%")
        print(f"   LDR: {data['ldr']}%")
        print(f"   Heater: {'ON' if data['heater'] else 'OFF'}")
        print(f"   Confidence: {data['confidence']}")
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def publish_control_command(self, device_id, command, value):
        """Publish control command"""
        data = {
            "device_id": device_id,
            "command": command,
            "value": value,
            "source": "test_publisher"
        }
        topic = f"poultry/control/device{device_id}"
        payload = json.dumps(data)
        
        result = self.client.publish(topic, payload, qos=1)
        print(f"\n🎛️  Published control command to {topic}: {command}={value}")
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def publish_status(self, device_id, status):
        """Publish device status"""
        data = {
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        topic = "poultry/status"
        payload = json.dumps(data)
        
        result = self.client.publish(topic, payload, qos=1)
        print(f"\n📡 Published status to {topic}: Device {device_id} is {status}")
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def stop(self):
        """Stop publisher"""
        self.client.loop_stop()
        self.client.disconnect()
        print("\n🛑 Publisher stopped")

# ============================================
# Test Scenarios
# ============================================

def test_continuous_publishing(publisher):
    """Continuously publish sensor data for all 3 devices"""
    print("\n" + "="*80)
    print("🔄 Starting continuous publishing (Ctrl+C to stop)")
    print("="*80)
    
    try:
        iteration = 1
        while True:
            print(f"\n--- Iteration {iteration} ---")
            
            # Publish data for all 3 devices
            for device_id in [1, 2, 3]:
                publisher.publish_sensor_data(device_id)
                time.sleep(0.5)  # Small delay between devices
            
            iteration += 1
            print(f"\n⏳ Waiting {PUBLISH_INTERVAL} seconds...")
            time.sleep(PUBLISH_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")

def test_single_publish(publisher):
    """Publish one round of data for all devices"""
    print("\n" + "="*80)
    print("📤 Publishing single round of data")
    print("="*80)
    
    for device_id in [1, 2, 3]:
        publisher.publish_sensor_data(device_id)
        time.sleep(0.5)
    
    print("\n✅ Single publish complete")

def test_control_commands(publisher):
    """Test control commands"""
    print("\n" + "="*80)
    print("🎛️  Testing control commands")
    print("="*80)
    
    # Turn ON heater for device 1
    publisher.publish_control_command(1, "heater", 1)
    time.sleep(1)
    
    # Turn OFF heater for device 2
    publisher.publish_control_command(2, "heater", 0)
    time.sleep(1)
    
    # Turn ON heater for device 3
    publisher.publish_control_command(3, "heater", 1)
    
    print("\n✅ Control commands sent")

def test_status_updates(publisher):
    """Test status updates"""
    print("\n" + "="*80)
    print("📡 Testing status updates")
    print("="*80)
    
    for device_id in [1, 2, 3]:
        publisher.publish_status(device_id, "online")
        time.sleep(0.5)
    
    print("\n✅ Status updates sent")

# ============================================
# Main Menu
# ============================================

def print_menu():
    """Print test menu"""
    print("\n" + "="*80)
    print("🧪 MQTT Test Publisher - Smart Poultry Control System")
    print("="*80)
    print("\nSelect test mode:")
    print("1. Single publish (one round for all 3 devices)")
    print("2. Continuous publishing (every 5 seconds)")
    print("3. Test control commands")
    print("4. Test status updates")
    print("5. Exit")
    print("="*80)

def main():
    """Main function"""
    # Create publisher
    publisher = TestPublisher()
    
    # Connect to broker
    if not publisher.connect():
        print("❌ Failed to connect to MQTT broker. Exiting.")
        return
    
    try:
        while True:
            print_menu()
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                test_single_publish(publisher)
            elif choice == '2':
                test_continuous_publishing(publisher)
            elif choice == '3':
                test_control_commands(publisher)
            elif choice == '4':
                test_status_updates(publisher)
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    finally:
        publisher.stop()

if __name__ == "__main__":
    main()
