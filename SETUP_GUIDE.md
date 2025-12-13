# 🚀 MQTT Bridge Setup & Deployment Guide

## Smart Poultry Heater Control System

---

## 📋 Prerequisites

### Software Requirements
- ✅ **XAMPP** (MySQL + Apache) - Running
- ✅ **Python 3.8+** - Installed
- ✅ **Mosquitto MQTT Broker** - Installed and running
- ✅ **Git** (optional) - For version control

### Hardware Requirements (for production)
- 3 Field Devices (ESP32/ATmega328P)
- 1 Gateway ESP32
- Sensors (DHT22, LDR)

---

## 🛠️ Step-by-Step Setup

### **Step 1: Install Python Dependencies**

```bash
# Navigate to project directory
cd "/Users/nanaamoako/Library/CloudStorage/OneDrive-AshesiUniversity/Ashesi/Year 4/IoT/IOT-PROJECT"

# Install required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "paho-mqtt|mysql-connector-python"
```

**Expected output:**
```
mysql-connector-python  8.2.0
paho-mqtt              1.6.1
```

---

### **Step 2: Setup MySQL Database**

#### **2.1 Start XAMPP**
1. Open XAMPP Control Panel
2. Start **MySQL** service
3. Start **Apache** service (for phpMyAdmin)

#### **2.2 Create Database**

**Option A: Using phpMyAdmin (Recommended)**
1. Open browser: `http://localhost/phpmyadmin`
2. Click "SQL" tab
3. Copy entire contents of `database_setup.sql`
4. Paste and click "Go"

**Option B: Using MySQL Command Line**
```bash
# Navigate to XAMPP MySQL bin directory
cd /Applications/XAMPP/xamppfiles/bin  # Mac
# OR
cd C:\xampp\mysql\bin  # Windows

# Run setup script
./mysql -u root -p < "/path/to/database_setup.sql"
# Press Enter when prompted for password (default is empty)
```

#### **2.3 Verify Database**
```sql
-- In phpMyAdmin SQL tab:
USE poultry_control;
SHOW TABLES;
SELECT * FROM devices;
```

**Expected output:**
```
devices
sensor_readings
control_commands
system_logs
```

---

### **Step 3: Install & Configure MQTT Broker**

#### **Option A: Mosquitto (Recommended)**

**Mac:**
```bash
# Install via Homebrew
brew install mosquitto

# Start Mosquitto
brew services start mosquitto

# Verify it's running
brew services list | grep mosquitto
```

**Windows:**
```bash
# Download from: https://mosquitto.org/download/
# Install and start service
net start mosquitto
```

**Linux:**
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

#### **Option B: Cloud MQTT Broker**
- Use HiveMQ Cloud, CloudMQTT, or AWS IoT Core
- Update `config.py` with broker details

#### **Verify MQTT Broker**
```bash
# Test subscribe (Terminal 1)
mosquitto_sub -h localhost -t "test/topic" -v

# Test publish (Terminal 2)
mosquitto_pub -h localhost -t "test/topic" -m "Hello MQTT"
```

---

### **Step 4: Configure the System**

Edit `config.py` if needed:

```python
# MySQL Configuration (default XAMPP)
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty for XAMPP default
    'database': 'poultry_control',
    'port': 3306,
}

# MQTT Configuration
MQTT_CONFIG = {
    'broker': 'localhost',  # Change if using cloud broker
    'port': 1883,
    'topics': [
        ('poultry/device1/sensors', 1),
        ('poultry/device2/sensors', 1),
        ('poultry/device3/sensors', 1),
        ('poultry/control/#', 1),
        ('poultry/status', 1)
    ],
}
```

---

### **Step 5: Test the System**

#### **5.1 Start MQTT Bridge**

```bash
# Terminal 1: Start the bridge
python mqtt_bridge_mysql.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║   🐔 Smart Poultry Heater Control System - MQTT Bridge      ║
║                                                              ║
║   Database: MySQL (XAMPP)                                    ║
║   MQTT Broker: localhost:1883                                ║
║   Devices: 3 field nodes                                     ║
╚══════════════════════════════════════════════════════════════╝

✅ MySQL connection pool initialized
✅ Connected to MQTT broker
📡 Subscribed to: poultry/device1/sensors (QoS 1)
📡 Subscribed to: poultry/device2/sensors (QoS 1)
📡 Subscribed to: poultry/device3/sensors (QoS 1)
📡 Subscribed to: poultry/control/# (QoS 1)
📡 Subscribed to: poultry/status (QoS 1)

Press Ctrl+C to stop...
```

#### **5.2 Test with Simulated Data**

```bash
# Terminal 2: Run test publisher
python test_mqtt_publisher.py
```

**Menu:**
```
🧪 MQTT Test Publisher - Smart Poultry Control System
================================================================================

Select test mode:
1. Single publish (one round for all 3 devices)
2. Continuous publishing (every 5 seconds)
3. Test control commands
4. Test status updates
5. Exit
```

