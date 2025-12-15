# 🏗️ Smart Poultry Heater Control System - Architecture Design

## System Overview

**Database:** MySQL (XAMPP localhost)  
**MQTT Bridge:** Python (paho-mqtt + mysql-connector-python)  
**Web Interface:** PHP + JavaScript  
**Field Devices:** 3 nodes (ESP32/ATmega328P)

---

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Field Devices (3 nodes)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Device 1, 2, 3                                          │  │
│  │  - DHT22 (Temp + Humidity)                               │  │
│  │  - LDR (Light sensor)                                    │  │
│  │  - ML Model (C code)                                     │  │
│  │  - NRF24L Radio                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ NRF24L Communication
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gateway ESP32                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Receives data from 3 field devices                    │  │
│  │  - Publishes to MQTT broker (WiFi)                       │  │
│  │  - Topics: Device{N}_temp, Device{N}_humidity,           │  │
│  │            Device{N}_ldr                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ MQTT over WiFi
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MQTT Broker (Mosquitto)                      │
│  - localhost:1883 (or cloud broker)                            │
│  - QoS Level 1 (at least once delivery)                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Subscribe to Topics
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│         Python MQTT Bridge (mqtt_bridge_mysql.py)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ✅ Subscribes to all sensor topics                      │  │
│  │  ✅ Aggregates data from separate topics                 │  │
│  │  ✅ Validates incoming data                              │  │
│  │  ✅ Stores in MySQL database                             │  │
│  │  ✅ Handles connection pooling                           │  │
│  │  ✅ Logs system events                                   │  │
│  │  ✅ Auto-reconnects on failure                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Write to MySQL
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              MySQL Database (XAMPP - localhost)                 │
│  Database: poultry_control                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tables:                                                 │  │
│  │  - devices (3 devices)                                   │  │
│  │  - sensor_readings (aggregated data)                     │  │
│  │  - control_commands (manual overrides)                   │  │
│  │  - system_logs (events & errors)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Read from MySQL
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Web Interface (PHP + JS)                     │
│  - Real-time dashboard                                          │
│  - Device control                                               │
│  - Historical data visualization                                │
│  - Manual heater override                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📡 MQTT Topic Structure (Your Design)

### **Sensor Topics (Published by Gateway)**

```
Device1_temp       → Temperature for Device 1
Device1_humidity   → Humidity for Device 1
Device1_ldr        → Light intensity for Device 1

Device2_temp       → Temperature for Device 2
Device2_humidity   → Humidity for Device 2
Device2_ldr        → Light intensity for Device 2

Device3_temp       → Temperature for Device 3
Device3_humidity   → Humidity for Device 3
Device3_ldr        → Light intensity for Device 3
```

### **Control Topics (Subscribed by Gateway)**

```
control/device1    → Commands for Device 1
control/device2    → Commands for Device 2
control/device3    → Commands for Device 3
```

### **Status Topics**

```
devices/status     → Device online/offline status
```

---

## 📊 MySQL Database Schema

### **Database Configuration**

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS poultry_control 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE poultry_control;
```

### **1. devices Table**

```sql
CREATE TABLE devices (
    device_id INT PRIMARY KEY AUTO_INCREMENT,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) DEFAULT 'field_node',
    status ENUM('online', 'offline', 'error') DEFAULT 'online',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB;

-- Insert 3 devices
INSERT INTO devices (device_id, device_name) VALUES
(1, 'Device 1'),
(2, 'Device 2'),
(3, 'Device 3');
```

### **2. sensor_readings Table**

```sql
CREATE TABLE sensor_readings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    humidity DECIMAL(5,2) NOT NULL,
    ldr DECIMAL(5,2) NOT NULL,
    heater_state TINYINT(1) NOT NULL DEFAULT 0,
    prediction_confidence DECIMAL(4,3) DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_time (device_id, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC)
) ENGINE=InnoDB;
```

### **3. control_commands Table**

```sql
CREATE TABLE control_commands (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    command_type VARCHAR(50) NOT NULL,
    command_value TINYINT(1) NOT NULL,
    source VARCHAR(50) DEFAULT 'web_interface',
    executed TINYINT(1) DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_executed (device_id, executed),
    INDEX idx_timestamp (timestamp DESC)
) ENGINE=InnoDB;
```

### **4. system_logs Table**

```sql
CREATE TABLE system_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    log_level ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100) DEFAULT 'mqtt_bridge',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level_time (log_level, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC)
) ENGINE=InnoDB;
```

---

## 🔄 Data Flow Design

### **Flow 1: Sensor Data (Field Device → Database)**

```
1. Field Device 1 reads sensors
   ├─ Temperature: 26.5°C
   ├─ Humidity: 80.0%
   └─ LDR: 50.0%

