/*
 * ═══════════════════════════════════════════════════════════
 * ESP32 GATEWAY CODE - Part B (Based on Working Version)
 * ═══════════════════════════════════════════════════════════
 * Upload this code to ONE ESP32 that acts as the gateway
 *
 * Features:
 * - Receives sensor data from field devices via nRF24L01
 * - Publishes data to local MQTT broker
 * - Hosts web interface for device control
 * - Sends commands back to field devices
 * ═══════════════════════════════════════════════════════════
 */

#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <RF24.h>
#include <SPI.h>
#include <WebServer.h>
#include <WiFi.h>
#include <nRF24L01.h>

// ================= PIN DEFINITIONS =================
#define CE_PIN 21
#define CSN_PIN 5

// ================= NETWORK CONFIGURATION =================
const char *ssid = "Amoako";       // CHANGE THIS
const char *password = "aaaaaaaa"; // CHANGE THIS

// Local MQTT Broker
const char *mqtt_server = "172.20.10.5"; // CHANGE to your MQTT broker IP
const int mqtt_port = 1883;

// ================= RADIO ADDRESSES =================
const uint64_t pipeAddresses[] = {
    0xA1A1A1A101LL, // Node 1
    0xA1A1A1A102LL, // Node 2
    0xA1A1A1A103LL, // Node 3
    0xA1A1A1A104LL, // Node 4
    0xA1A1A1A105LL, // Node 5
    0xA1A1A1A106LL  // Node 6
};

// ================= DATA STRUCTURES =================
struct DataPackage {
  int node_id;
  float temp;
  float hum;
  int light;
};
DataPackage data;

struct CommandPackage {
  int node_id;
  int device_id;
  bool state;
};
CommandPackage cmd;

// ================= NODE STATUS TRACKING =================
struct NodeStatus {
  bool active;
  float lastTemp;
  float lastHum;
  int lastLight;
  unsigned long lastSeen;
  bool deviceState;
};
NodeStatus nodes[7]; // Index 0 unused, 1-6 for nodes

// ================= OBJECTS =================
RF24 radio(CE_PIN, CSN_PIN);
WiFiClient espClient;
PubSubClient mqttClient(espClient);
WebServer server(80);

// ================= STATISTICS =================
int packetsReceived = 0;
int mqttPublished = 0;
int commandsSent = 0;

// ================= WIFI SETUP =================
void setup_wifi() {
  Serial.println("\n========================================");
  Serial.println("WIFI SETUP");
  Serial.println("========================================");
  Serial.printf("Connecting to: %s\n", ssid);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(400);
    Serial.print(".");
    attempts++;

    if (attempts % 10 == 0) {
      Serial.printf("\nStatus code: %d ", WiFi.status());
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("Gateway IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi Connection Failed!");
    Serial.printf("Status Code: %d\n", WiFi.status());
    Serial.println("\nPossible issues:");
    Serial.println("1. Wrong SSID or password");
    Serial.println("2. Router too far away");
    Serial.println("3. 5GHz network (ESP32 needs 2.4GHz)");
  }
  Serial.println("========================================\n");
}

// ================= MQTT SETUP =================
void reconnect() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected - cannot connect to MQTT");
    return;
  }

  while (!mqttClient.connected()) {
    Serial.println("\n========================================");
    Serial.println("MQTT SETUP");
    Serial.println("========================================");
    Serial.printf("Broker: %s:%d\n", mqtt_server, mqtt_port);
    Serial.print("Connecting... ");

    String clientId = "GatewayNode-" + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("Connected!");
      mqttClient.subscribe("poultry/commands/#");
      Serial.println("Subscribed to: poultry/commands/#");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(mqttClient.state());
      Serial.println("\nRetrying in 3 seconds...");
      delay(3000);
    }
    Serial.println("========================================\n");
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  Serial.printf("\nMQTT Message on [%s]: ", topic);

  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Parse command format: "nodeId,deviceId,state"
  int firstComma = message.indexOf(',');
  int secondComma = message.indexOf(',', firstComma + 1);

  if (firstComma > 0 && secondComma > 0) {
    int nodeId = message.substring(0, firstComma).toInt();
    int deviceId = message.substring(firstComma + 1, secondComma).toInt();
    int state = message.substring(secondComma + 1).toInt();

    sendCommandToNode(nodeId, deviceId, state);
  }
}

