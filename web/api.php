<?php
/**
 * Smart Poultry Heater Control System - API Backend
 * Connects to MySQL database (XAMPP) and provides real-time data
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type');

// ============================================
// Database Configuration
// ============================================

define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'poultry_control');
define('DB_PORT', 3306);

// ============================================
// Database Connection
// ============================================

function getDBConnection()
{
    try {
        $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT);

        if ($conn->connect_error) {
            throw new Exception("Connection failed: " . $conn->connect_error);
        }

        $conn->set_charset("utf8mb4");
        return $conn;
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'message' => 'Database connection failed',
            'error' => $e->getMessage()
        ]);
        exit;
    }
}

// ============================================
// API Router
// ============================================

$method = $_SERVER['REQUEST_METHOD'];
$action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
    case 'devices':
        handleDevices($method);
        break;

    case 'readings':
        handleReadings($method);
        break;

    case 'latest':
        handleLatestReadings($method);
        break;

    case 'stats':
        handleStats($method);
        break;

    case 'control':
        handleControl($method);
        break;

    case 'system_status':
        handleSystemStatus($method);
        break;

    case 'device_stats':
        handleDeviceStats($method);
        break;

    default:
        echo json_encode([
            'status' => 'error',
            'message' => 'Invalid action',
            'available_actions' => [
                'devices',
                'readings',
                'latest',
                'stats',
                'control',
                'system_status',
                'device_stats'
            ]
        ]);
        break;
}

// ============================================
// Device Management
// ============================================

function handleDevices($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    // Get all devices with their latest readings
    $query = "
        SELECT 
            d.device_id,
            d.device_name,
            d.device_type,
            d.status,
            d.last_seen,
            lr.temperature,
            lr.humidity,
            lr.ldr,
            lr.heater_state,
            lr.prediction_confidence,
            lr.timestamp as last_reading_time
        FROM devices d
        LEFT JOIN latest_readings lr ON d.device_id = lr.device_id
        ORDER BY d.device_id ASC
    ";

    $result = $conn->query($query);

    if (!$result) {
        sendError('Query failed: ' . $conn->error);
        $conn->close();
        return;
    }

    $devices = [];
    while ($row = $result->fetch_assoc()) {
        $devices[] = [
            'id' => (int) $row['device_id'],
            'name' => $row['device_name'],
            'type' => $row['device_type'],
            'status' => $row['status'],
            'last_seen' => $row['last_seen'],
            'latest_reading' => [
                'temperature' => $row['temperature'] ? (float) $row['temperature'] : null,
                'humidity' => $row['humidity'] ? (float) $row['humidity'] : null,
                'ldr' => $row['ldr'] ? (float) $row['ldr'] : null,
                'heater' => $row['heater_state'] !== null ? (int) $row['heater_state'] : null,
                'confidence' => $row['prediction_confidence'] ? (float) $row['prediction_confidence'] : null,
                'timestamp' => $row['last_reading_time']
            ]
        ];
    }

    $conn->close();

    sendSuccess([
        'devices' => $devices,
        'count' => count($devices)
    ]);
}

// ============================================
// Sensor Readings
// ============================================

function handleReadings($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    $deviceId = isset($_GET['device_id']) ? (int) $_GET['device_id'] : null;
    $limit = isset($_GET['limit']) ? (int) $_GET['limit'] : 100;
    $limit = min($limit, 1000); // Max 1000 records

    if ($deviceId) {
        $stmt = $conn->prepare("
            SELECT 
                id,
                device_id,
                temperature,
                humidity,
                ldr,
                heater_state,
                prediction_confidence,
                timestamp
            FROM sensor_readings
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ");
        $stmt->bind_param("ii", $deviceId, $limit);
    } else {
        $stmt = $conn->prepare("
            SELECT 
                id,
                device_id,
                temperature,
                humidity,
                ldr,
                heater_state,
                prediction_confidence,
                timestamp
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT ?
        ");
        $stmt->bind_param("i", $limit);
    }

    $stmt->execute();
    $result = $stmt->get_result();

    $readings = [];
    while ($row = $result->fetch_assoc()) {
        $readings[] = [
            'id' => (int) $row['id'],
            'device_id' => (int) $row['device_id'],
            'temperature' => (float) $row['temperature'],
            'humidity' => (float) $row['humidity'],
            'ldr' => (float) $row['ldr'],
            'heater' => (int) $row['heater_state'],
            'confidence' => $row['prediction_confidence'] ? (float) $row['prediction_confidence'] : null,
            'timestamp' => $row['timestamp']
        ];
    }

    $stmt->close();
    $conn->close();

    sendSuccess([
        'readings' => $readings,
        'count' => count($readings)
    ]);
}

// ============================================
// Latest Readings (All Devices)
// ============================================

function handleLatestReadings($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    $query = "
        SELECT 
            device_id,
            device_name,
            status,
            temperature,
            humidity,
            ldr,
            heater_state,
            prediction_confidence,
            timestamp
        FROM latest_readings
        ORDER BY device_id ASC
    ";

    $result = $conn->query($query);

    if (!$result) {
        sendError('Query failed: ' . $conn->error);
        $conn->close();
        return;
    }

    $readings = [];
    while ($row = $result->fetch_assoc()) {
        $readings[] = [
            'device_id' => (int) $row['device_id'],
            'device_name' => $row['device_name'],
            'status' => $row['status'],
            'temperature' => $row['temperature'] ? (float) $row['temperature'] : null,
            'humidity' => $row['humidity'] ? (float) $row['humidity'] : null,
            'ldr' => $row['ldr'] ? (float) $row['ldr'] : null,
            'heater' => $row['heater_state'] !== null ? (int) $row['heater_state'] : null,
            'confidence' => $row['prediction_confidence'] ? (float) $row['prediction_confidence'] : null,
            'timestamp' => $row['timestamp']
        ];
    }

    $conn->close();

    sendSuccess([
        'readings' => $readings,
        'count' => count($readings)
    ]);
}

// ============================================
// Statistics (24 hour aggregates)
// ============================================

function handleStats($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    // Get overall statistics from the last 24 hours
    $query = "
        SELECT 
            COUNT(*) as total_readings,
            AVG(temperature) as avg_temp,
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            AVG(humidity) as avg_humidity,
            MIN(humidity) as min_humidity,
            MAX(humidity) as max_humidity,
            AVG(ldr) as avg_ldr,
            MIN(ldr) as min_ldr,
            MAX(ldr) as max_ldr,
            AVG(heater_state) as heater_on_percentage,
            AVG(prediction_confidence) as avg_confidence
        FROM sensor_readings
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    ";

    $result = $conn->query($query);
    $stats = $result->fetch_assoc();

    // Get active device count
    $deviceQuery = "SELECT COUNT(*) as count FROM devices WHERE status = 'online'";
    $deviceResult = $conn->query($deviceQuery);
    $deviceCount = $deviceResult->fetch_assoc()['count'];

    // Get total device count
    $totalDeviceQuery = "SELECT COUNT(*) as count FROM devices";
    $totalDeviceResult = $conn->query($totalDeviceQuery);
    $totalDeviceCount = $totalDeviceResult->fetch_assoc()['count'];

    $conn->close();

    sendSuccess([
        'temperature' => [
            'average' => $stats['avg_temp'] ? round((float) $stats['avg_temp'], 1) : null,
            'min' => $stats['min_temp'] ? round((float) $stats['min_temp'], 1) : null,
            'max' => $stats['max_temp'] ? round((float) $stats['max_temp'], 1) : null
        ],
        'humidity' => [
            'average' => $stats['avg_humidity'] ? round((float) $stats['avg_humidity'], 1) : null,
            'min' => $stats['min_humidity'] ? round((float) $stats['min_humidity'], 1) : null,
            'max' => $stats['max_humidity'] ? round((float) $stats['max_humidity'], 1) : null
        ],
        'light' => [
            'average' => $stats['avg_ldr'] ? round((float) $stats['avg_ldr'], 1) : null,
            'min' => $stats['min_ldr'] ? round((float) $stats['min_ldr'], 1) : null,
            'max' => $stats['max_ldr'] ? round((float) $stats['max_ldr'], 1) : null
        ],
        'heater_on_percentage' => $stats['heater_on_percentage'] ? round((float) $stats['heater_on_percentage'] * 100, 1) : 0,
        'avg_confidence' => $stats['avg_confidence'] ? round((float) $stats['avg_confidence'] * 100, 1) : null,
        'total_readings' => (int) $stats['total_readings'],
        'active_devices' => (int) $deviceCount,
        'total_devices' => (int) $totalDeviceCount
    ]);
}

// ============================================
// Device Statistics (per device, 24h)
// ============================================

function handleDeviceStats($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    $query = "
        SELECT 
            d.device_id,
            d.device_name,
            ds.reading_count,
            ds.avg_temperature,
            ds.min_temperature,
            ds.max_temperature,
            ds.avg_humidity,
            ds.min_humidity,
            ds.max_humidity,
            ds.avg_ldr,
            ds.heater_on_percentage
        FROM devices d
        LEFT JOIN device_stats_24h ds ON d.device_id = ds.device_id
        ORDER BY d.device_id ASC
    ";

    $result = $conn->query($query);

    if (!$result) {
        sendError('Query failed: ' . $conn->error);
        $conn->close();
        return;
    }

    $deviceStats = [];
    while ($row = $result->fetch_assoc()) {
        $deviceStats[] = [
            'device_id' => (int) $row['device_id'],
            'device_name' => $row['device_name'],
            'reading_count' => $row['reading_count'] ? (int) $row['reading_count'] : 0,
            'temperature' => [
                'avg' => $row['avg_temperature'] ? round((float) $row['avg_temperature'], 1) : null,
                'min' => $row['min_temperature'] ? round((float) $row['min_temperature'], 1) : null,
                'max' => $row['max_temperature'] ? round((float) $row['max_temperature'], 1) : null
            ],
            'humidity' => [
                'avg' => $row['avg_humidity'] ? round((float) $row['avg_humidity'], 1) : null,
                'min' => $row['min_humidity'] ? round((float) $row['min_humidity'], 1) : null,
                'max' => $row['max_humidity'] ? round((float) $row['max_humidity'], 1) : null
            ],
            'ldr' => [
                'avg' => $row['avg_ldr'] ? round((float) $row['avg_ldr'], 1) : null
            ],
            'heater_on_percentage' => $row['heater_on_percentage'] ? round((float) $row['heater_on_percentage'], 1) : 0
        ];
    }

    $conn->close();

    sendSuccess([
        'device_stats' => $deviceStats,
        'count' => count($deviceStats)
    ]);
}

// ============================================
// Control Commands
// ============================================

function handleControl($method)
{
    $conn = getDBConnection();

    if ($method === 'POST') {
        // Create new control command
        $data = json_decode(file_get_contents('php://input'), true);

        if (!isset($data['device_id']) || !isset($data['command']) || !isset($data['value'])) {
            sendError('Missing required fields: device_id, command, value');
            $conn->close();
            return;
        }

        $stmt = $conn->prepare("
            INSERT INTO control_commands 
            (device_id, command_type, command_value, source)
            VALUES (?, ?, ?, ?)
        ");

        $source = isset($data['source']) ? $data['source'] : 'web_interface';
        $stmt->bind_param(
            "isis",
            $data['device_id'],
            $data['command'],
            $data['value'],
            $source
        );

        if ($stmt->execute()) {
            $commandId = $stmt->insert_id;
            $stmt->close();
            $conn->close();

            sendSuccess([
                'message' => 'Command sent successfully',
                'command_id' => $commandId
            ]);
        } else {
            sendError('Failed to insert command: ' . $stmt->error);
            $stmt->close();
            $conn->close();
        }

    } elseif ($method === 'GET') {
        // Get recent control commands
        $limit = isset($_GET['limit']) ? (int) $_GET['limit'] : 50;
        $limit = min($limit, 500);

        $stmt = $conn->prepare("
            SELECT 
                id,
                device_id,
                command_type,
                command_value,
                source,
                executed,
                timestamp,
                executed_at
            FROM control_commands
            ORDER BY timestamp DESC
            LIMIT ?
        ");

        $stmt->bind_param("i", $limit);
        $stmt->execute();
        $result = $stmt->get_result();

        $commands = [];
        while ($row = $result->fetch_assoc()) {
            $commands[] = [
                'id' => (int) $row['id'],
                'device_id' => (int) $row['device_id'],
                'command' => $row['command_type'],
                'value' => (int) $row['command_value'],
                'source' => $row['source'],
                'executed' => (bool) $row['executed'],
                'timestamp' => $row['timestamp'],
                'executed_at' => $row['executed_at']
            ];
        }

        $stmt->close();
        $conn->close();

        sendSuccess([
            'commands' => $commands,
            'count' => count($commands)
        ]);
    } else {
        sendError('Method not allowed', 405);
        $conn->close();
    }
}

// ============================================
// System Status
// ============================================

function handleSystemStatus($method)
{
    if ($method !== 'GET') {
        sendError('Method not allowed', 405);
        return;
    }

    $conn = getDBConnection();

    // Get system information
    $deviceQuery = "SELECT COUNT(*) as total, 
                    SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online
                    FROM devices";
    $deviceResult = $conn->query($deviceQuery);
    $deviceStats = $deviceResult->fetch_assoc();

    // Get latest reading timestamp
    $latestQuery = "SELECT MAX(timestamp) as latest FROM sensor_readings";
    $latestResult = $conn->query($latestQuery);
    $latest = $latestResult->fetch_assoc();

    // Get total readings count
    $countQuery = "SELECT COUNT(*) as count FROM sensor_readings";
    $countResult = $conn->query($countQuery);
    $readingCount = $countResult->fetch_assoc();

    $conn->close();

    sendSuccess([
        'system_online' => true,
        'devices' => [
            'total' => (int) $deviceStats['total'],
            'online' => (int) $deviceStats['online'],
            'offline' => (int) $deviceStats['total'] - (int) $deviceStats['online']
        ],
        'latest_reading' => $latest['latest'],
        'total_readings' => (int) $readingCount['count'],
        'database' => 'poultry_control',
        'timestamp' => date('Y-m-d H:i:s')
    ]);
}

// ============================================
// Helper Functions
// ============================================

function sendSuccess($data)
{
    http_response_code(200);
    echo json_encode([
        'status' => 'success',
        'data' => $data
    ], JSON_PRETTY_PRINT);
}

function sendError($message, $code = 400)
{
    http_response_code($code);
    echo json_encode([
        'status' => 'error',
        'message' => $message
    ], JSON_PRETTY_PRINT);
}

?>