2. Field Device sends to Gateway via NRF24L
   └─ Packet: {deviceId: 1, temp: 26.5, humidity: 80.0, ldr: 50.0, heater: 1}

3. Gateway ESP32 publishes to MQTT (3 separate topics)
   ├─ Topic: "Device1_temp"     Payload: "26.5"
   ├─ Topic: "Device1_humidity" Payload: "80.0"
   └─ Topic: "Device1_ldr"      Payload: "50.0"

4. Python Bridge receives messages
   ├─ Aggregates data from 3 topics for Device 1
   ├─ Waits for all 3 values (with timeout)
   └─ Validates data ranges

5. Python Bridge writes to MySQL
   └─ INSERT INTO sensor_readings (device_id, temperature, humidity, ldr, heater_state)
      VALUES (1, 26.5, 80.0, 50.0, 1)

6. Web Interface reads from MySQL
   └─ SELECT * FROM sensor_readings WHERE device_id = 1 ORDER BY timestamp DESC LIMIT 1
```

### **Flow 2: Control Command (Web → Field Device)**

```
1. User clicks "Turn ON Heater" for Device 1

2. Web Interface sends to PHP API
   └─ POST /api.php?action=control
      {device_id: 1, command: "heater", value: 1}

3. PHP API stores in database
   └─ INSERT INTO control_commands (device_id, command_type, command_value, source)
      VALUES (1, 'heater', 1, 'web_interface')

4. PHP API publishes to MQTT
   └─ Topic: "control/device1"
      Payload: {"command": "heater", "value": 1}

5. Gateway ESP32 receives command
   └─ Subscribes to "control/device1"

6. Gateway forwards to Field Device 1 via NRF24L
   └─ Packet: {command: "heater", value: 1}

7. Field Device 1 executes command
   └─ digitalWrite(HEATER_PIN, HIGH)

8. Python Bridge logs command execution
   └─ UPDATE control_commands SET executed = 1 WHERE id = ...
```

---

## 🧩 Python Bridge Design

### **Key Features**

1. **Topic Aggregation**
   - Subscribes to 9 topics (3 devices × 3 sensors)
   - Aggregates data from `Device{N}_temp`, `Device{N}_humidity`, `Device{N}_ldr`
   - Stores complete reading when all 3 values received

2. **Data Validation**
   - Temperature: -40°C to 85°C
   - Humidity: 0% to 100%
   - LDR: 0 to 100
   - Heater: 0 or 1

3. **Connection Management**
   - MySQL connection pooling
   - Auto-reconnect on MQTT disconnect
   - Graceful error handling

4. **Logging**
   - File logging: `mqtt_bridge.log`
   - Database logging: `system_logs` table
   - Console output for monitoring

### **Data Aggregation Strategy**

```python
# Example: Aggregating data for Device 1
device_data = {
    1: {'temp': None, 'humidity': None, 'ldr': None, 'timestamp': None},
    2: {'temp': None, 'humidity': None, 'ldr': None, 'timestamp': None},
    3: {'temp': None, 'humidity': None, 'ldr': None, 'timestamp': None}
}

# When "Device1_temp" arrives → store in device_data[1]['temp']
# When "Device1_humidity" arrives → store in device_data[1]['humidity']
# When "Device1_ldr" arrives → store in device_data[1]['ldr']