**Choose option 1** for a single test, or **option 2** for continuous testing.

#### **5.3 Verify Data in Database**

```sql
-- In phpMyAdmin:
USE poultry_control;

-- Check latest readings
SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;

-- Check device status
SELECT * FROM devices;

-- Check system logs
SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 10;
```

---

## 📊 Monitoring & Logs

### **View Bridge Logs**
```bash
# Real-time log monitoring
tail -f mqtt_bridge.log

# View last 50 lines
tail -n 50 mqtt_bridge.log

# Search for errors
grep "ERROR" mqtt_bridge.log
```

### **Check System Status**
```sql
-- Latest reading per device
SELECT * FROM latest_readings;

-- 24-hour statistics
SELECT * FROM device_stats_24h;

-- Recent system logs
SELECT * FROM system_logs 
WHERE log_level IN ('ERROR', 'CRITICAL')
ORDER BY timestamp DESC 
LIMIT 20;
```

---

## 🔧 Troubleshooting

### **Problem: Bridge won't connect to MySQL**

**Solution:**
```bash
# Check if MySQL is running
# Mac:
ps aux | grep mysql

# Windows:
netstat -an | find "3306"

# Test MySQL connection
mysql -u root -p -h localhost
```

### **Problem: Bridge won't connect to MQTT**

**Solution:**
```bash
# Check if Mosquitto is running
# Mac:
brew services list | grep mosquitto

# Test MQTT connection
mosquitto_sub -h localhost -t "#" -v

# Check Mosquitto logs
# Mac:
tail -f /usr/local/var/log/mosquitto/mosquitto.log
```

### **Problem: No data in database**

**Solution:**
1. Check bridge logs: `tail -f mqtt_bridge.log`
2. Verify MQTT messages are being published
3. Check data validation rules in `config.py`
4. Verify database permissions

### **Problem: "Access denied" MySQL error**

**Solution:**
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON poultry_control.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🚀 Production Deployment

### **1. Run Bridge as Background Service**

#### **Mac/Linux (systemd)**
Create `/etc/systemd/system/mqtt-bridge.service`:

```ini
[Unit]
Description=Poultry MQTT Bridge
After=network.target mysql.service mosquitto.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/project/mqtt_bridge_mysql.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable mqtt-bridge
sudo systemctl start mqtt-bridge
sudo systemctl status mqtt-bridge
```

#### **Mac (launchd)**
Create `~/Library/LaunchAgents/com.poultry.mqtt-bridge.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.poultry.mqtt-bridge</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/mqtt_bridge_mysql.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.poultry.mqtt-bridge.plist
```

#### **Windows (NSSM)**
```bash
# Download NSSM from nssm.cc
nssm install MQTTBridge "C:\Python39\python.exe" "C:\path\to\mqtt_bridge_mysql.py"
nssm start MQTTBridge
```

### **2. Setup Database Backup**

```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root poultry_control > backup_$DATE.sql
```

### **3. Setup Log Rotation**

Create `/etc/logrotate.d/mqtt-bridge`:

```
/path/to/mqtt_bridge.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 📈 Performance Optimization

### **Database Optimization**
```sql
-- Analyze tables
ANALYZE TABLE sensor_readings;
ANALYZE TABLE control_commands;

-- Optimize tables
OPTIMIZE TABLE sensor_readings;
OPTIMIZE TABLE control_commands;
```

### **Cleanup Old Data**
```sql
-- Run cleanup procedure (keeps last 30 days)
CALL cleanup_old_data();

-- Schedule as cron job (daily at 2 AM)
0 2 * * * mysql -u root poultry_control -e "CALL cleanup_old_data();"
```

---

## ✅ Deployment Checklist

- [ ] Python dependencies installed
- [ ] MySQL database created and verified
- [ ] MQTT broker running
- [ ] `config.py` configured correctly
- [ ] Bridge connects to MySQL successfully
- [ ] Bridge connects to MQTT successfully
- [ ] Test data flows to database
- [ ] Logs are being written
- [ ] Bridge runs as background service (production)
- [ ] Database backup configured
- [ ] Log rotation configured
- [ ] Monitoring/alerting setup (optional)

---

## 🎯 Next Steps

1. **ESP32 Gateway Code** - Implement MQTT publishing
2. **Web Interface** - Update to use MySQL database
3. **Field Devices** - Deploy ML model and sensors
4. **Testing** - End-to-end system testing
5. **Documentation** - User manual and API docs

---

## 📞 Support

For issues or questions:
- Check logs: `mqtt_bridge.log`
- Review database: phpMyAdmin
- Test MQTT: `mosquitto_sub -h localhost -t "#" -v`

---

**🎉 Your MQTT-to-MySQL bridge is ready for deployment!**