// ================= RADIO SETUP =================
void setupRadio() {
  Serial.println("\n========================================");
  Serial.println("RADIO SETUP");
  Serial.println("========================================");
  Serial.println("Initializing nRF24L01...");

  if (!radio.begin()) {
    Serial.println("Radio hardware not responding!");
    Serial.println("Check wiring:");
    Serial.println("  CE  → GPIO 21");
    Serial.println("  CSN → GPIO 5");
    Serial.println("  SCK → GPIO 18");
    Serial.println("  MOSI→ GPIO 23");
    Serial.println("  MISO→ GPIO 19");
    Serial.println("  VCC → 3.3V (NOT 5V!)");
    Serial.println("  GND → GND");
    while (1)
      delay(1000);
  }

  radio.setPALevel(RF24_PA_LOW);
  radio.setChannel(108);
  radio.setDataRate(RF24_1MBPS);
  radio.setPayloadSize(max(sizeof(DataPackage), sizeof(CommandPackage)));
  radio.setAutoAck(true);

  // Open reading pipes for all 6 nodes
  for (int i = 0; i < 6; i++) {
    radio.openReadingPipe(i + 1, pipeAddresses[i]);
    Serial.printf("  Pipe %d: 0x%llX\n", i + 1, pipeAddresses[i]);
  }

  radio.startListening();

  Serial.println("Radio configured and listening");
  Serial.println("  Power: LOW");
  Serial.println("  Channel: 108");
  Serial.println("  Data Rate: 1MBPS");
  Serial.println("========================================\n");
}

// ================= RADIO DATA HANDLING =================
void checkRadioData() {
  uint8_t pipeNum;

  if (radio.available(&pipeNum)) {
    radio.read(&data, sizeof(data));
    packetsReceived++;

    Serial.println("\n┌─────────────────────────────────────┐");
    Serial.printf("│  DATA FROM NODE %d (Pipe %d)         │\n", data.node_id,
                  pipeNum);
    Serial.println("└─────────────────────────────────────┘");
    Serial.printf("Temperature: %.1f °C\n", data.temp);
    Serial.printf("Humidity:    %.1f %%\n", data.hum);
    Serial.printf("Light Level:  %d\n", data.light);

    // Update node status
    nodes[data.node_id].active = true;
    nodes[data.node_id].lastTemp = data.temp;
    nodes[data.node_id].lastHum = data.hum;
    nodes[data.node_id].lastLight = data.light;
    nodes[data.node_id].lastSeen = millis();

    // Publish to MQTT
    publishToMQTT(data.node_id, data.temp, data.hum, data.light);
  }
}

// ================= MQTT PUBLISHING =================
void publishToMQTT(int nodeId, float temp, float hum, int light) {
  if (!mqttClient.connected())
    return;

  // Create JSON document
  StaticJsonDocument<256> doc;
  doc["node_id"] = nodeId;
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["light"] = light;
  doc["device_state"] = nodes[nodeId].deviceState;
  doc["timestamp"] = millis();

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);

  // Publish to main topic
  String topic = "poultry/node" + String(nodeId) + "/data";
  mqttClient.publish(topic.c_str(), jsonBuffer);

  // Also publish individual readings
  char payload[50];

  sprintf(payload, "%.1f", temp);
  topic = "poultry/node" + String(nodeId) + "/temperature";
  mqttClient.publish(topic.c_str(), payload);

  sprintf(payload, "%.1f", hum);
  topic = "poultry/node" + String(nodeId) + "/humidity";
  mqttClient.publish(topic.c_str(), payload);

  sprintf(payload, "%d", light);
  topic = "poultry/node" + String(nodeId) + "/light";
  mqttClient.publish(topic.c_str(), payload);

  mqttPublished++;
  Serial.println("Published to MQTT");
}

// ================= COMMAND SENDING =================
void sendCommandToNode(int nodeId, int deviceId, bool state) {
  if (nodeId < 1 || nodeId > 6) {
    Serial.println("Invalid node ID");
    return;
  }

  Serial.printf("\nSending command to Node %d...\n", nodeId);
  Serial.printf("   Device: %d, State: %s\n", deviceId, state ? "ON" : "OFF");

  cmd.node_id = nodeId;
  cmd.device_id = deviceId;
  cmd.state = state;

  // Stop listening to transmit
  radio.stopListening();
  delay(5);

  // Open writing pipe for target node
  radio.openWritingPipe(pipeAddresses[nodeId - 1]);

  bool success = radio.write(&cmd, sizeof(cmd));

  commandsSent++;

  if (success) {
    Serial.println("Command sent successfully");
    nodes[nodeId].deviceState = state;
  } else {
    Serial.println("Command transmission failed");
  }

  // Return to listening mode
  delay(5);
  radio.startListening();
}

// ================= NODE STATUS UPDATE =================
void updateNodeStatus() {
  unsigned long currentTime = millis();

  for (int i = 1; i <= 6; i++) {
    if (nodes[i].active && (currentTime - nodes[i].lastSeen > 30000)) {
      nodes[i].active = false; // Mark as inactive after 30 seconds
      Serial.printf("Node %d marked as inactive (timeout)\n", i);
    }
  }
}

