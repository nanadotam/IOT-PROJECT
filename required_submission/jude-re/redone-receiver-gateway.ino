/*
 *  3-NODE GATEWAY RECEIVER + MQTT PUBLISHER
 *  Receives sensor packets from 3 field devices via nRF24
 *  Publishes each node's data to MQTT broker
 */

#include <RF24.h>
#include <SPI.h>
#include <nRF24L01.h>

#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>

// ------------------ NRF24 SETUP ------------------
RF24 radio(5, 17); // CE, CSN

// nRF24 pipe addresses for each node
const byte nodeAddresses[][6] = {
    "NODE1", // Node 1
    "NODE2", // Node 2
    "NODE3"  // Node 3
};

// Must match transmitter struct
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

SensorPacket incomingPacket;

// ------------------ WIFI + MQTT ------------------
const char *ssid = "Amoako";
const char *password = "aaaaaaaa";

const char *mqtt_server = "172.20.10.5"; // CHANGE THIS
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

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
      Serial.print("failed (rc=");
      Serial.print(client.state());
      Serial.println("). Retrying in 3 sec...");
      delay(3000);
    }
  }
}

// ------------------ SETUP ------------------
void setup() {
  Serial.begin(9600);

  // nRF24 Setup
  radio.begin();
  radio.setPALevel(RF24_PA_MIN);
  radio.setDataRate(RF24_250KBPS);
  // Open 3 reading pipes
  radio.openReadingPipe(1, nodeAddresses[0]); // Node 1
  radio.openReadingPipe(2, nodeAddresses[1]); // Node 2
  radio.openReadingPipe(3, nodeAddresses[2]); // Node 3

  radio.startListening();
  Serial.println("Gateway listening for data from 3 nodes...");

  // WiFi & MQTT Setup
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

// ------------------ LOOP ------------------
void loop() {
  if (!client.connected())
    reconnect();
  client.loop();

  byte pipeNum;
  if (radio.available(&pipeNum)) {

    // Read the packet
    radio.read(&incomingPacket, sizeof(incomingPacket));

    // Debug: Print raw bytes received
    Serial.println("\n====== New Sensor Data ======");
    Serial.print("Pipe Number: ");
    Serial.println(pipeNum);
    Serial.print("Packet Size: ");
    Serial.println(sizeof(incomingPacket));

    // Hex dump for debugging
    byte *ptr = (byte *)&incomingPacket;
    Serial.print("Raw Bytes: ");
    for (int i = 0; i < sizeof(incomingPacket); i++) {
      if (ptr[i] < 16)
        Serial.print("0");
      Serial.print(ptr[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    // Print parsed values
    Serial.print("Temperature: ");
    Serial.println(incomingPacket.temperature);
    Serial.print("Humidity: ");
    Serial.println(incomingPacket.humidity);
    Serial.print("Light Level: ");
    Serial.println(incomingPacket.lightLevel);

    // --------------------------------------------------
    // CONVERT PIPE NUMBER TO DEVICE ID
    // Pipe 1 = Device 0, Pipe 2 = Device 1, Pipe 3 = Device 2
    // --------------------------------------------------
    int device_id = pipeNum - 1;

    // --------------------------------------------------
    // BUILD JSON PAYLOAD (MATCHES PYTHON EXPECTATION)
    // --------------------------------------------------
    StaticJsonDocument<256> doc;

    doc["device_id"] = device_id;
    doc["temperature"] = incomingPacket.temperature;
    doc["humidity"] = incomingPacket.humidity;
    doc["ldr"] = incomingPacket.lightLevel;

    // Gateway does not decide heater state
    // Set placeholder (Python ML can override later)
    doc["heater"] = 0;

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    // --------------------------------------------------
    // BUILD CORRECT MQTT TOPIC
    // --------------------------------------------------
    String topic = "poultry/device" + String(device_id) + "/sensors";

    // --------------------------------------------------
    // PUBLISH JSON PAYLOAD
    // --------------------------------------------------
    boolean status = client.publish(topic.c_str(), jsonBuffer);

    if (status) {
      Serial.print("📡 Published to ");
      Serial.println(topic);
      Serial.println(jsonBuffer);
    } else {
      Serial.println("❌ MQTT publish failed");
    }

    Serial.println("=============================\n");
  }

  delay(100); // Reduced delay for faster response
}