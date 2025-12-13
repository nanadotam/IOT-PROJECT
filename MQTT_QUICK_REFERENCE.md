# 📡 MQTT to Database - Quick Reference

## Overview

Based on your project requirements (FR-B3), here's how data flows from MQTT to the database:

```
Field Devices → Gateway ESP32 → MQTT Broker → Python Bridge → SQLite Database → Web Interface
```

---

## 🗄️ Database Structure

### **4 Main Tables:**

1. **devices** - Device registry (6 field nodes)
2. **sensor_readings** - Time-series sensor data
3. **control_commands** - Manual override commands
4. **system_logs** - System events and errors

### **Key Design Decisions:**

✅ **SQLite** - Lightweight, no server needed, perfect for this scale  
✅ **Normalized schema** - Devices table separate from readings  
✅ **Indexed queries** - Fast lookups by device_id and timestamp  
✅ **Auto-timestamps** - Automatic timestamp on all inserts  

---

## 📊 Sensor Data Format

### **MQTT Message (from Gateway):**

**Topic:** `poultry/sensors/device1`

**Payload:**
```json
{
  "device_id": 1,
  "temperature": 26.5,
  "humidity": 80.0,
  "ldr": 50.0,
  "heater": 1,
  "confidence": 0.92
}
```

### **Database Record:**

```sql
INSERT INTO sensor_readings 
(device_id, temperature, humidity, ldr, heater_state, prediction_confidence)
VALUES (1, 26.5, 80.0, 50.0, 1, 0.92);
```

**Result:**
```
id | device_id | temperature | humidity | ldr  | heater_state | confidence | timestamp
1  | 1         | 26.5        | 80.0     | 50.0 | 1            | 0.92       | 2025-12-13 16:00:00
```

---

## 🚀 Quick Start

### **1. Install Dependencies**
```bash
pip install paho-mqtt
```

### **2. Configure MQTT Broker**
Edit `mqtt_bridge.py`:
```python
MQTT_CONFIG = {
    'broker': '192.168.1.100',  # Your broker IP
    'port': 1883,
}
```

### **3. Run the Bridge**
```bash
python mqtt_bridge.py
```

### **4. Verify Database**
```bash
sqlite3 poultry_system.db "SELECT * FROM sensor_readings LIMIT 5;"
```

---

## 🔄 Data Flow Example

### **Step-by-Step:**

1. **Field Device** (ESP32/ATmega328P):
   - Reads DHT22 sensor: `temp=26.5°C, humidity=80%`
   - Reads LDR: `ldr=50%`
   - ML model predicts: `heater=1 (ON)`
   - Sends via NRF24L to Gateway

2. **Gateway ESP32**:
   - Receives NRF24L packet
   - Publishes to MQTT: `poultry/sensors/device1`
   - JSON payload with all sensor data

3. **MQTT Broker**:
   - Receives message
   - Forwards to all subscribers

4. **Python Bridge** (`mqtt_bridge.py`):
   - Subscribes to `poultry/sensors/#`
   - Receives message
   - Validates JSON
   - Inserts into database

5. **SQLite Database**:
   - Stores reading with auto-timestamp
   - Indexed for fast queries

6. **Web Interface** (PHP):
   - Queries database
   - Displays on dashboard
   - Updates charts

---

## 📈 Common Queries

### **Get Latest Reading for Device 1:**
```sql
SELECT * FROM sensor_readings 
WHERE device_id = 1 
ORDER BY timestamp DESC 
LIMIT 1;
```

### **Get Average Temperature (Last Hour):**
```sql
SELECT 
    device_id,
    AVG(temperature) as avg_temp,
    AVG(humidity) as avg_humidity
FROM sensor_readings
WHERE timestamp >= datetime('now', '-1 hour')
GROUP BY device_id;
```

### **Get Heater ON Percentage:**
```sql
SELECT 
    device_id,
    ROUND(AVG(heater_state) * 100, 2) as heater_on_percent
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY device_id;
```

---

## 🎯 Integration Points

### **1. ESP32 Gateway Code**

```cpp
#include <PubSubClient.h>
#include <ArduinoJson.h>

void publishSensorData(int deviceId, float temp, float humidity, float ldr, int heater) {
    StaticJsonDocument<256> doc;
    doc["device_id"] = deviceId;
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["ldr"] = ldr;
    doc["heater"] = heater;
    doc["confidence"] = 0.92;
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    char topic[50];
    sprintf(topic, "poultry/sensors/device%d", deviceId);
    
    mqttClient.publish(topic, buffer);
}
```

### **2. Web Interface (PHP)**

```php
// Get latest readings
$db = new SQLite3('poultry_system.db');
$result = $db->query('
    SELECT * FROM sensor_readings 
    WHERE device_id = 1 
    ORDER BY timestamp DESC 
    LIMIT 10
');

while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    echo json_encode($row);
}
```

### **3. Control Commands**

**Web → MQTT:**
```javascript
// Send heater ON command
fetch('/api.php?action=control', {
    method: 'POST',
    body: JSON.stringify({
        device_id: 1,
        command: 'heater',
        value: 1
    })
});
```

**MQTT → Gateway → Field Device:**
```cpp
void callback(char* topic, byte* payload, unsigned int length) {
    StaticJsonDocument<256> doc;
    deserializeJson(doc, payload, length);
    
    int deviceId = doc["device_id"];
    int value = doc["value"];
    
    // Send to field device via NRF24L
    sendCommandToDevice(deviceId, value);
}
```

---

## 🔧 Troubleshooting

### **Bridge Not Connecting:**
```bash
# Check MQTT broker is running
mosquitto -v

# Test connection
mosquitto_sub -h 192.168.1.100 -t "poultry/#" -v
```

### **No Data in Database:**
```bash
# Check if bridge is running
ps aux | grep mqtt_bridge

# Check logs
tail -f mqtt_bridge.log

# Manually test database
sqlite3 poultry_system.db "SELECT COUNT(*) FROM sensor_readings;"
```

### **Database Locked:**
```python
# Use connection pooling or check_same_thread=False
conn = sqlite3.connect('poultry_system.db', check_same_thread=False)
```

---

## 📝 Files Created

1. **`mqtt_bridge.py`** - Main MQTT-to-Database bridge
2. **`MQTT_DATABASE_ARCHITECTURE.md`** - Full documentation
3. **`requirements.txt`** - Python dependencies
4. **`MQTT_QUICK_REFERENCE.md`** - This file

---

## ✅ Checklist

- [ ] Install `paho-mqtt`
- [ ] Configure MQTT broker IP in `mqtt_bridge.py`
- [ ] Run `python mqtt_bridge.py`
- [ ] Verify database created: `poultry_system.db`
- [ ] Test with sample MQTT message
- [ ] Check data in database
- [ ] Update web interface to use new database
- [ ] Test end-to-end flow

---

## 🎓 Key Concepts

**Why Python Bridge (not Gateway writes to DB)?**
- ✅ Separation of concerns
- ✅ Gateway focuses on IoT communication
- ✅ Python handles data persistence
- ✅ Easier to scale and maintain
- ✅ Can run on separate server

**Why SQLite?**
- ✅ No server setup needed
- ✅ Perfect for 6 devices
- ✅ Fast for read-heavy workloads
- ✅ Easy to backup (single file)
- ✅ Can migrate to PostgreSQL later if needed

**Why MQTT?**
- ✅ Lightweight protocol
- ✅ Publish/Subscribe model
- ✅ Quality of Service (QoS) levels
- ✅ Retained messages
- ✅ Industry standard for IoT

---

**🐔 Your MQTT-to-Database pipeline is ready! 🚀**
