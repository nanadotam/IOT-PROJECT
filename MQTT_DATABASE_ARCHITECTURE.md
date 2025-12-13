# 📡 MQTT to Database Architecture

## Smart Poultry Heater Control System - Data Flow Documentation

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Field Devices (6 nodes)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ESP32/ATmega328P                                        │  │
│  │  - DHT22 (Temp + Humidity)                               │  │
│  │  - LDR (Light sensor)                                    │  │
│  │  - ML Model (C code)                                     │  │
│  │  - NRF24L Radio                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ NRF24L / Bluetooth
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Gateway ESP32                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Receives data from field devices                      │  │
│  │  - Aggregates sensor readings                            │  │
│  │  - Publishes to MQTT broker (WiFi)                       │  │
│  │  - Hosts web interface                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ MQTT over WiFi
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MQTT Broker                                  │
│  (Mosquitto / HiveMQ / CloudMQTT)                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Subscribe
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                Python MQTT Bridge (mqtt_bridge.py)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Subscribes to MQTT topics                             │  │
│  │  - Validates incoming data                               │  │
│  │  - Stores in SQLite database                             │  │
│  │  - Logs system events                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Write
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                SQLite Database (poultry_system.db)              │
│  - devices                                                      │
│  - sensor_readings                                              │
│  - control_commands                                             │
│  - system_logs                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Read
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Web Interface (PHP API)                      │
│  - Serves data to frontend                                      │
│  - Handles user commands                                        │
│  - Real-time dashboard                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### 1. **devices** Table
Stores information about each field device.

```sql
CREATE TABLE devices (
    device_id INTEGER PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT DEFAULT 'field_node',
    status TEXT DEFAULT 'online',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `device_id`: Unique identifier (1-6 for your 6 devices)
- `device_name`: Human-readable name (e.g., "Device 1", "Coop A")
- `device_type`: Type of device (field_node, gateway, etc.)
- `status`: Current status (online, offline, error)
- `last_seen`: Last time device sent data
- `created_at`: When device was first registered

### 2. **sensor_readings** Table
Stores all sensor data from field devices.

```sql
CREATE TABLE sensor_readings (
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
```

**Fields:**
- `id`: Auto-incrementing primary key
- `device_id`: Which device sent this reading
- `temperature`: Temperature in °C
- `humidity`: Relative humidity in %
- `ldr`: Light intensity (0-100)
- `heater_state`: 0 = OFF, 1 = ON
- `prediction_confidence`: ML model confidence (0.0-1.0)
- `timestamp`: When reading was received

### 3. **control_commands** Table
Stores commands sent to devices (manual override).

```sql
CREATE TABLE control_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    command_type TEXT NOT NULL,
    command_value INTEGER NOT NULL,
    source TEXT DEFAULT 'web_interface',
    executed INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);
```

**Fields:**
- `id`: Auto-incrementing primary key
- `device_id`: Target device
- `command_type`: Type of command (e.g., "heater", "reset")
- `command_value`: Command value (0 = OFF, 1 = ON)
- `source`: Where command came from (web_interface, mqtt, api)
- `executed`: Whether command was executed (0 = pending, 1 = done)
- `timestamp`: When command was issued

### 4. **system_logs** Table
Stores system events and errors.

```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT DEFAULT 'mqtt_bridge',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Auto-incrementing primary key
- `log_level`: INFO, WARNING, ERROR, CRITICAL
- `message`: Log message
- `source`: Component that generated the log
- `timestamp`: When event occurred

---

## 📡 MQTT Topic Structure

### Topic Hierarchy

```
poultry/
├── sensors/
│   ├── device1
│   ├── device2
│   ├── device3
│   ├── device4
│   ├── device5
│   └── device6
├── control/
│   ├── device1
│   ├── device2
│   └── ...
└── devices/
    └── status
```

### 1. **Sensor Data Topics**
`poultry/sensors/device{N}`

**Payload Format (JSON):**
```json
{
  "device_id": 1,
  "temperature": 26.5,
  "humidity": 80.0,
  "ldr": 50.0,
  "heater": 1,
  "confidence": 0.92,
  "timestamp": "2025-12-13T16:00:00Z"
}
```

