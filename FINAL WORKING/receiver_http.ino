/*
 *  3-NODE GATEWAY RECEIVER + MQTT PUBLISHER
 *  + HTTP LED CONTROL
 */

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>

// ------------------ NRF24 SETUP ------------------
RF24 radio(21, 5); // CE, CSN

// Node-specific addresses (5 bytes + null)
const byte nodeAddresses[][6] = {
  "00001",  // Node 1
  "00002",  // Node 2
  "00003"   // Node 3
};

// ------------------ DATA STRUCTS ------------------
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

struct ControlPacket {
  uint8_t node_id;
  uint8_t led_state; // 0 = OFF, 1 = ON
};

SensorPacket incomingPacket;
ControlPacket controlCmd;

// ------------------ WIFI + MQTT ------------------
const char* ssid = "Amoako";
const char* password = "aaaaaaaa";

const char* mqtt_server = "172.20.10.5";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

// ------------------ HTTP SERVER ------------------
WebServer server(80);

// ------------------ WIFI SETUP ------------------
void setup_wifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("Gateway IP Address: ");
  Serial.println(WiFi.localIP());
}

// ------------------ MQTT RECONNECT ------------------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT... ");
    if (client.connect("GatewayNode")) {
      Serial.println("connected!");
    } else {
      delay(3000);
    }
  }
}

// ------------------ HTTP HANDLERS ------------------
void handleRoot() {
  String page =
    "<html><body>"
    "<h2>Gateway LED Control</h2>"
    "<a href=\"/on\"><button>LED ON</button></a><br><br>"
    "<a href=\"/off\"><button>LED OFF</button></a>"
    "</body></html>";

  server.send(200, "text/html", page);
}

void handleLedOn() {
  controlCmd.node_id = 1;
  controlCmd.led_state = 1;

  radio.stopListening();
  radio.write(&controlCmd, sizeof(controlCmd));
  radio.startListening();

  server.send(200, "text/plain", "LED ON command sent");
}

void handleLedOff() {
  controlCmd.node_id = 1;
  controlCmd.led_state = 0;

  radio.stopListening();
  radio.write(&controlCmd, sizeof(controlCmd));
  radio.startListening();

  server.send(200, "text/plain", "LED OFF command sent");
}

void setupWebServer() {
  server.on("/", handleRoot);
  server.on("/on", handleLedOn);
  server.on("/off", handleLedOff);
  server.begin();
  Serial.println("HTTP server started");
}

// ------------------ SETUP ------------------
void setup() {
  Serial.begin(9600);

  radio.begin();
  radio.setPALevel(RF24_PA_MIN);

  // Open reading pipes for all nodes
  radio.openReadingPipe(1, nodeAddresses[0]); // Node 1
  radio.openReadingPipe(2, nodeAddresses[1]); // Node 2
  radio.openReadingPipe(3, nodeAddresses[2]); // Node 3

  radio.startListening();

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  setupWebServer();
}

// ------------------ LOOP ------------------
void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  server.handleClient();

  byte pipeNum;
  if (radio.available(&pipeNum)) {

    radio.read(&incomingPacket, sizeof(incomingPacket));

    Serial.println("====== New Sensor Data ======");
    Serial.print("From Node: ");
    Serial.println(pipeNum);
    Serial.print("Temperature: "); Serial.println(incomingPacket.temperature);
    Serial.print("Humidity: "); Serial.println(incomingPacket.humidity);
    Serial.print("Light Level: "); Serial.println(incomingPacket.lightLevel);
    Serial.println("=============================");

    StaticJsonDocument<256> doc;
    doc["device_id"] = pipeNum;
    doc["temperature"] = incomingPacket.temperature;
    doc["humidity"] = incomingPacket.humidity;
    doc["ldr"] = incomingPacket.lightLevel;
    doc["heater"] = 0;

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    String topic = "poultry/device" + String(pipeNum) + "/sensors";
    client.publish(topic.c_str(), jsonBuffer);
  }

  delay(1500);
}
