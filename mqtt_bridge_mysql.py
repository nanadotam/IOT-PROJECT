"""
Smart Poultry Heater Control System - MQTT to MySQL Bridge
Subscribes to MQTT topics and stores sensor data in MySQL database
Functional Programming Approach
"""

import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import pooling
import json
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import sys
import signal

from config import (
    MYSQL_CONFIG, MQTT_CONFIG, VALIDATION_RULES,
    LOGGING_CONFIG, SYSTEM_CONFIG, DEBUG_MODE
)

# ============================================
# Global Variables
# ============================================

# Database connection pool (global)
db_connection_pool = None

# MQTT client (global)
mqtt_client = None

# Connection state
is_connected = False
reconnect_count = 0

# Logger (global)
logger = None

# ============================================
# Logging Functions
# ============================================

def setup_logging():
    """Configure logging with file and console handlers"""
    log = logging.getLogger('MQTTBridge')
    log.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOGGING_CONFIG['log_file'],
        maxBytes=LOGGING_CONFIG['max_bytes'],
        backupCount=LOGGING_CONFIG['backup_count']
    )
    file_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['log_format']))
    log.addHandler(file_handler)
    
    # Console handler
    if LOGGING_CONFIG['console_output']:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['log_format']))
        log.addHandler(console_handler)
    
    return log

# ============================================
# Database Functions
# ============================================

def initialize_database_pool():
    """Initialize MySQL connection pool"""
    global db_connection_pool
    
    try:
        db_connection_pool = pooling.MySQLConnectionPool(
            pool_name=MYSQL_CONFIG['pool_name'],
            pool_size=MYSQL_CONFIG['pool_size'],
            pool_reset_session=True,
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            port=MYSQL_CONFIG['port'],
            charset=MYSQL_CONFIG['charset'],
            autocommit=MYSQL_CONFIG['autocommit']
        )
        logger.info("✅ MySQL connection pool initialized")
        log_system_event('INFO', 'MySQL connection pool initialized')
        return True
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to initialize MySQL pool: {e}")
        return False

def get_database_connection():
    """Get connection from pool"""
    global db_connection_pool
    
    try:
        return db_connection_pool.get_connection()
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to get connection from pool: {e}")
        raise

def update_device_status(device_id, status='online'):
    """Update device status and last_seen timestamp"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE devices 
            SET status = %s, last_seen = NOW()
            WHERE device_id = %s
        """, (status, device_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.debug(f"📱 Device {device_id} status updated: {status}")
        return True
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to update device status: {e}")
        return False

def store_sensor_reading(data):
    """
    Store sensor reading in database
    
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
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Update device status
        update_device_status(data['device_id'], 'online')
        
        # Insert sensor reading
        cursor.execute("""
            INSERT INTO sensor_readings 
            (device_id, temperature, humidity, ldr, heater_state, prediction_confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['device_id'],
            data['temperature'],
            data['humidity'],
            data['ldr'],
            data['heater'],
            data.get('confidence', None)
        ))
        
        reading_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(
            f"📊 Sensor data stored [ID: {reading_id}] - "
            f"Device {data['device_id']}: "
            f"Temp={data['temperature']}°C, "
            f"Humidity={data['humidity']}%, "
            f"LDR={data['ldr']}%, "
            f"Heater={'ON' if data['heater'] else 'OFF'}"
        )
        return True
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to store sensor reading: {e}")
        log_system_event('ERROR', f'Failed to store sensor reading: {e}')
        return False

def store_control_command(data):
    """Store control command in database"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO control_commands 
            (device_id, command_type, command_value, source)
            VALUES (%s, %s, %s, %s)
        """, (
            data['device_id'],
            data['command'],
            data['value'],
            data.get('source', 'mqtt')
        ))
        
        command_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(
            f"🎛️  Control command stored [ID: {command_id}] - "
            f"Device {data['device_id']}: {data['command']}={data['value']}"
        )
        return True
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to store control command: {e}")
        return False

def log_system_event(level, message, source='mqtt_bridge', details=None):
    """Log system event to database"""
    if not SYSTEM_CONFIG['enable_database_logging']:
        return
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        details_json = json.dumps(details) if details else None
        
        cursor.execute("""
            INSERT INTO system_logs (log_level, message, source, details)
            VALUES (%s, %s, %s, %s)
        """, (level, message, source, details_json))
        
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        logger.error(f"❌ Failed to log system event: {e}")

