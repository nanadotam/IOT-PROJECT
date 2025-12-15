"""
Configuration file for Smart Poultry Heater Control System
"""

# ============================================
# MySQL Database Configuration (XAMPP)
# ============================================

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # XAMPP default (empty password)
    'database': 'poultry_control',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True,
    'pool_size': 5,  # Connection pool size
    'pool_name': 'poultry_pool'
}

# ============================================
# MQTT Broker Configuration
# ============================================

MQTT_CONFIG = {
    'broker': 'localhost',  # Change to your MQTT broker IP if different
    'port': 1883,
    'keepalive': 60,
    'qos': 1,  # Quality of Service (0, 1, or 2)
    'client_id': 'poultry_mqtt_bridge',
    'clean_session': True,
    
    # Topics to subscribe to
    'topics': [
        ('poultry/node1/data', 1),
        ('poultry/node2/data', 1),
        ('poultry/node3/data', 1),
        ('poultry/node1/temperature', 1),
        ('poultry/node2/temperature', 1),
        ('poultry/node3/temperature', 1),
        ('poultry/node1/humidity', 1),
        ('poultry/node2/humidity', 1),
        ('poultry/node3/humidity', 1),
        ('poultry/node1/light', 1),
        ('poultry/node2/light', 1),
        ('poultry/node3/light', 1),
        ('poultry/control/#', 1),
        ('poultry/status', 1)
    ],
    
    # Optional: MQTT authentication
    'username': None,  # Set if your broker requires auth
    'password': None,  # Set if your broker requires auth
    
    # Optional: TLS/SSL
    'use_tls': False,
    'ca_certs': None,
    'certfile': None,
    'keyfile': None
}

# ============================================
# Data Validation Rules
# ============================================

VALIDATION_RULES = {
    'temperature': {
        'min': -40.0,
        'max': 85.0,
        'type': float
    },
    'humidity': {
        'min': 0.0,
        'max': 100.0,
        'type': float
    },
    'ldr': {
        'min': 0.0,
        'max': 100.0,  # Scaled to percentage (0-100)
        'type': float
    },
    'heater_state': {
        'values': [0, 1],
        'type': int
    },
    'device_id': {
        'values': [1, 2, 3],
        'type': int
    },
    'prediction_confidence': {
        'min': 0.0,
        'max': 1.0,
        'type': float,
        'optional': True
    }
}

# ============================================
# Logging Configuration
# ============================================

LOGGING_CONFIG = {
    'log_file': 'mqtt_bridge.log',
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_bytes': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,
    'console_output': True
}

# ============================================
# System Configuration
# ============================================

SYSTEM_CONFIG = {
    'device_count': 3,
    'device_timeout': 300,  # Seconds before marking device offline
    'reconnect_delay': 5,  # Seconds between reconnection attempts
    'max_reconnect_attempts': 10,
    'data_retention_days': 30,  # Days to keep sensor data
    'enable_database_logging': True,
    'enable_file_logging': True
}

# ============================================
# Alert Thresholds (Optional)
# ============================================

ALERT_THRESHOLDS = {
    'temperature': {
        'min': 18.0,
        'max': 35.0
    },
    'humidity': {
        'min': 60.0,
        'max': 95.0
    },
    'low_confidence': 0.70  # Alert if ML confidence < 70%
}

# ============================================
# Development/Testing Mode
# ============================================

DEBUG_MODE = False  # Set to True for verbose logging
TEST_MODE = False   # Set to True to use test database
