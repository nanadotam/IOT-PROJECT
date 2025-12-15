/*
 *  SMART POULTRY HEATER CONTROL SYSTEM
 *  3-NODE GATEWAY RECEIVER + MQTT PUBLISHER
 *  
 *  Receives sensor packets from 3 field devices via nRF24
 *  Publishes each node's data to MQTT broker
 *  
 *  MQTT Topics (matches Python config):
 *    - poultry/device1/sensors
 *    - poultry/device2/sensors
 *    - poultry/device3/sensors
 */

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ============================================
// NRF24 CONFIGURATION
// ============================================
RF24 radio(34, 5);  // CE, CSN pins

// nRF24 pipe addresses for each node
const byte nodeAddresses[][6] = {
  "NODE1",  // Node 1 -> Device 1
  "NODE2",  // Node 2 -> Device 2
  "NODE3"   // Node 3 -> Device 3
};

// Sensor data packet structure (must match transmitter)
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

SensorPacket incomingPacket;

// ============================================
// WIFI CONFIGURATION
// ============================================
const char* ssid = "Amoako";
const char* password = "aaaaaaaa";

// ============================================
// MQTT CONFIGURATION
// ============================================
const char* mqtt_server = "172.20.10.5";   // CHANGE TO YOUR MQTT BROKER IP
const int mqtt_port = 1883;
const char* mqtt_client_id = "PoultryGateway";

// MQTT Topics (matches Python config.py)
const char* mqtt_topics[] = {
  "poultry/device1/sensors",  // Node 1
  "poultry/device2/sensors",  // Node 2
  "poultry/device3/sensors"   // Node 3
};

WiFiClient espClient;
PubSubClient client(espClient);

// ============================================
// WIFI SETUP
// ============================================
void setup_wifi() {
  Serial.println("========================================");
  Serial.println("🌐 Connecting to WiFi...");
  Serial.print("SSID: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("Gateway IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi connection failed!");
  }
  Serial.println("========================================");
}

// ============================================
// MQTT RECONNECT
// ============================================
void reconnect() {
  int attempts = 0;
  while (!client.connected() && attempts < 5) {
    Serial.print("📡 Connecting to MQTT broker... ");
    
    if (client.connect(mqtt_client_id)) {
      Serial.println("✅ Connected!");
      Serial.print("Broker: ");
      Serial.print(mqtt_server);
      Serial.print(":");
      Serial.println(mqtt_port);
    } else {
      Serial.print("❌ Failed (rc=");
      Serial.print(client.state());
      Serial.println("). Retrying in 3 sec...");
      delay(3000);
      attempts++;
    }
  }
}

// ============================================
// PUBLISH SENSOR DATA AS JSON
// ============================================
void publishSensorData(int deviceId, SensorPacket data) {
  // Create JSON document
  StaticJsonDocument<200> doc;
  
  doc["device_id"] = deviceId;
  doc["temperature"] = data.temperature;
  doc["humidity"] = data.humidity;
  doc["ldr"] = data.lightLevel;
  doc["heater"] = 0;  // Will be determined by ML model
  
  // Serialize JSON to string
  char jsonBuffer[200];
  serializeJson(doc, jsonBuffer);
  
  // Get the correct topic for this device
  const char* topic = mqtt_topics[deviceId - 1];
  
  // Publish to MQTT
  if (client.publish(topic, jsonBuffer)) {
    Serial.println("✅ Published to MQTT:");
    Serial.print("   Topic: ");
    Serial.println(topic);
    Serial.print("   Data: ");
    Serial.println(jsonBuffer);
  } else {
    Serial.println("❌ Failed to publish to MQTT");
  }
}

// ============================================
// SETUP
// ============================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("╔══════════════════════════════════════════════════════════╗");
  Serial.println("║   🐔 Smart Poultry Heater Control System - Gateway      ║");
  Serial.println("║                                                          ║");
  Serial.println("║   3-Node nRF24 Receiver + MQTT Publisher                ║");
  Serial.println("╚══════════════════════════════════════════════════════════╝");
  Serial.println();

  // ============================================
  // NRF24 SETUP
  // ============================================
  Serial.println("📻 Initializing nRF24L01...");
  if (radio.begin()) {
    Serial.println("✅ nRF24L01 initialized!");
    
    radio.setPALevel(RF24_PA_MIN);
    radio.setDataRate(RF24_250KBPS);
    radio.setChannel(108);
    
    // Open 3 reading pipes (one for each field node)
    radio.openReadingPipe(1, nodeAddresses[0]);  // Node 1
    radio.openReadingPipe(2, nodeAddresses[1]);  // Node 2
    radio.openReadingPipe(3, nodeAddresses[2]);  // Node 3
    
    radio.startListening();
    
    Serial.println("📡 Listening on 3 pipes:");
    Serial.println("   Pipe 1: NODE1 -> poultry/device1/sensors");
    Serial.println("   Pipe 2: NODE2 -> poultry/device2/sensors");
    Serial.println("   Pipe 3: NODE3 -> poultry/device3/sensors");
  } else {
    Serial.println("❌ nRF24L01 initialization failed!");
  }
  Serial.println();

  // ============================================
  // WIFI & MQTT SETUP
  // ============================================
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  Serial.println("\n🚀 Gateway ready!");
  Serial.println("Waiting for sensor data from field nodes...\n");
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Check for incoming nRF24 data
  byte pipeNum;
  if (radio.available(&pipeNum)) {
    
    // Read the sensor packet
    radio.read(&incomingPacket, sizeof(incomingPacket));
    
    // Calculate device ID (pipeNum is 1, 2, or 3)
    int deviceId = pipeNum;
    
    // Display received data
    Serial.println("════════════════════════════════════════");
    Serial.print("📥 Data received from Node ");
    Serial.print(pipeNum);
    Serial.print(" (Device ");
    Serial.print(deviceId);
    Serial.println(")");
    Serial.println("────────────────────────────────────────");
    Serial.print("🌡️  Temperature: ");
    Serial.print(incomingPacket.temperature);
    Serial.println(" °C");
    Serial.print("💧 Humidity:    ");
    Serial.print(incomingPacket.humidity);
    Serial.println(" %");
    Serial.print("💡 Light Level: ");
    Serial.print(incomingPacket.lightLevel);
    Serial.println(" %");
    Serial.println("────────────────────────────────────────");
    
    // Publish to MQTT in JSON format
    publishSensorData(deviceId, incomingPacket);
    
    Serial.println("════════════════════════════════════════\n");
  }
  
  // Small delay to prevent overwhelming the system
  delay(100);
}
