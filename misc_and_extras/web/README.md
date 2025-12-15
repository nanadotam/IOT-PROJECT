# Smart Poultry Heater Control System - Web Interface

## Overview

This web interface provides real-time monitoring and control for the Smart Poultry Heater Control System. It connects to a MySQL database (XAMPP) to display live sensor data from 3 field devices.

## Features

✅ **Real-time Data Display**
- Live temperature, humidity, and light intensity readings
- Device status monitoring (online/offline)
- Heater state visualization

✅ **Interactive Charts**
- Historical trends for all sensor metrics
- Individual metric sparklines
- Multi-axis comparison charts

✅ **Device Control**
- Manual heater control (when in manual mode)
- Auto/Manual mode switching
- Individual device management

✅ **Analytics Dashboard**
- 24-hour statistics and aggregates
- ML model performance metrics
- Prediction confidence tracking

✅ **Modern UI/UX**
- Dark/Light theme toggle
- Responsive design
- Smooth animations and transitions
- Premium glassmorphism effects

## File Structure

```
web/
├── index.html          # Main HTML structure
├── style.css           # Styling and themes
├── script.js           # Frontend logic and API integration
└── api.php             # Backend API (MySQL connection)
```

## Setup Instructions

### Prerequisites

1. **XAMPP** installed and running
   - Apache server
   - MySQL server

2. **Database Setup**
   - Database name: `poultry_control`
   - Run the `database_setup.sql` script to create tables
   - Default MySQL credentials (can be changed in `api.php`):
     - Host: `localhost`
     - User: `root`
     - Password: `` (empty)
     - Port: `3306`

3. **MQTT Bridge Running**
   - The `mqtt_bridge_mysql.py` script should be running
   - This populates the database with sensor data

### Installation

1. **Copy web files to XAMPP htdocs**
   ```bash
   # Copy the entire web folder to your XAMPP htdocs directory
   cp -r web/ /Applications/XAMPP/htdocs/poultry/
   ```

2. **Configure Database Connection**
   - Open `web/api.php`
   - Update database credentials if needed (lines 13-17):
     ```php
     define('DB_HOST', 'localhost');
     define('DB_USER', 'root');
     define('DB_PASS', '');
     define('DB_NAME', 'poultry_control');
     define('DB_PORT', 3306);
     ```

3. **Start XAMPP Services**
   - Start Apache
   - Start MySQL

4. **Access the Web Interface**
   - Open browser and navigate to:
     ```
     http://localhost/poultry/
     ```

## API Endpoints

The `api.php` file provides the following REST API endpoints:

### 1. Get All Devices
```
GET api.php?action=devices
```
Returns all devices with their latest sensor readings.

**Response:**
```json
{
  "status": "success",
  "data": {
    "devices": [
      {
        "id": 1,
        "name": "Device 1",
        "type": "field_node",
        "status": "online",
        "last_seen": "2025-12-14 17:00:00",
        "latest_reading": {
          "temperature": 26.5,
          "humidity": 80.0,
          "ldr": 50.0,
          "heater": 1,
          "confidence": 0.92,
          "timestamp": "2025-12-14 17:00:00"
        }
      }
    ],
    "count": 3
  }
}
```

### 2. Get Sensor Readings
```
GET api.php?action=readings&device_id=1&limit=100
```
Returns historical sensor readings for a specific device or all devices.

**Parameters:**
- `device_id` (optional): Filter by device ID
- `limit` (optional): Number of records to return (default: 100, max: 1000)

### 3. Get Latest Readings
```
GET api.php?action=latest
```
Returns the most recent reading from each device.

### 4. Get Statistics
```
GET api.php?action=stats
```
Returns 24-hour aggregated statistics for all sensors.

**Response:**
```json
{
  "status": "success",
  "data": {
    "temperature": {
      "average": 26.8,
      "min": 18.0,
      "max": 34.0
    },
    "humidity": {
      "average": 80.5,
      "min": 68.0,
      "max": 100.0
    },
    "light": {
      "average": 49.6,
      "min": 0.0,
      "max": 96.0
    },
    "heater_on_percentage": 50.0,
    "avg_confidence": 92.0,
    "total_readings": 1500,
    "active_devices": 3,
    "total_devices": 3
  }
}
```

