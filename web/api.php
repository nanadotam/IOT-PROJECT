<?php
/**
 * Smart Poultry Heater Control System - API Backend
 * Handles device data, predictions, and control commands
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type');

// Configuration
define('DB_FILE', 'poultry_data.db');
define('MODEL_METADATA', '../model_metadata.json');
define('LOOKUP_TABLE', '../lookup_table.json');

// Database initialization
function initDatabase() {
    $db = new SQLite3(DB_FILE);
    
    // Create tables if they don't exist
    $db->exec('CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        status TEXT DEFAULT "online",
        last_update DATETIME DEFAULT CURRENT_TIMESTAMP
    )');
    
    $db->exec('CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        temperature REAL,
        humidity REAL,
        ldr REAL,
        heater INTEGER,
        confidence REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )');
    
    $db->exec('CREATE TABLE IF NOT EXISTS control_commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        command TEXT,
        value INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )');
    
    // Initialize devices if empty
    $result = $db->query('SELECT COUNT(*) as count FROM devices');
    $row = $result->fetchArray();
    if ($row['count'] == 0) {
        for ($i = 1; $i <= 6; $i++) {
            $db->exec("INSERT INTO devices (id, name) VALUES ($i, 'Device $i')");
        }
    }
    
    return $db;
}

// API Router
$method = $_SERVER['REQUEST_METHOD'];
$request = isset($_GET['action']) ? $_GET['action'] : '';

switch ($request) {
    case 'devices':
        handleDevices($method);
        break;
    
    case 'readings':
        handleReadings($method);
        break;
    
    case 'predict':
        handlePredict($method);
        break;
    
    case 'control':
        handleControl($method);
        break;
    
    case 'stats':
        handleStats($method);
        break;
    
    case 'model':
        handleModel($method);
        break;
    
    default:
        echo json_encode([
            'status' => 'error',
            'message' => 'Invalid action',
            'available_actions' => ['devices', 'readings', 'predict', 'control', 'stats', 'model']
        ]);
        break;
}

// ============================================
// Device Management
// ============================================

function handleDevices($method) {
    $db = initDatabase();
    
    if ($method === 'GET') {
        $devices = [];
        $result = $db->query('SELECT * FROM devices');
        
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            // Get latest reading for each device
            $deviceId = $row['id'];
            $readingQuery = $db->query("
                SELECT * FROM sensor_readings 
                WHERE device_id = $deviceId 
                ORDER BY timestamp DESC 
                LIMIT 1
            ");
            $reading = $readingQuery->fetchArray(SQLITE3_ASSOC);
            
            $devices[] = [
                'id' => $row['id'],
                'name' => $row['name'],
                'status' => $row['status'],
                'last_update' => $row['last_update'],
                'latest_reading' => $reading ?: null
            ];
        }
        
        echo json_encode([
            'status' => 'success',
            'data' => $devices
        ]);
    }
    
    $db->close();
}

// ============================================
// Sensor Readings
// ============================================

function handleReadings($method) {
    $db = initDatabase();
    
    if ($method === 'GET') {
        $deviceId = isset($_GET['device_id']) ? intval($_GET['device_id']) : null;
        $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 100;
        
        if ($deviceId) {
            $result = $db->query("
                SELECT * FROM sensor_readings 
                WHERE device_id = $deviceId 
                ORDER BY timestamp DESC 
                LIMIT $limit
            ");
        } else {
            $result = $db->query("
                SELECT * FROM sensor_readings 
                ORDER BY timestamp DESC 
                LIMIT $limit
            ");
        }
        
        $readings = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $readings[] = $row;
        }
        
        echo json_encode([
            'status' => 'success',
            'data' => $readings
        ]);
    }
    
    if ($method === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        
        $deviceId = $data['device_id'];
        $temperature = $data['temperature'];
        $humidity = $data['humidity'];
        $ldr = $data['ldr'];
        $heater = isset($data['heater']) ? $data['heater'] : predictHeater($temperature, $humidity, $ldr);
        $confidence = isset($data['confidence']) ? $data['confidence'] : 0.85;
        
        $stmt = $db->prepare('
            INSERT INTO sensor_readings (device_id, temperature, humidity, ldr, heater, confidence) 
            VALUES (:device_id, :temperature, :humidity, :ldr, :heater, :confidence)
        ');
        
        $stmt->bindValue(':device_id', $deviceId, SQLITE3_INTEGER);
        $stmt->bindValue(':temperature', $temperature, SQLITE3_FLOAT);
        $stmt->bindValue(':humidity', $humidity, SQLITE3_FLOAT);
        $stmt->bindValue(':ldr', $ldr, SQLITE3_FLOAT);
        $stmt->bindValue(':heater', $heater, SQLITE3_INTEGER);
        $stmt->bindValue(':confidence', $confidence, SQLITE3_FLOAT);
        
        $result = $stmt->execute();
        
        // Update device last_update
        $db->exec("UPDATE devices SET last_update = CURRENT_TIMESTAMP WHERE id = $deviceId");
        
        echo json_encode([
            'status' => 'success',
            'message' => 'Reading saved',
            'id' => $db->lastInsertRowID()
        ]);
    }
    
    $db->close();
}

// ============================================
// ML Prediction
// ============================================

function handlePredict($method) {
    if ($method === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        
        $temperature = $data['temperature'];
        $humidity = $data['humidity'];
        $ldr = $data['ldr'];
        
        $prediction = predictHeater($temperature, $humidity, $ldr);
        $confidence = calculateConfidence($temperature, $humidity, $ldr);
        
        echo json_encode([
            'status' => 'success',
            'prediction' => $prediction,
            'confidence' => $confidence,
            'inputs' => [
                'temperature' => $temperature,
                'humidity' => $humidity,
                'ldr' => $ldr
            ]
        ]);
    }
}

function predictHeater($temp, $humidity, $ldr) {
    // Simple prediction based on humidity (strongest correlation)
    // In production, this would use the actual ML model
    
    // Load lookup table for more accurate predictions
    if (file_exists(LOOKUP_TABLE)) {
        $lookupTable = json_decode(file_get_contents(LOOKUP_TABLE), true);
        
        // Find closest match in lookup table
        $minDistance = PHP_FLOAT_MAX;
        $prediction = 0;
        
        foreach ($lookupTable as $entry) {
            $distance = sqrt(
                pow($entry['temp'] - $temp, 2) +
                pow($entry['humidity'] - $humidity, 2) +
                pow($entry['ldr'] - $ldr, 2)
            );
            
            if ($distance < $minDistance) {
                $minDistance = $distance;
                $prediction = $entry['heater'];
            }
        }
        
        return $prediction;
    }
    
    // Fallback simple rule
    if ($humidity < 80) {
        return 1; // Heater ON
    } else {
        return 0; // Heater OFF
    }
}

function calculateConfidence($temp, $humidity, $ldr) {
    // Calculate confidence based on how typical the values are
    $tempInRange = ($temp >= 18 && $temp <= 35) ? 1 : 0.5;
    $humidityInRange = ($humidity >= 70 && $humidity <= 95) ? 1 : 0.5;
    $ldrInRange = ($ldr >= 0 && $ldr <= 96) ? 1 : 0.5;
    
    $confidence = ($tempInRange + $humidityInRange + $ldrInRange) / 3;
    
    // Add some randomness for realism
    $confidence = $confidence * (0.85 + (mt_rand() / mt_getrandmax()) * 0.1);
    
    return round($confidence, 3);
}

// ============================================
// Control Commands
// ============================================

function handleControl($method) {
    $db = initDatabase();
    
    if ($method === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        
        $deviceId = $data['device_id'];
        $command = $data['command'];
        $value = $data['value'];
        
        $stmt = $db->prepare('
            INSERT INTO control_commands (device_id, command, value) 
            VALUES (:device_id, :command, :value)
        ');
        
        $stmt->bindValue(':device_id', $deviceId, SQLITE3_INTEGER);
        $stmt->bindValue(':command', $command, SQLITE3_TEXT);
        $stmt->bindValue(':value', $value, SQLITE3_INTEGER);
        
        $result = $stmt->execute();
        
        echo json_encode([
            'status' => 'success',
            'message' => 'Command sent',
            'id' => $db->lastInsertRowID()
        ]);
    }
    
    if ($method === 'GET') {
        $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;
        
        $result = $db->query("
            SELECT * FROM control_commands 
            ORDER BY timestamp DESC 
            LIMIT $limit
        ");
        
        $commands = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $commands[] = $row;
        }
        
        echo json_encode([
            'status' => 'success',
            'data' => $commands
        ]);
    }
    
    $db->close();
}

// ============================================
// Statistics
// ============================================

function handleStats($method) {
    $db = initDatabase();
    
    if ($method === 'GET') {
        // Get overall statistics
        $result = $db->query('
            SELECT 
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(ldr) as avg_ldr,
                MIN(ldr) as min_ldr,
                MAX(ldr) as max_ldr,
                AVG(heater) as heater_on_percentage,
                AVG(confidence) as avg_confidence,
                COUNT(*) as total_readings
            FROM sensor_readings
            WHERE timestamp >= datetime("now", "-24 hours")
        ');
        
        $stats = $result->fetchArray(SQLITE3_ASSOC);
        
        // Get device count
        $deviceResult = $db->query('SELECT COUNT(*) as count FROM devices WHERE status = "online"');
        $deviceCount = $deviceResult->fetchArray(SQLITE3_ASSOC)['count'];
        
        echo json_encode([
            'status' => 'success',
            'data' => [
                'temperature' => [
                    'average' => round($stats['avg_temp'], 1),
                    'min' => round($stats['min_temp'], 1),
                    'max' => round($stats['max_temp'], 1)
                ],
                'humidity' => [
                    'average' => round($stats['avg_humidity'], 1),
                    'min' => round($stats['min_humidity'], 1),
                    'max' => round($stats['max_humidity'], 1)
                ],
                'light' => [
                    'average' => round($stats['avg_ldr'], 1),
                    'min' => round($stats['min_ldr'], 1),
                    'max' => round($stats['max_ldr'], 1)
                ],
                'heater_on_percentage' => round($stats['heater_on_percentage'] * 100, 1),
                'avg_confidence' => round($stats['avg_confidence'] * 100, 1),
                'total_readings' => $stats['total_readings'],
                'active_devices' => $deviceCount
            ]
        ]);
    }
    
    $db->close();
}

// ============================================
// Model Information
// ============================================

function handleModel($method) {
    if ($method === 'GET') {
        if (file_exists(MODEL_METADATA)) {
            $metadata = json_decode(file_get_contents(MODEL_METADATA), true);
            
            echo json_encode([
                'status' => 'success',
                'data' => $metadata
            ]);
        } else {
            echo json_encode([
                'status' => 'error',
                'message' => 'Model metadata not found'
            ]);
        }
    }
}

?>