# When all 3 values present → INSERT into database
# Clear device_data[1] after insert
```

---

## 🔧 Configuration Files

### **1. MySQL Configuration**

```python
# config.py
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default XAMPP password
    'database': 'poultry_control',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True
}
```

### **2. MQTT Configuration**

```python
# config.py
MQTT_CONFIG = {
    'broker': 'localhost',  # or your MQTT broker IP
    'port': 1883,
    'keepalive': 60,
    'qos': 1,  # At least once delivery
    'topics': [
        'Device1_temp',
        'Device1_humidity',
        'Device1_ldr',
        'Device2_temp',
        'Device2_humidity',
        'Device2_ldr',
        'Device3_temp',
        'Device3_humidity',
        'Device3_ldr',
        'control/#',
        'devices/status'
    ]
}
```

### **3. Data Validation Rules**

```python
# config.py
VALIDATION_RULES = {
    'temperature': {'min': -40, 'max': 85},
    'humidity': {'min': 0, 'max': 100},
    'ldr': {'min': 0, 'max': 100},
    'heater_state': {'values': [0, 1]}
}
```

---

## 📈 Performance Considerations

### **1. Database Optimization**

✅ **Indexes on frequently queried columns**
- `device_id` + `timestamp` (composite index)
- `timestamp` (for time-based queries)
- `status` (for device filtering)

✅ **InnoDB Engine**
- ACID compliance
- Foreign key support
- Row-level locking

✅ **Data Archiving Strategy**
- Keep last 30 days in main table
- Archive older data to `sensor_readings_archive`
- Scheduled cleanup job

### **2. MQTT Optimization**

✅ **QoS Level 1**
- Guaranteed delivery (at least once)
- Balance between reliability and performance

✅ **Connection Pooling**
- Reuse MySQL connections
- Reduce connection overhead

✅ **Message Batching** (Optional)
- Batch multiple readings
- Insert in single transaction

---

## 🛡️ Error Handling Strategy

### **1. MQTT Connection Failures**

```python
- Auto-reconnect with exponential backoff
- Log disconnection events
- Alert after 3 failed reconnection attempts
```

### **2. Database Failures**

```python
- Retry failed inserts (max 3 attempts)
- Queue messages during database downtime
- Log all database errors
```

### **3. Data Validation Failures**

```python
- Log invalid data
- Skip invalid readings
- Alert on repeated validation failures
```

---

## 🎯 System Requirements

### **Software Requirements**

- **XAMPP** (MySQL + Apache)
- **Python 3.8+**
- **Mosquitto MQTT Broker** (or cloud broker)
- **PHP 7.4+**

### **Python Packages**

```txt
paho-mqtt==1.6.1
mysql-connector-python==8.2.0
python-dotenv==1.0.0
```

### **Hardware Requirements**

- **3 Field Devices** (ESP32/ATmega328P)
- **1 Gateway** (ESP32 with WiFi)
- **1 Server** (for Python bridge - can be same as XAMPP)

---

## ✅ Architecture Review Checklist

### **Database Design**
- [x] MySQL schema with proper indexes
- [x] Foreign key constraints
- [x] Timestamp tracking
- [x] Data types optimized for storage

### **MQTT Topics**
- [x] Clear topic naming (Device{N}_{sensor})
- [x] Separate topics for each sensor
- [x] Control topics for commands
- [x] Status topics for monitoring

### **Python Bridge**
- [x] Data aggregation from multiple topics
- [x] Validation before database insert
- [x] Error handling and logging
- [x] Auto-reconnection logic

### **Data Flow**
- [x] Field Device → Gateway → MQTT → Bridge → MySQL → Web
- [x] Web → API → MQTT → Gateway → Field Device
- [x] Bidirectional communication

### **Scalability**
- [x] Can handle 3 devices (expandable to more)
- [x] Efficient database queries
- [x] Connection pooling

---

## 🚀 Next Steps

Once you **approve this architecture**, I will create:

1. **`mqtt_bridge_mysql.py`** - Complete Python MQTT bridge
2. **`config.py`** - Configuration file
3. **`database_setup.sql`** - MySQL schema setup
4. **`requirements.txt`** - Python dependencies
5. **`api_mysql.php`** - Updated PHP API for MySQL
6. **Testing scripts** - For validation

---

## 📝 Questions to Confirm

Before I write the code, please confirm:

1. ✅ **XAMPP MySQL** on localhost with default credentials (root, no password)?
2. ✅ **3 devices** (Device 1, 2, 3)?
3. ✅ **Topic structure** as specified (Device{N}_temp, Device{N}_humidity, Device{N}_ldr)?
4. ✅ **MQTT broker** - localhost or cloud? (I'll default to localhost:1883)
5. ✅ **Data aggregation** - Wait for all 3 sensor values before inserting?

---

**Please review this architecture and let me know if you approve or need any changes! 🎯**