**ESP32 Gateway Code Example:**
```cpp
void publishSensorData(int deviceId, float temp, float humidity, float ldr, int heater) {
    StaticJsonDocument<256> doc;
    doc["device_id"] = deviceId;
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["ldr"] = ldr;
    doc["heater"] = heater;
    doc["confidence"] = 0.92;  // From ML model
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    char topic[50];
    sprintf(topic, "poultry/sensors/device%d", deviceId);
    
    mqttClient.publish(topic, buffer);
}
```

### 2. **Control Command Topics**
`poultry/control/device{N}`

**Payload Format (JSON):**
```json
{
  "device_id": 1,
  "command": "heater",
  "value": 1,
  "source": "web_interface"
}
```

**ESP32 Gateway Subscription:**
```cpp
void callback(char* topic, byte* payload, unsigned int length) {
    StaticJsonDocument<256> doc;
    deserializeJson(doc, payload, length);
    
    int deviceId = doc["device_id"];
    String command = doc["command"];
    int value = doc["value"];
    
    // Forward command to field device via NRF24L
    sendCommandToDevice(deviceId, command, value);
}
```

### 3. **Device Status Topics**
`poultry/devices/status`

**Payload Format (JSON):**
```json
{
  "device_id": 1,
  "name": "Coop A - Zone 1",
  "status": "online",
  "uptime": 3600,
  "rssi": -45
}
```

---

## 🔄 Data Flow Examples

### Example 1: Sensor Reading Flow

1. **Field Device** reads sensors:
   ```cpp
   float temp = dht.readTemperature();
   float humidity = dht.readHumidity();
   float ldr = analogRead(LDR_PIN) / 10.24;  // 0-100
   ```

2. **Field Device** runs ML prediction:
   ```cpp
   int heater = predict_heater_state(temp, humidity, ldr);
   ```

3. **Field Device** sends to Gateway via NRF24L:
   ```cpp
   SensorData data = {deviceId, temp, humidity, ldr, heater};
   radio.write(&data, sizeof(data));
   ```

4. **Gateway ESP32** receives and publishes to MQTT:
   ```cpp
   publishSensorData(data.deviceId, data.temp, data.humidity, data.ldr, data.heater);
   ```

5. **MQTT Broker** forwards to subscribers

6. **Python Bridge** receives and stores:
   ```python
   def on_message(client, userdata, msg):
       data = json.loads(msg.payload)
       db.store_sensor_reading(data)
   ```

7. **Database** stores the reading

8. **Web Interface** queries database:
   ```php
   $result = $db->query("SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10");
   ```

### Example 2: Control Command Flow

1. **User** clicks "Turn ON Heater" on web interface

2. **Web Interface** sends command to API:
   ```javascript
   fetch('/api.php?action=control', {
       method: 'POST',
       body: JSON.stringify({
           device_id: 1,
           command: 'heater',
           value: 1
       })
   });
   ```

3. **PHP API** publishes to MQTT:
   ```php
   $mqtt->publish('poultry/control/device1', json_encode($command));
   ```

4. **Gateway ESP32** receives command

5. **Gateway** forwards to field device via NRF24L

6. **Field Device** executes command:
   ```cpp
   digitalWrite(HEATER_PIN, command.value);
   ```

7. **Python Bridge** logs command in database

---

## 🚀 Running the MQTT Bridge

### Installation

```bash
# Install required packages
pip install paho-mqtt

# Or use requirements.txt
pip install -r requirements.txt
```

### Configuration

Edit `mqtt_bridge.py`:

```python
MQTT_CONFIG = {
    'broker': '192.168.1.100',  # Your MQTT broker IP
    'port': 1883,
    'keepalive': 60,
    'topics': [
        'poultry/sensors/#',
        'poultry/devices/#',
        'poultry/control/#'
    ]
}

DB_CONFIG = {
    'database': 'poultry_system.db'
}
```

### Running

```bash
# Run the bridge
python mqtt_bridge.py

# Run in background (Linux/Mac)
nohup python mqtt_bridge.py &

# Run as service (systemd)
sudo systemctl start mqtt-bridge
```

### Output