// ================= WEB SERVER SETUP =================
void setupWebServer() {
  server.on("/", handleRoot);
  server.on("/control", HTTP_POST, handleControl);
  server.on("/status", handleStatus);
  server.on("/node1/on", []() {
    sendCommandToNode(1, 1, true);
    server.send(200, "text/plain", "ON");
  });
  server.on("/node1/off", []() {
    sendCommandToNode(1, 1, false);
    server.send(200, "text/plain", "OFF");
  });
  server.on("/node2/on", []() {
    sendCommandToNode(2, 1, true);
    server.send(200, "text/plain", "ON");
  });
  server.on("/node2/off", []() {
    sendCommandToNode(2, 1, false);
    server.send(200, "text/plain", "OFF");
  });
  server.on("/node3/on", []() {
    sendCommandToNode(3, 1, true);
    server.send(200, "text/plain", "ON");
  });
  server.on("/node3/off", []() {
    sendCommandToNode(3, 1, false);
    server.send(200, "text/plain", "OFF");
  });

  server.begin();
  Serial.println("\nHTTP server started on port 80");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("Access web interface at: http://%s\n",
                  WiFi.localIP().toString().c_str());
  }
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head>";
  html +=
      "<meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<meta http-equiv='refresh' content='10'>"; // Auto-refresh every 10s
  html += "<style>";
  html += "body{font-family:Arial;margin:20px;background:#f0f0f0}";
  html += ".container{max-width:800px;margin:auto;background:white;padding:"
          "20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}";
  html += "h1{color:#333;text-align:center;margin-bottom:10px}";
  html += ".subtitle{text-align:center;color:#666;margin-bottom:30px}";
  html += ".node{background:#f9f9f9;padding:15px;margin:15px "
          "0;border-radius:5px;border-left:4px solid #4CAF50}";
  html += ".node.inactive{border-left-color:#ccc;opacity:0.6}";
  html += ".node-header{display:flex;justify-content:space-between;align-items:"
          "center;margin-bottom:10px}";
  html += ".status{display:inline-block;padding:5px "
          "10px;border-radius:3px;font-size:12px;font-weight:bold}";
  html += ".status.active{background:#4CAF50;color:white}";
  html += ".status.inactive{background:#ccc;color:#666}";
  html += ".data{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;"
          "margin:10px 0}";
  html += ".data-item{text-align:center;padding:10px;background:white;border-"
          "radius:5px;border:1px solid #ddd}";
  html += ".data-label{font-size:12px;color:#666;margin-bottom:5px}";
  html += ".data-value{font-size:20px;font-weight:bold;color:#333}";
  html += ".controls{text-align:center;margin-top:15px;padding-top:15px;border-"
          "top:1px solid #ddd}";
  html += ".btn{padding:12px "
          "24px;margin:5px;border:none;border-radius:5px;cursor:pointer;font-"
          "size:16px;font-weight:bold;transition:0.3s}";
  html += ".btn-on{background:#4CAF50;color:white}";
  html += ".btn-on:hover{background:#45a049}";
  html += ".btn-off{background:#f44336;color:white}";
  html += ".btn-off:hover{background:#da190b}";
  html += ".device-status{display:inline-block;margin-left:15px;padding:5px "
          "10px;border-radius:3px;font-size:14px}";
  html +=
      ".device-on{background:#e8f5e9;color:#2e7d32;border:1px solid #4CAF50}";
  html +=
      ".device-off{background:#ffebee;color:#c62828;border:1px solid #f44336}";
  html += ".stats{background:#e3f2fd;padding:15px;border-radius:5px;margin-top:"
          "20px}";
  html += ".stats h3{margin-top:0;color:#1976d2}";
  html +=
      ".stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}";
  html += ".stat-item{background:white;padding:10px;border-radius:5px;text-"
          "align:center}";
  html += "</style>";
  html += "</head><body>";
  html += "<div class='container'>";
  html += "<h1>Poultry Farm Control System</h1>";
  html +=
      "<p class='subtitle'>Gateway IP: " + WiFi.localIP().toString() + "</p>";

  // Display each node
  for (int i = 1; i <= 6; i++) {
    html += "<div class='node " +
            String(nodes[i].active ? "active" : "inactive") + "'>";
    html += "<div class='node-header'>";
    html += "<h3 style='margin:0'>Node " + String(i) + "</h3>";
    html += "<span class='status " +
            String(nodes[i].active ? "active" : "inactive") + "'>";
    html += nodes[i].active ? "ACTIVE" : "OFFLINE";
    html += "</span></div>";

    if (nodes[i].active) {
      html += "<div class='data'>";
      html += "<div class='data-item'><div "
              "class='data-label'>Temperature</div><div class='data-value'>" +
              String(nodes[i].lastTemp, 1) + "°C</div></div>";
      html += "<div class='data-item'><div "
              "class='data-label'>Humidity</div><div class='data-value'>" +
              String(nodes[i].lastHum, 1) + "%</div></div>";
      html += "<div class='data-item'><div class='data-label'>Light "
              "Level</div><div class='data-value'>" +
              String(nodes[i].lastLight) + "</div></div>";
      html += "</div>";

      html += "<div class='controls'>";
      html += "<button class='btn btn-on' onclick='fetch(\"/node" + String(i) +
              "/on\").then(()=>location.reload())'>Turn ON</button>";
      html += "<button class='btn btn-off' onclick='fetch(\"/node" + String(i) +
              "/off\").then(()=>location.reload())'>Turn OFF</button>";
      html += "<span class='device-status " +
              String(nodes[i].deviceState ? "device-on" : "device-off") + "'>";
      html += "Device: " + String(nodes[i].deviceState ? "ON" : "OFF");
      html += "</span></div>";
    } else {
      html += "<p style='color:#999;text-align:center;margin:20px 0'>No data "
              "received from this node</p>";
    }

    html += "</div>";
  }

  // Statistics
  html += "<div class='stats'>";
  html += "<h3>System Statistics</h3>";
  html += "<div class='stat-grid'>";
  html += "<div class='stat-item'><strong>Packets Received</strong><br>" +
          String(packetsReceived) + "</div>";
  html += "<div class='stat-item'><strong>MQTT Published</strong><br>" +
          String(mqttPublished) + "</div>";
  html += "<div class='stat-item'><strong>Commands Sent</strong><br>" +
          String(commandsSent) + "</div>";
  html += "<div class='stat-item'><strong>Uptime</strong><br>" +
          String(millis() / 1000) + "s</div>";
  html += "</div></div>";

  html += "<p "
          "style='text-align:center;color:#999;margin-top:20px;font-size:12px'>"
          "Page auto-refreshes every 10 seconds</p>";
  html += "</div></body></html>";

  server.send(200, "text/html", html);
}

