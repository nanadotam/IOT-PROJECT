****# nRF24L01+ Troubleshooting Guide

## Problem Summary
- **Transmitter**: Sending data successfully (occasional TX OK/FAIL)
- **Receiver**: Receiving packets but all values are 0
- **MQTT**: Publishing zeros to broker

## Root Causes Identified

### 1. Device ID Mapping Issue
**Problem**: Pipe numbers don't directly map to device IDs
- Pipe 1 → Device 0
- Pipe 2 → Device 1  
- Pipe 3 → Device 2

**Solution**: Changed `device_id = pipeNum - 1` in receiver

### 2. Address Mismatch
**Problem**: Your transmitter was using "NODE2" but should use "NODE1" for device 0

**Solution**: 
- Device 0 → "NODE1" (Pipe 1)
- Device 1 → "NODE2" (Pipe 2)
- Device 2 → "NODE3" (Pipe 3)

### 3. Potential Struct Alignment
**Problem**: Data might not be properly aligned between transmitter/receiver

**Solution**: Both use identical struct:
```cpp
struct SensorPacket {
  float temperature;  // 4 bytes
  float humidity;     // 4 bytes
  int lightLevel;     // 4 bytes (ESP32)
};
// Total: 12 bytes
```

## What Was Changed

### Transmitter (transmitter-node0.ino)
✅ Changed address from "NODE2" to "NODE1"  
✅ Added better serial debugging  
✅ Confirmed matching data rate (RF24_250KBPS)  
✅ Confirmed matching power level (RF24_PA_MIN)

### Receiver (redone-receiver-gateway.ino)
✅ Fixed device_id calculation: `device_id = pipeNum - 1`  
✅ Added hex dump debugging to see raw bytes  
✅ Added packet size verification  
✅ Reduced loop delay from 1500ms to 100ms for faster response  
✅ Fixed MQTT topic to use device_id instead of pipeNum

## Testing Steps

1. **Upload receiver code** to ESP32 gateway
2. **Upload transmitter code** to ESP32 transmitter (Device 0)
3. **Monitor receiver serial output** - look for:
   - Pipe Number: 1
   - Raw Bytes: (should NOT be all zeros)
   - Temperature, Humidity, LDR values
4. **Check MQTT** with:
   ```bash
   mosquitto_sub -h 172.20.10.5 -t "poultry/device0/sensors" -v
   ```

## Expected Output

### Receiver Serial Monitor:
```
====== New Sensor Data ======
Pipe Number: 1
Packet Size: 12
Raw Bytes: 00 00 DE 41 66 66 88 42 51 06 00 00
Temperature: 27.80
Humidity: 68.30
Light Level: 1617
📡 Published to poultry/device0/sensors
{"device_id":0,"temperature":27.80,"humidity":68.30,"ldr":1617,"heater":0}
=============================
```

### MQTT Subscriber:
```
poultry/device0/sensors {"device_id":0,"temperature":27.80,"humidity":68.30,"ldr":1617,"heater":0}
```

## If Still Getting Zeros

If you still see zeros after these changes, the hex dump will tell us:

1. **All zeros in Raw Bytes** → nRF24 communication issue (check wiring, power)
2. **Non-zero Raw Bytes but zero values** → Struct alignment issue (need to pack struct)
3. **Pipe Number = 0** → Radio not detecting pipe correctly

## Additional Debugging Commands

### Check nRF24 Configuration (add to setup):
```cpp
Serial.println(radio.isPVariant() ? "nRF24L01+ detected" : "nRF24L01 detected");
Serial.print("Data Rate: ");
Serial.println(radio.getDataRate());
Serial.print("PA Level: ");
Serial.println(radio.getPALevel());
```

### Force Struct Packing (if needed):
```cpp
struct __attribute__((packed)) SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};
```

## Device Address Reference

| Device ID | Pipe Number | Address | Transmitter File |
|-----------|-------------|---------|------------------|
| 0         | 1           | NODE1   | transmitter-node0.ino |
| 1         | 2           | NODE2   | transmitter-node1.ino |
| 2         | 3           | NODE3   | transmitter-node2.ino |