def close_database_pool():
    """Close all connections in pool"""
    global db_connection_pool
    
    if db_connection_pool:
        logger.info("🔒 Closing MySQL connection pool")

# ============================================
# Data Validation Functions
# ============================================

def validate_sensor_data(data):
    """
    Validate sensor data against rules
    Returns: (is_valid, error_message)
    """
    required_fields = ['device_id', 'temperature', 'humidity', 'ldr', 'heater']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate device_id
    if data['device_id'] not in VALIDATION_RULES['device_id']['values']:
        return False, f"Invalid device_id: {data['device_id']}"
    
    # Validate temperature
    try:
        temp = float(data['temperature'])
        if not (VALIDATION_RULES['temperature']['min'] <= temp <= VALIDATION_RULES['temperature']['max']):
            return False, f"Temperature out of range: {temp}"
    except (ValueError, TypeError):
        return False, f"Invalid temperature value: {data['temperature']}"
    
    # Validate humidity
    try:
        humidity = float(data['humidity'])
        if not (VALIDATION_RULES['humidity']['min'] <= humidity <= VALIDATION_RULES['humidity']['max']):
            return False, f"Humidity out of range: {humidity}"
    except (ValueError, TypeError):
        return False, f"Invalid humidity value: {data['humidity']}"
    
    # Validate LDR
    try:
        ldr = float(data['ldr'])
        if not (VALIDATION_RULES['ldr']['min'] <= ldr <= VALIDATION_RULES['ldr']['max']):
            return False, f"LDR out of range: {ldr}"
    except (ValueError, TypeError):
        return False, f"Invalid LDR value: {data['ldr']}"
    
    # Validate heater state
    if data['heater'] not in VALIDATION_RULES['heater_state']['values']:
        return False, f"Invalid heater state: {data['heater']}"
    
    # Validate confidence (optional)
    if 'confidence' in data and data['confidence'] is not None:
        try:
            conf = float(data['confidence'])
            if not (VALIDATION_RULES['prediction_confidence']['min'] <= conf <= VALIDATION_RULES['prediction_confidence']['max']):
                return False, f"Confidence out of range: {conf}"
        except (ValueError, TypeError):
            return False, f"Invalid confidence value: {data['confidence']}"
    
    return True, None

# ============================================
# Message Handling Functions
# ============================================

def handle_sensor_data(data, topic):
    """Handle sensor data messages"""
    # Validate data
    is_valid, error_msg = validate_sensor_data(data)
    
    if not is_valid:
        logger.error(f"❌ Validation failed for {topic}: {error_msg}")
        log_system_event('WARNING', f'Data validation failed: {error_msg}', details=data)
        return
    
    # Store in database
    success = store_sensor_reading(data)
    
    if not success:
        logger.error(f"❌ Failed to store sensor data from {topic}")

def handle_control_command(data, topic):
    """Handle control command messages"""
    required_fields = ['device_id', 'command', 'value']
    
    if all(field in data for field in required_fields):
        store_control_command(data)
    else:
        logger.error(f"❌ Missing required fields in control command: {data}")

def handle_status_update(data, topic):
    """Handle device status updates"""
    if 'device_id' in data and 'status' in data:
        update_device_status(data['device_id'], data['status'])
    else:
        logger.error(f"❌ Invalid status update: {data}")

# ============================================
# MQTT Callback Functions
# ============================================

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    global is_connected, reconnect_count
    
    if rc == 0:
        is_connected = True
        reconnect_count = 0
        logger.info("✅ Connected to MQTT broker")
        
        # Subscribe to all topics
        for topic, qos in MQTT_CONFIG['topics']:
            client.subscribe(topic, qos)
            logger.info(f"📡 Subscribed to: {topic} (QoS {qos})")
        
        log_system_event('INFO', 'MQTT bridge connected to broker')
    else:
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
        logger.error(f"❌ Connection failed: {error_msg}")
        is_connected = False

def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    global is_connected
    
    is_connected = False
    if rc != 0:
        logger.warning(f"⚠️  Unexpected disconnection (code: {rc})")
        log_system_event('WARNING', f'MQTT bridge disconnected: {rc}')
    else:
        logger.info("🔌 Disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """Callback when message received"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"📨 Message received on {topic}: {payload}")
        
        # Parse JSON payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON payload on {topic}: {e}")
            return
        
        # Route message based on topic
        if 'sensors' in topic:
            handle_sensor_data(data, topic)
        elif 'control' in topic:
            handle_control_command(data, topic)
        elif 'status' in topic:
            handle_status_update(data, topic)
        else:
            logger.warning(f"⚠️  Unknown topic: {topic}")
    
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}", exc_info=True)
        log_system_event('ERROR', f'Error processing message: {e}')

