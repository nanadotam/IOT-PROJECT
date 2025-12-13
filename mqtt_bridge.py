"""
MQTT to Database Bridge - Smart Poultry Heater Control System
Subscribes to MQTT topics and stores sensor data in SQLite database

Architecture:
- Field Devices (ESP32/ATmega328P) → NRF24L → Gateway ESP32
- Gateway ESP32 → MQTT Broker (WiFi)
- This Script → Subscribes to MQTT → Stores in Database
"""

import paho.mqtt.client as mqtt
import sqlite3
import json
import time
from datetime import datetime
import logging

# ============================================
# Configuration
# ============================================

MQTT_CONFIG = {
    'broker': '192.168.1.100',  # Your MQTT broker IP
    'port': 1883,
    'keepalive': 60,
    'topics': [
        'poultry/sensors/#',      # All sensor data
        'poultry/devices/#',      # Device status
        'poultry/control/#'       # Control commands
    ]
}

DB_CONFIG = {
    'database': 'poultry_system.db'
}

# ============================================
# Database Schema
# ============================================

DB_SCHEMA = """
-- Devices Table
CREATE TABLE IF NOT EXISTS devices (
    device_id INTEGER PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT DEFAULT 'field_node',
    status TEXT DEFAULT 'online',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensor Readings Table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    ldr REAL NOT NULL,
    heater_state INTEGER NOT NULL,
    prediction_confidence REAL DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Control Commands Table
CREATE TABLE IF NOT EXISTS control_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    command_type TEXT NOT NULL,
    command_value INTEGER NOT NULL,
    source TEXT DEFAULT 'web_interface',
    executed INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- System Logs Table
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT DEFAULT 'mqtt_bridge',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_time 
    ON sensor_readings(device_id, timestamp DESC);
    
CREATE INDEX IF NOT EXISTS idx_control_commands_device_time 
    ON control_commands(device_id, timestamp DESC);
"""