### 5. Get Device Statistics
```
GET api.php?action=device_stats
```
Returns per-device statistics for the last 24 hours.

### 6. Send Control Command
```
POST api.php?action=control
Content-Type: application/json

{
  "device_id": 1,
  "command": "heater",
  "value": 1,
  "source": "web_interface"
}
```
Sends a control command to a device.

### 7. Get Control Commands
```
GET api.php?action=control&limit=50
```
Returns recent control commands.

### 8. Get System Status
```
GET api.php?action=system_status
```
Returns overall system health and status.

## Database Schema

The web interface connects to the following MySQL tables:

### Tables
- **devices** - Device information and status
- **sensor_readings** - Historical sensor data
- **control_commands** - Heater control commands
- **system_logs** - System event logs

### Views
- **latest_readings** - Most recent reading per device
- **device_stats_24h** - 24-hour statistics per device

## Configuration

### Update Interval
Modify the update frequency in `script.js`:
```javascript
const CONFIG = {
  apiBaseUrl: "api.php",
  updateInterval: 5000,        // 5 seconds (data refresh)
  chartUpdateInterval: 10000,  // 10 seconds (chart update)
  deviceCount: 3,
  maxChartPoints: 20,
};
```

### Theme
The interface supports dark and light themes. The preference is saved in localStorage.

## Troubleshooting

### No Data Showing
1. **Check MQTT Bridge**: Ensure `mqtt_bridge_mysql.py` is running
2. **Check Database**: Verify data exists in `sensor_readings` table
   ```sql
   SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;
   ```
3. **Check API**: Test API directly in browser
   ```
   http://localhost/poultry/api.php?action=devices
   ```

### Database Connection Error
1. Verify XAMPP MySQL is running
2. Check database credentials in `api.php`
3. Ensure `poultry_control` database exists
4. Check MySQL error log in XAMPP

### Devices Show as Offline
1. Check if MQTT bridge is publishing data
2. Verify `last_seen` timestamp in devices table
3. Ensure device_id matches in MQTT topics and database

### API Returns Empty Data
1. Check if sensor_readings table has data
2. Verify the views are created (`latest_readings`, `device_stats_24h`)
3. Check MySQL user permissions

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Dependencies

### Frontend
- **Chart.js 4.4.0** - Data visualization
- **Inter Font** - Typography

### Backend
- **PHP 7.4+** - Server-side logic
- **MySQL 5.7+** - Database
- **mysqli extension** - Database connectivity

## Security Notes

⚠️ **Important**: This is a development setup. For production:

1. **Change MySQL Password**
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'strong_password';
   ```

2. **Update api.php** with the new password

3. **Enable HTTPS** for secure communication

4. **Add Authentication** to protect the web interface

5. **Sanitize Inputs** - Already using prepared statements, but review for your use case

6. **Restrict CORS** - Update `Access-Control-Allow-Origin` in `api.php`

## Performance Tips

1. **Database Indexing**: Already optimized in `database_setup.sql`
2. **Limit Data**: Use the `limit` parameter in API calls
3. **Cache Results**: Consider adding caching for frequently accessed data
4. **Connection Pooling**: MySQL connection is created per request (consider persistent connections for high traffic)

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Real-time WebSocket updates
- [ ] Export data to CSV/Excel
- [ ] Email/SMS alerts for threshold violations
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced analytics and predictions
- [ ] Multi-farm support

## Support

For issues or questions:
1. Check the main `PROJECT_SUMMARY.md`
2. Review `SETUP_GUIDE.md`
3. Check MQTT bridge logs: `mqtt_bridge.log`
4. Review MySQL error logs in XAMPP

## License

Part of the Smart Poultry Heater Control System IoT Project.

---

**Last Updated**: December 14, 2025  
**Version**: 2.0 (MySQL Integration)
