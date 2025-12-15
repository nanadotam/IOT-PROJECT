# Arduino Gateway - MQTT Topic Configuration

## 🎯 Overview

The Arduino gateway receives sensor data from 3 field nodes via nRF24L01 and publishes to MQTT broker using the **exact same topics** as the Python MQTT bridge.

## 📡 MQTT Topics

### Topic Format
```
poultry/device{X}/sensors
```

### Specific Topics
| Node | Device ID | MQTT Topic |
|------|-----------|------------|
| Node 1 | Device 1 | `poultry/device1/sensors` |
| Node 2 | Device 2 | `poultry/device2/sensors` |
| Node 3 | Device 3 | `poultry/device3/sensors` |

## 📦 JSON Payload Format

The Arduino gateway publishes data in JSON format matching the Python bridge expectations:

```json
{
  "device_id": 1,
  "temperature": 26.5,
  "humidity": 80.0,
  "ldr": 50.0,
  "heater": 0
}
```

### Field Descriptions
- `device_id` (int): Device identifier (1, 2, or 3)
- `temperature` (float): Temperature in Celsius
- `humidity` (float): Relative humidity percentage
- `ldr` (int): Light intensity (0-100%)
- `heater` (int): Heater state (0=OFF, will be set by ML model)

## 🔧 Configuration

### WiFi Settings
```cpp
const char* ssid = "Amoako";
const char* password = "aaaaaaaa";
```

### MQTT Broker Settings
```cpp
const char* mqtt_server = "172.20.10.5";  // Change to your broker IP
const int mqtt_port = 1883;
const char* mqtt_client_id = "PoultryGateway";
```

### nRF24 Pipe Addresses
```cpp
const byte nodeAddresses[][6] = {
  "NODE1",  // Node 1 -> Device 1
  "NODE2",  // Node 2 -> Device 2
  "NODE3"   // Node 3 -> Device 3
};
```

## 📋 Required Libraries

Install these libraries in Arduino IDE:

1. **RF24** by TMRh20
   ```
   Sketch -> Include Library -> Manage Libraries -> Search "RF24"
   ```

2. **PubSubClient** by Nick O'Leary
   ```
   Sketch -> Include Library -> Manage Libraries -> Search "PubSubClient"
   ```

3. **ArduinoJson** by Benoit Blanchon
   ```
   Sketch -> Include Library -> Manage Libraries -> Search "ArduinoJson"
   ```

## 🚀 Upload Instructions

1. **Open Arduino IDE**
2. **Load the sketch**: `src/embedded/gateway_mqtt_publisher.ino`
3. **Select Board**: ESP32 Dev Module
4. **Select Port**: Your ESP32 COM port
5. **Configure settings**:
   - Update WiFi SSID and password
   - Update MQTT broker IP address
6. **Upload**: Click Upload button

## 📊 Data Flow

```
Field Node 1 (nRF24) ──┐
                       │
Field Node 2 (nRF24) ──┼──> ESP32 Gateway ──> MQTT Broker ──> Python Bridge ──> MySQL
                       │
Field Node 3 (nRF24) ──┘
```

## 🔍 Serial Monitor Output

Expected output when receiving data:

```
════════════════════════════════════════
📥 Data received from Node 1 (Device 1)
────────────────────────────────────────
🌡️  Temperature: 26.5 °C
💧 Humidity:    80.0 %
💡 Light Level: 50 %
────────────────────────────────────────
✅ Published to MQTT:
   Topic: poultry/device1/sensors
   Data: {"device_id":1,"temperature":26.5,"humidity":80.0,"ldr":50,"heater":0}
════════════════════════════════════════
```

## ⚙️ Hardware Connections

### ESP32 to nRF24L01
| nRF24L01 Pin | ESP32 Pin |
|--------------|-----------|
| VCC | 3.3V |
| GND | GND |
| CE | GPIO 34 |
| CSN | GPIO 5 |
| SCK | GPIO 18 (SPI) |
| MOSI | GPIO 23 (SPI) |
| MISO | GPIO 19 (SPI) |

## 🐛 Troubleshooting

### WiFi Not Connecting
- Check SSID and password
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check signal strength

### MQTT Connection Failed
- Verify broker IP address
- Ensure broker is running and accessible
- Check firewall settings
- Test with MQTT client (e.g., MQTT Explorer)

### No Data from nRF24
- Check nRF24 wiring
- Verify power supply (3.3V, not 5V!)
- Check pipe addresses match transmitter
- Verify field nodes are transmitting

### JSON Parsing Issues
- Ensure ArduinoJson library is installed
- Check JSON buffer size (currently 200 bytes)
- Verify field names match Python expectations

## 📝 Notes

1. **Topic Consistency**: The topics MUST match exactly with `config.py`:
   ```python
   'topics': [
       ('poultry/device1/sensors', 1),
       ('poultry/device2/sensors', 1),
       ('poultry/device3/sensors', 1),
   ]
   ```

2. **JSON Format**: The Python bridge expects this exact JSON structure. Don't modify field names.

3. **Device ID Mapping**: 
   - nRF24 Pipe 1 → Device 1
   - nRF24 Pipe 2 → Device 2
   - nRF24 Pipe 3 → Device 3

4. **Heater Field**: Always set to 0 in Arduino. The ML model in Python will determine the actual heater state.

## 🔄 Integration with Python System

The Arduino gateway integrates seamlessly with the Python system:

1. **Arduino publishes** → `poultry/device{X}/sensors`
2. **Python bridge subscribes** → Same topics
3. **Python validates** → Data validation rules in `config.py`
4. **Python stores** → MySQL database
5. **Web interface displays** → Real-time data

## ✅ Verification

To verify the gateway is working:

1. **Check Serial Monitor**: Should show received data and MQTT publish confirmations
2. **Check MQTT Broker**: Use MQTT Explorer to see published messages
3. **Check Python Bridge**: Should show incoming messages in logs
4. **Check Database**: Should see new entries in `sensor_readings` table
5. **Check Web Interface**: Should display real-time data

---

**Last Updated**: December 14, 2025  
**Compatible with**: Python MQTT Bridge v2.0
