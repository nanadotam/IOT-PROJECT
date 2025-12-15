/*
 *  3-NODE GATEWAY RECEIVER + MQTT PUBLISHER
 *  Receives sensor packets from 3 field devices via nRF24
 *  Publishes each node's data to MQTT broker
 */

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>


// ------------------ NRF24 SETUP ------------------

RF24 radio(21, 5); // CE, CSN

// nRF24 pipe addresses for each node
// const byte nodeAddresses[][6] = {
//   "NODE1",  // Node 1
//   "NODE2",  // Node 2
//   "NODE3"   // Node 3
// };

const byte address[6] = "00001";

// Must match transmitter struct
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

SensorPacket incomingPacket;

// ------------------ WIFI + MQTT ------------------
const char* ssid = "Amoako";
const char* password = "aaaaaaaa";

const char* mqtt_server = "172.20.10.5";   // CHANGE THIS
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
  Serial.begin(9600);
  radio.begin();
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_MIN);
  radio.startListening();

  // WiFi & MQTT Setup
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

// ------------------ LOOP ------------------
// ------------------ LOOP ------------------
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

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

    // --------------------------------------------------
    // BUILD JSON PAYLOAD (MATCHES PYTHON EXPECTATION)
    // --------------------------------------------------
    StaticJsonDocument<256> doc;

    doc["device_id"]   = pipeNum;
    doc["temperature"] = incomingPacket.temperature;
    doc["humidity"]    = incomingPacket.humidity;
    doc["ldr"]         = incomingPacket.lightLevel;

    // Gateway does not decide heater state
    // Set placeholder (Python ML can override later)
    doc["heater"] = 0;

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    // --------------------------------------------------
    // BUILD CORRECT MQTT TOPIC
    // --------------------------------------------------
    String topic = "poultry/device" + String(pipeNum) + "/sensors";

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
  }

  delay(1500);
}