# Quick Start Guide - Web Interface

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Prerequisites ✅

Make sure these are running:
- [x] **XAMPP** - Apache and MySQL servers
- [x] **MQTT Bridge** - `python mqtt_bridge_mysql.py` (currently running ✅)
- [x] **Test Publisher** - `python test_mqtt_publisher.py` (currently running ✅)

### Step 2: Copy Web Files to XAMPP 📁

```bash
# Option 1: Copy to htdocs root
cp -r web/ /Applications/XAMPP/htdocs/poultry/

# Option 2: Create symbolic link (recommended for development)
ln -s "$(pwd)/web" /Applications/XAMPP/htdocs/poultry
```

### Step 3: Access the Web Interface 🌐

Open your browser and navigate to:

```
http://localhost/poultry/
```

### Step 4: Test the API 🧪

First, verify the API is working:

```
http://localhost/poultry/test_api.html
```

Click "Run All Tests" to verify all endpoints are working.

---

## 📊 What You Should See

### Dashboard
- **3 Active Devices** (Device 1, Device 2, Device 3)
- **Live Temperature, Humidity, Light readings**
- **Heater Status** for each device
- **Real-time Charts** updating every 10 seconds

### Device Cards
Each device shows:
- Current temperature (°C)
- Current humidity (%)
- Current light intensity (%)
- Heater ON/OFF status
- Online/Offline status

### Analytics
- 24-hour statistics
- ML model performance metrics
- Prediction confidence gauge
- Historical trends chart

---

## 🎛️ Using the Interface

### View Real-Time Data
1. Data updates automatically every 5 seconds
2. Charts update every 10 seconds
3. Click "Refresh" button to update immediately

### Control Heaters (Manual Mode)
1. Switch to **MANUAL** mode in Settings section
2. Click heater button on any device card
3. Command is sent to database (will be picked up by IoT device)

### View Device Details
1. Click "Details" button on any device card
2. See complete sensor readings and timestamps

### Switch Themes
1. Click the moon/sun icon in the navigation bar
2. Toggle between dark and light themes

---

## 🔍 Troubleshooting

### No Data Showing?

**Check 1: Is MQTT Bridge Running?**
```bash
# Check if process is running
ps aux | grep mqtt_bridge_mysql.py

# If not running, start it:
python mqtt_bridge_mysql.py
```

**Check 2: Is Test Publisher Running?**
```bash
# Check if process is running
ps aux | grep test_mqtt_publisher.py

# If not running, start it:
python test_mqtt_publisher.py
```

**Check 3: Is Data in Database?**
```bash
# Open MySQL in XAMPP
mysql -u root

# Check for data
USE poultry_control;
SELECT COUNT(*) FROM sensor_readings;
SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;
```

### API Not Working?

**Check 1: Is Apache Running?**
- Open XAMPP Control Panel
- Verify Apache is running (green indicator)

**Check 2: Is MySQL Running?**
- Open XAMPP Control Panel
- Verify MySQL is running (green indicator)

**Check 3: Test API Directly**
```
http://localhost/poultry/api.php?action=system_status
```

Should return JSON with system information.

### Devices Show as Offline?

**Solution**: The devices will show as online once they start publishing data. The MQTT bridge updates the device status automatically when it receives sensor data.

---

## 📱 Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

---

## 🎯 Quick Commands

### Start Everything
```bash
# Terminal 1: Start MQTT Bridge
python mqtt_bridge_mysql.py

# Terminal 2: Start Test Publisher
python test_mqtt_publisher.py

# Terminal 3: Open XAMPP
open -a XAMPP

# Browser: Open Web Interface
open http://localhost/poultry/
```

### Stop Everything
```bash
# Stop MQTT Bridge: Ctrl+C in Terminal 1
# Stop Test Publisher: Ctrl+C in Terminal 2
# Stop XAMPP: Use XAMPP Control Panel
```

### View Logs
```bash
# MQTT Bridge logs
tail -f mqtt_bridge.log

# MySQL logs
tail -f /Applications/XAMPP/logs/mysql_error.log

# Apache logs
tail -f /Applications/XAMPP/logs/error_log
```

---

## 📊 Understanding the Data

### Temperature
- **Range**: 18°C - 35°C (typical)
- **Updates**: Every 5 seconds
- **Source**: DHT22 sensors on IoT devices

### Humidity
- **Range**: 70% - 100% (typical)
- **Updates**: Every 5 seconds
- **Source**: DHT22 sensors on IoT devices

### Light (LDR)
- **Range**: 0% - 100%
- **Updates**: Every 5 seconds
- **Source**: Light Dependent Resistor sensors

### Heater State
- **Values**: ON (1) or OFF (0)
- **Control**: Automatic (ML model) or Manual
- **Updates**: Based on sensor readings and ML predictions

---

## 🔧 Configuration

### Change Update Interval

Edit `web/script.js`:
```javascript
const CONFIG = {
  updateInterval: 5000,        // Change to desired milliseconds
  chartUpdateInterval: 10000,  // Change to desired milliseconds
};
```

### Change Database Credentials

Edit `web/api.php`:
```php
define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', '');  // Add password if needed
define('DB_NAME', 'poultry_control');
```

---

## 📚 Additional Resources

- **Full Documentation**: `web/README.md`
- **Update Summary**: `WEB_UPDATE_SUMMARY.md`
- **Setup Guide**: `SETUP_GUIDE.md`
- **Project Summary**: `PROJECT_SUMMARY.md`

---

## ✅ Success Checklist

After following this guide, you should have:

- [x] Web interface accessible at `http://localhost/poultry/`
- [x] 3 devices showing with real data
- [x] Charts updating with live sensor readings
- [x] Statistics showing 24-hour aggregates
- [x] Heater controls working in manual mode
- [x] Theme toggle working
- [x] All API endpoints responding correctly

---

## 🎉 You're All Set!

Your Smart Poultry Heater Control System web interface is now running with real data from your MySQL database!

**Next Steps**:
1. Monitor the system for a few hours
2. Review the analytics dashboard
3. Test manual heater control
4. Explore the different sections
5. Check the API test page for detailed endpoint information

**Need Help?**
- Check `web/README.md` for detailed documentation
- Review `WEB_UPDATE_SUMMARY.md` for technical details
- Check logs: `mqtt_bridge.log`

---

**Last Updated**: December 14, 2025  
**Status**: ✅ System Operational