void handleControl() {
  if (server.hasArg("node") && server.hasArg("device") &&
      server.hasArg("state")) {
    int nodeId = server.arg("node").toInt();
    int deviceId = server.arg("device").toInt();
    bool state = server.arg("state").toInt();

    sendCommandToNode(nodeId, deviceId, state);

    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Missing parameters");
  }
}

void handleStatus() {
  StaticJsonDocument<1024> doc;
  JsonArray nodesArray = doc.createNestedArray("nodes");

  for (int i = 1; i <= 6; i++) {
    JsonObject node = nodesArray.createNestedObject();
    node["id"] = i;
    node["active"] = nodes[i].active;
    node["temp"] = nodes[i].lastTemp;
    node["hum"] = nodes[i].lastHum;
    node["light"] = nodes[i].lastLight;
    node["device"] = nodes[i].deviceState;
  }

  doc["packets_received"] = packetsReceived;
  doc["mqtt_published"] = mqttPublished;
  doc["commands_sent"] = commandsSent;
  doc["uptime"] = millis() / 1000;

  String json;
  serializeJson(doc, json);
  server.send(200, "application/json", json);
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n╔════════════════════════════════════════╗");
  Serial.println("║   ESP32 GATEWAY - LOCAL NETWORK        ║");
  Serial.println("║        Based on Working Version        ║");
  Serial.println("╚════════════════════════════════════════╝\n");

  // Initialize node status
  for (int i = 1; i <= 6; i++) {
    nodes[i].active = false;
    nodes[i].lastSeen = 0;
    nodes[i].deviceState = false;
    nodes[i].lastTemp = 0;
    nodes[i].lastHum = 0;
    nodes[i].lastLight = 0;
  }

  // Initialize WiFi
  setup_wifi();

  // Initialize MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);
  reconnect();

  // Initialize Radio
  setupRadio();

  // Setup Web Server
  setupWebServer();

  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║         GATEWAY READY!                 ║");
  Serial.println("╚════════════════════════════════════════╝\n");
}

// ================= MAIN LOOP =================
void loop() {
  // Handle WiFi reconnection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    setup_wifi();
  }

  // Handle MQTT
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // Handle Web Server
  server.handleClient();

  // Check for incoming radio data
  checkRadioData();

  // Update node activity status (check every loop)
  static unsigned long lastStatusCheck = 0;
  if (millis() - lastStatusCheck > 5000) { // Check every 5 seconds
    updateNodeStatus();
    lastStatusCheck = millis();
  }
}