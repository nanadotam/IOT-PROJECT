-- ============================================
-- Smart Poultry Heater Control System
-- MySQL Database Setup Script
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS poultry_control 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE poultry_control;

-- ============================================
-- 1. DEVICES TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS devices (
    device_id INT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) DEFAULT 'field_node',
    status ENUM('online', 'offline', 'error') DEFAULT 'offline',
    last_seen TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert 3 devices
INSERT INTO devices (device_id, device_name, device_type) VALUES
(1, 'Device 1', 'field_node'),
(2, 'Device 2', 'field_node'),
(3, 'Device 3', 'field_node')
ON DUPLICATE KEY UPDATE 
    device_name = VALUES(device_name),
    device_type = VALUES(device_type);

-- ============================================
-- 2. SENSOR READINGS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    temperature DECIMAL(5,2) NOT NULL COMMENT 'Temperature in Celsius',
    humidity DECIMAL(5,2) NOT NULL COMMENT 'Relative humidity percentage',
    ldr DECIMAL(5,2) NOT NULL COMMENT 'Light intensity (0-100)',
    heater_state TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0=OFF, 1=ON',
    prediction_confidence DECIMAL(4,3) DEFAULT NULL COMMENT 'ML model confidence (0.0-1.0)',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_time (device_id, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_heater_state (heater_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. CONTROL COMMANDS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS control_commands (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    command_type VARCHAR(50) NOT NULL COMMENT 'Type of command (e.g., heater, reset)',
    command_value TINYINT(1) NOT NULL COMMENT 'Command value (0=OFF, 1=ON)',
    source VARCHAR(50) DEFAULT 'web_interface' COMMENT 'Source of command',
    executed TINYINT(1) DEFAULT 0 COMMENT '0=pending, 1=executed',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP NULL DEFAULT NULL,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_executed (device_id, executed),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_pending (executed, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. SYSTEM LOGS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    log_level ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100) DEFAULT 'mqtt_bridge',
    details JSON DEFAULT NULL COMMENT 'Additional log details in JSON format',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_level_time (log_level, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. VIEWS FOR EASY QUERYING
-- ============================================

-- Latest reading per device
CREATE OR REPLACE VIEW latest_readings AS
SELECT 
    d.device_id,
    d.device_name,
    d.status,
    sr.temperature,
    sr.humidity,
    sr.ldr,
    sr.heater_state,
    sr.prediction_confidence,
    sr.timestamp
FROM devices d
LEFT JOIN sensor_readings sr ON d.device_id = sr.device_id
WHERE sr.id IN (
    SELECT MAX(id) 
    FROM sensor_readings 
    GROUP BY device_id
);

-- Device statistics (last 24 hours)
CREATE OR REPLACE VIEW device_stats_24h AS
SELECT 
    device_id,
    COUNT(*) as reading_count,
    AVG(temperature) as avg_temperature,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature,
    AVG(humidity) as avg_humidity,
    MIN(humidity) as min_humidity,
    MAX(humidity) as max_humidity,
    AVG(ldr) as avg_ldr,
    SUM(CASE WHEN heater_state = 1 THEN 1 ELSE 0 END) as heater_on_count,
    ROUND(AVG(heater_state) * 100, 2) as heater_on_percentage
FROM sensor_readings
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY device_id;

-- ============================================
-- 6. STORED PROCEDURES
-- ============================================

DELIMITER //

-- Get latest readings for a device
CREATE PROCEDURE IF NOT EXISTS get_device_readings(
    IN p_device_id INT,
    IN p_limit INT
)
BEGIN
    SELECT * FROM sensor_readings
    WHERE device_id = p_device_id
    ORDER BY timestamp DESC
    LIMIT p_limit;
END //

-- Get pending control commands
CREATE PROCEDURE IF NOT EXISTS get_pending_commands()
BEGIN
    SELECT * FROM control_commands
    WHERE executed = 0
    ORDER BY timestamp ASC;
END //

-- Mark command as executed
CREATE PROCEDURE IF NOT EXISTS mark_command_executed(
    IN p_command_id BIGINT
)
BEGIN
    UPDATE control_commands
    SET executed = 1, executed_at = NOW()
    WHERE id = p_command_id;
END //

-- Clean old data (keep last 30 days)
CREATE PROCEDURE IF NOT EXISTS cleanup_old_data()
BEGIN
    -- Archive sensor readings older than 30 days
    DELETE FROM sensor_readings
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Archive logs older than 30 days
    DELETE FROM system_logs
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Archive executed commands older than 7 days
    DELETE FROM control_commands
    WHERE executed = 1 AND timestamp < DATE_SUB(NOW(), INTERVAL 7 DAY);
END //

DELIMITER ;

-- ============================================
-- 7. INITIAL SYSTEM LOG
-- ============================================

INSERT INTO system_logs (log_level, message, source) 
VALUES ('INFO', 'Database initialized successfully', 'database_setup');

-- ============================================
-- 8. DISPLAY SETUP SUMMARY
-- ============================================

SELECT '✅ Database setup complete!' as status;
SELECT COUNT(*) as device_count FROM devices;
SELECT 'Tables created:' as info, 
       'devices, sensor_readings, control_commands, system_logs' as tables;
SELECT 'Views created:' as info,
       'latest_readings, device_stats_24h' as views;
SELECT 'Procedures created:' as info,
       'get_device_readings, get_pending_commands, mark_command_executed, cleanup_old_data' as procedures;