# ============================================
# Logging Setup
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mqtt_bridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================
# Database Manager
# ============================================

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create database and tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.executescript(DB_SCHEMA)
            self.conn.commit()
            logger.info(f"✅ Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def register_device(self, device_id, device_name=None):
        """Register or update device in database"""
        try:
            cursor = self.conn.cursor()
            
            if device_name is None:
                device_name = f"Device_{device_id}"
            
            cursor.execute("""
                INSERT INTO devices (device_id, device_name, status, last_seen)
                VALUES (?, ?, 'online', CURRENT_TIMESTAMP)
                ON CONFLICT(device_id) DO UPDATE SET
                    status = 'online',
                    last_seen = CURRENT_TIMESTAMP
            """, (device_id, device_name))
            
            self.conn.commit()
            logger.info(f"📱 Device registered: {device_id} ({device_name})")
            return True
        except Exception as e:
            logger.error(f"❌ Device registration failed: {e}")
            return False
    
    def store_sensor_reading(self, data):
        """
        Store sensor reading from MQTT message
        
        Expected data format:
        {
            "device_id": 1,
            "temperature": 26.5,
            "humidity": 80.0,
            "ldr": 50.0,
            "heater": 1,
            "confidence": 0.92  # Optional
        }
        """
        try:
            cursor = self.conn.cursor()
            
            # Register device if not exists
            self.register_device(data['device_id'])
            
            cursor.execute("""
                INSERT INTO sensor_readings 
                (device_id, temperature, humidity, ldr, heater_state, prediction_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['device_id'],
                data['temperature'],
                data['humidity'],
                data['ldr'],
                data['heater'],
                data.get('confidence', None)
            ))
            
            self.conn.commit()
            logger.info(f"📊 Sensor data stored: Device {data['device_id']} - "
                       f"Temp: {data['temperature']}°C, "
                       f"Humidity: {data['humidity']}%, "
                       f"Heater: {'ON' if data['heater'] else 'OFF'}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store sensor reading: {e}")
            return False
    
    def store_control_command(self, data):
        """
        Store control command from MQTT message
        
        Expected data format:
        {
            "device_id": 1,
            "command": "heater",
            "value": 1,
            "source": "web_interface"
        }
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO control_commands 
                (device_id, command_type, command_value, source)
                VALUES (?, ?, ?, ?)
            """, (
                data['device_id'],
                data['command'],
                data['value'],
                data.get('source', 'mqtt')
            ))
            
            self.conn.commit()
            logger.info(f"🎛️  Control command stored: Device {data['device_id']} - "
                       f"{data['command']} = {data['value']}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store control command: {e}")
            return False
    
    def log_system_event(self, level, message, source='mqtt_bridge'):
        """Log system events to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (log_level, message, source)
                VALUES (?, ?, ?)
            """, (level, message, source))
            self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to log system event: {e}")
    
    def get_latest_readings(self, device_id=None, limit=10):
        """Get latest sensor readings"""
        try:
            cursor = self.conn.cursor()
            
            if device_id:
                cursor.execute("""
                    SELECT * FROM sensor_readings 
                    WHERE device_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (device_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM sensor_readings 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Failed to get readings: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("🔒 Database connection closed")

# ============================================
# MQTT Handler
# ============================================

class MQTTBridge:
    def __init__(self, db_manager):
        self.db = db_manager
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Connected to MQTT broker")
            
            # Subscribe to all topics
            for topic in MQTT_CONFIG['topics']:
                client.subscribe(topic)
                logger.info(f"📡 Subscribed to: {topic}")
            
            self.db.log_system_event('INFO', 'MQTT bridge connected')
        else:
            logger.error(f"❌ Connection failed with code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        logger.warning(f"⚠️  Disconnected from MQTT broker (code: {rc})")
        self.db.log_system_event('WARNING', f'MQTT bridge disconnected: {rc}')
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"📨 Message received on {topic}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON payload: {payload}")
                return
            
            # Route message based on topic
            if 'sensors' in topic:
                self.handle_sensor_data(data)
            elif 'control' in topic:
                self.handle_control_command(data)
            elif 'devices' in topic:
                self.handle_device_status(data)
            else:
                logger.warning(f"⚠️  Unknown topic: {topic}")
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def handle_sensor_data(self, data):
        """Handle sensor data messages"""
        required_fields = ['device_id', 'temperature', 'humidity', 'ldr', 'heater']
        
        if all(field in data for field in required_fields):
            self.db.store_sensor_reading(data)
        else:
            logger.error(f"❌ Missing required fields in sensor data: {data}")
    
    def handle_control_command(self, data):
        """Handle control command messages"""
        required_fields = ['device_id', 'command', 'value']
        
        if all(field in data for field in required_fields):
            self.db.store_control_command(data)
        else:
            logger.error(f"❌ Missing required fields in control command: {data}")
    
    def handle_device_status(self, data):
        """Handle device status updates"""
        if 'device_id' in data:
            device_name = data.get('name', f"Device_{data['device_id']}")
            self.db.register_device(data['device_id'], device_name)
        else:
            logger.error(f"❌ Missing device_id in status update: {data}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"🔌 Connecting to MQTT broker at {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
            self.client.connect(
                MQTT_CONFIG['broker'],
                MQTT_CONFIG['port'],
                MQTT_CONFIG['keepalive']
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def start(self):
        """Start MQTT client loop"""
        try:
            logger.info("🚀 Starting MQTT bridge...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("⏹️  MQTT bridge stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ MQTT bridge error: {e}")
            self.stop()
    
    def stop(self):
        """Stop MQTT client"""
        logger.info("🛑 Stopping MQTT bridge...")
        self.client.disconnect()
        self.db.close()

# ============================================
# Main Application
# ============================================

def main():
    """Main application entry point"""
    print("=" * 80)
    print("🐔 Smart Poultry Heater Control System - MQTT Bridge")
    print("=" * 80)
    print()
    
    # Initialize database
    db = DatabaseManager(DB_CONFIG['database'])
    
    # Initialize MQTT bridge
    bridge = MQTTBridge(db)
    
    # Connect and start
    if bridge.connect():
        print(f"✅ MQTT Bridge initialized successfully")
        print(f"📊 Database: {DB_CONFIG['database']}")
        print(f"📡 MQTT Broker: {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
        print(f"🎯 Subscribed Topics: {', '.join(MQTT_CONFIG['topics'])}")
        print()
        print("Press Ctrl+C to stop...")
        print("=" * 80)
        print()
        
        bridge.start()
    else:
        print("❌ Failed to initialize MQTT bridge")
        db.close()

if __name__ == "__main__":
    main()