# ============================================
# MQTT Connection Functions
# ============================================

def initialize_mqtt_client():
    """Initialize MQTT client with callbacks"""
    global mqtt_client
    
    mqtt_client = mqtt.Client(
        client_id=MQTT_CONFIG['client_id'], 
        clean_session=MQTT_CONFIG['clean_session']
    )
    
    # Set callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    
    # Set authentication if configured
    if MQTT_CONFIG['username'] and MQTT_CONFIG['password']:
        mqtt_client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])
    
    # Set TLS if configured
    if MQTT_CONFIG['use_tls']:
        mqtt_client.tls_set(
            ca_certs=MQTT_CONFIG['ca_certs'],
            certfile=MQTT_CONFIG['certfile'],
            keyfile=MQTT_CONFIG['keyfile']
        )
    
    logger.info("📡 MQTT client initialized")
    return mqtt_client

def connect_to_mqtt_broker():
    """Connect to MQTT broker with retry logic"""
    global reconnect_count, mqtt_client
    
    while reconnect_count < SYSTEM_CONFIG['max_reconnect_attempts']:
        try:
            logger.info(f"🔌 Connecting to MQTT broker at {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
            mqtt_client.connect(
                MQTT_CONFIG['broker'],
                MQTT_CONFIG['port'],
                MQTT_CONFIG['keepalive']
            )
            return True
        except Exception as e:
            reconnect_count += 1
            logger.error(f"❌ Connection attempt {reconnect_count} failed: {e}")
            if reconnect_count < SYSTEM_CONFIG['max_reconnect_attempts']:
                logger.info(f"⏳ Retrying in {SYSTEM_CONFIG['reconnect_delay']} seconds...")
                time.sleep(SYSTEM_CONFIG['reconnect_delay'])
    
    logger.critical("❌ Max reconnection attempts reached. Exiting.")
    return False

def start_mqtt_loop():
    """Start MQTT client loop"""
    global mqtt_client
    
    try:
        logger.info("🚀 Starting MQTT bridge...")
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        logger.info("⏹️  MQTT bridge stopped by user")
        stop_mqtt_bridge()
    except Exception as e:
        logger.error(f"❌ MQTT bridge error: {e}", exc_info=True)
        stop_mqtt_bridge()

def stop_mqtt_bridge():
    """Stop MQTT client gracefully"""
    global mqtt_client
    
    logger.info("🛑 Stopping MQTT bridge...")
    if mqtt_client:
        mqtt_client.disconnect()
    close_database_pool()
    logger.info("✅ MQTT bridge stopped")

# ============================================
# Utility Functions
# ============================================

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\n⏹️  Received interrupt signal. Shutting down...")
    stop_mqtt_bridge()
    sys.exit(0)

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║   🐔 Smart Poultry Heater Control System - MQTT Bridge      ║
    ║                                                              ║
    ║   Database: MySQL (XAMPP)                                    ║
    ║   MQTT Broker: {:<47}║
    ║   Devices: 3 field nodes                                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """.format(f"{MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
    print(banner)

# ============================================
# Main Application
# ============================================

def main():
    """Main application entry point"""
    global logger
    
    # Initialize logger first
    logger = setup_logging()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print banner
    print_banner()
    
    try:
        # Initialize database
        logger.info("🗄️  Initializing database connection...")
        if not initialize_database_pool():
            logger.critical("❌ Failed to initialize database")
            sys.exit(1)
        
        # Initialize MQTT client
        logger.info("📡 Initializing MQTT bridge...")
        initialize_mqtt_client()
        
        # Connect to MQTT broker
        if connect_to_mqtt_broker():
            logger.info("✅ MQTT Bridge initialized successfully")
            logger.info(f"📊 Database: {MYSQL_CONFIG['database']}@{MYSQL_CONFIG['host']}")
            logger.info(f"📡 MQTT Broker: {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
            logger.info(f"🎯 Subscribed to {len(MQTT_CONFIG['topics'])} topics")
            logger.info("")
            logger.info("Press Ctrl+C to stop...")
            logger.info("=" * 80)
            logger.info("")
            
            # Start the MQTT loop
            start_mqtt_loop()
        else:
            logger.critical("❌ Failed to connect to MQTT broker")
            close_database_pool()
            sys.exit(1)
    
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