```
================================================================================
🐔 Smart Poultry Heater Control System - MQTT Bridge
================================================================================

✅ MQTT Bridge initialized successfully
📊 Database: poultry_system.db
📡 MQTT Broker: 192.168.1.100:1883
🎯 Subscribed Topics: poultry/sensors/#, poultry/devices/#, poultry/control/#

Press Ctrl+C to stop...
================================================================================

2025-12-13 16:00:01 - INFO - ✅ Connected to MQTT broker
2025-12-13 16:00:01 - INFO - 📡 Subscribed to: poultry/sensors/#
2025-12-13 16:00:05 - INFO - 📨 Message received on poultry/sensors/device1
2025-12-13 16:00:05 - INFO - 📊 Sensor data stored: Device 1 - Temp: 26.5°C, Humidity: 80.0%, Heater: ON
```

---

## 📈 Querying the Database

### Get Latest Readings

```sql
SELECT 
    d.device_name,
    sr.temperature,
    sr.humidity,
    sr.ldr,
    sr.heater_state,
    sr.timestamp
FROM sensor_readings sr
JOIN devices d ON sr.device_id = d.device_id
ORDER BY sr.timestamp DESC
LIMIT 10;
```

### Get Average Temperature per Device

```sql
SELECT 
    device_id,
    AVG(temperature) as avg_temp,
    AVG(humidity) as avg_humidity,
    AVG(ldr) as avg_light,
    COUNT(*) as reading_count
FROM sensor_readings
WHERE timestamp >= datetime('now', '-1 hour')
GROUP BY device_id;
```

### Get Heater ON/OFF Statistics

```sql
SELECT 
    device_id,
    SUM(CASE WHEN heater_state = 1 THEN 1 ELSE 0 END) as heater_on_count,
    SUM(CASE WHEN heater_state = 0 THEN 1 ELSE 0 END) as heater_off_count,
    ROUND(AVG(heater_state) * 100, 2) as heater_on_percentage
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY device_id;
```

---

## 🔧 Integration with Web Interface

Update `web/api.php` to use the new database:

```php
// Connect to database
$db = new SQLite3('poultry_system.db');

// Get latest readings
function getLatestReadings($deviceId = null) {
    global $db;
    
    if ($deviceId) {
        $stmt = $db->prepare('
            SELECT * FROM sensor_readings 
            WHERE device_id = :device_id 
            ORDER BY timestamp DESC 
            LIMIT 1
        ');
        $stmt->bindValue(':device_id', $deviceId, SQLITE3_INTEGER);
    } else {
        $stmt = $db->prepare('
            SELECT * FROM sensor_readings 
            ORDER BY timestamp DESC 
            LIMIT 100
        ');
    }
    
    $result = $stmt->execute();
    // ... process results
}
```

---

## 🎯 Best Practices

### 1. **Data Validation**
- Always validate incoming MQTT messages
- Check for required fields
- Validate data ranges (temp: -40 to 85°C, humidity: 0-100%, etc.)

### 2. **Error Handling**
- Log all errors to database
- Implement retry logic for failed database writes
- Monitor MQTT connection status

### 3. **Performance**
- Use database indexes for faster queries
- Batch insert multiple readings if needed
- Archive old data periodically

### 4. **Security**
- Use MQTT authentication (username/password)
- Enable TLS/SSL for MQTT connections
- Sanitize all database inputs
- Use prepared statements

### 5. **Monitoring**
- Track message rates
- Monitor database size
- Alert on connection failures
- Log system health metrics

---

## 📝 Summary

**Data Flow:**
1. Field devices → NRF24L → Gateway ESP32
2. Gateway → MQTT Broker (WiFi)
3. Python Bridge → SQLite Database
4. Web Interface → Database (read/write)

**Database Structure:**
- `devices` - Device registry
- `sensor_readings` - Time-series sensor data
- `control_commands` - User commands
- `system_logs` - System events

**MQTT Topics:**
- `poultry/sensors/device{N}` - Sensor data
- `poultry/control/device{N}` - Control commands
- `poultry/devices/status` - Device status

This architecture provides a **scalable, reliable, and maintainable** solution for your IoT poultry control system! 🐔
