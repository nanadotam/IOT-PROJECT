# MQTT Monitor - Quick Guide

## ✅ Arduino Code Verification

Your Arduino code is **CORRECT**! ✅

**Publishing to:**
```cpp
"poultry/device1/sensors"  // When pipeNum = 1
"poultry/device2/sensors"  // When pipeNum = 2
"poultry/device3/sensors"  // When pipeNum = 3
```

**Python expecting:**
```python
'poultry/device1/sensors'
'poultry/device2/sensors'
'poultry/device3/sensors'
```

**✅ PERFECT MATCH!**

---

## 🎧 How to Monitor MQTT Topics in Real-Time

### Step 1: Run the Monitor

Open a new terminal and run:

```bash
python mqtt_monitor.py
```

### Step 2: What You'll See

When Arduino publishes data, you'll see:

```
============================================================
📨 Message Received
Time: 19:45:23
Topic: poultry/device1/sensors
────────────────────────────────────────────────────────────
JSON Data:
  🔢 device_id: 1
  🌡️  temperature: 26.5°C
  💧 humidity: 80.0%
  💡 ldr: 50%
  🔥 heater: OFF
============================================================
```

### Step 3: Verify Topics

The monitor subscribes to:
- `poultry/device1/sensors`
- `poultry/device2/sensors`
- `poultry/device3/sensors`
- `poultry/#` (all poultry topics)

---

## 🔧 If You Need to Change MQTT Broker

Edit `mqtt_monitor.py` line 13:

```python
MQTT_BROKER = "localhost"  # Change to your broker IP
```

For example, if your broker is on `172.20.10.5`:
```python
MQTT_BROKER = "172.20.10.5"
```

---

## 🎯 Testing Checklist

### 1. Start MQTT Broker
```bash
# If using Mosquitto
brew services start mosquitto

# Or check if running
brew services list | grep mosquitto
```

### 2. Run Monitor
```bash
python mqtt_monitor.py
```

You should see:
```
✅ Connected to MQTT Broker!
Broker: localhost:1883

Subscribing to topics:
  📡 poultry/device1/sensors
  📡 poultry/device2/sensors
  📡 poultry/device3/sensors
  📡 poultry/#

🎧 Listening for messages... (Press Ctrl+C to stop)
```

### 3. Power On Arduino Gateway

Arduino should show:
```
WiFi connected!
Gateway IP Address: 172.20.10.2
Connecting to MQTT... connected!
Gateway listening for data from 3 nodes...
```

### 4. Power On Field Nodes

When field nodes transmit, you'll see on:

**Arduino Serial Monitor:**
```
====== New Sensor Data ======
From Node: 1
Temperature: 26.5
Humidity: 80.0
Light Level: 50
=============================
📡 Published to poultry/device1/sensors
{"device_id":1,"temperature":26.5,"humidity":80.0,"ldr":50,"heater":0}
```

**MQTT Monitor Terminal:**
```
============================================================
📨 Message Received
Time: 19:45:23
Topic: poultry/device1/sensors
────────────────────────────────────────────────────────────
JSON Data:
  🔢 device_id: 1
  🌡️  temperature: 26.5°C
  💧 humidity: 80.0%
  💡 ldr: 50%
  🔥 heater: OFF
============================================================
```

---

## 🐛 Troubleshooting

### Monitor Shows "Connection failed"
**Problem:** MQTT broker not running or wrong IP

**Solution:**
```bash
# Check if Mosquitto is running
brew services list | grep mosquitto

# Start if not running
brew services start mosquitto

# Or check broker IP in mqtt_monitor.py
```

### Monitor Connected But No Messages
**Problem:** Arduino not publishing or wrong broker IP

**Check:**
1. Arduino serial monitor shows "connected!" to MQTT
2. Arduino shows "Published to poultry/device1/sensors"
3. Arduino `mqtt_server` IP matches broker IP

### Arduino Shows "MQTT publish failed"
**Problem:** Not connected to MQTT broker

**Check:**
1. MQTT broker is running
2. Arduino `mqtt_server` IP is correct
3. Arduino WiFi is connected

---

## 📊 Multiple Monitors

You can run multiple monitors simultaneously:

**Terminal 1:** MQTT Monitor (see raw data)
```bash
python mqtt_monitor.py
```

**Terminal 2:** Python Bridge (store to database)
```bash
python mqtt_bridge_mysql.py
```

**Terminal 3:** Test Publisher (simulate data)
```bash
python test_mqtt_publisher.py
```

All will receive the same MQTT messages!

---

## 🎯 Expected Data Flow

```
Field Node 1 (nRF24)
    ↓
ESP32 Gateway
    ↓ (WiFi)
MQTT Broker (localhost:1883)
    ↓ (Subscribe)
    ├─→ mqtt_monitor.py (displays)
    ├─→ mqtt_bridge_mysql.py (stores to DB)
    └─→ Any other subscribers
```

---

## 💡 Tips

1. **Keep monitor running** while testing Arduino
2. **Check both** Arduino serial AND monitor terminal
3. **If no data**: Check field nodes are transmitting (see previous debug guide)
4. **Color coding**: Green = success, Red = error, Yellow = info

---

## 🛑 Stop Monitor

Press `Ctrl+C` in the terminal running the monitor

You'll see:
```
⏹️  Stopping monitor...
✅ Monitor stopped
```

---

**That's it!** This monitor will show you exactly what data is being published to MQTT in real-time. 🎉
