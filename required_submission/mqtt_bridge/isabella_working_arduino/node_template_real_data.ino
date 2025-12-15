/*
 * ==========================================================
 * ESP32 FIELD DEVICE - TRANSMITTER NODE (REAL SENSOR DATA)
 * ==========================================================
 */

#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <DHT.h>

// ================= CONFIG =================
#define NODE_ID     1          // CHANGE PER NODE (1–6)
#define CE_PIN      21
#define CSN_PIN     5
#define LED_PIN     2

#define DHTPIN      14
#define DHTTYPE     DHT11
#define LDR_PIN     34

// ================= RADIO ADDRESSES =================
const uint64_t pipeAddresses[] = {
  0xA1A1A1A101LL,
  0xA1A1A1A102LL,
  0xA1A1A1A103LL,
  0xA1A1A1A104LL,
  0xA1A1A1A105LL,
  0xA1A1A1A106LL
};

// ================= DATA STRUCTURES =================
struct DataPackage {
  int node_id;
  float temp;
  float hum;
  int light;
};

struct CommandPackage {
  int node_id;
  int device_id;
  bool state;
};

DataPackage data;
CommandPackage cmd;

// ================= OBJECTS =================
RF24 radio(CE_PIN, CSN_PIN);
DHT dht(DHTPIN, DHTTYPE);

// ================= TIMING =================
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL = 3000;

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("\n==============================");
  Serial.printf("FIELD NODE %d STARTING\n", NODE_ID);
  Serial.println("==============================");

  dht.begin();

  if (!radio.begin()) {
    Serial.println("❌ nRF24L01 not responding");
    while (1);
  }

  radio.setPALevel(RF24_PA_LOW);
  radio.setChannel(108);
  radio.setDataRate(RF24_1MBPS);
  radio.setPayloadSize(max(sizeof(DataPackage), sizeof(CommandPackage)));
  radio.setAutoAck(true);

  radio.openWritingPipe(pipeAddresses[NODE_ID - 1]);
  radio.openReadingPipe(1, pipeAddresses[NODE_ID - 1]);

  radio.startListening();

  Serial.println("✓ Radio and sensors ready");
}

// ================= LOOP =================
void loop() {
  receiveCommand();
  sendSensorData();
}

// ================= SEND DATA =================
void sendSensorData() {
  if (millis() - lastSend < SEND_INTERVAL) return;
  lastSend = millis();

  float temperature = dht.readTemperature();
  float humidity    = dht.readHumidity();
  int ldrRaw        = analogRead(LDR_PIN);

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠️ DHT read failed");
    return;
  }

  int lightLevel = map(ldrRaw, 0, 4095, 0, 100);
  lightLevel = constrain(lightLevel, 0, 100);

  data.node_id = NODE_ID;
  data.temp = temperature;
  data.hum = humidity;
  data.light = lightLevel;

  Serial.println("\n📤 Sending Sensor Data");
  Serial.printf("🌡️ %.1f °C | 💧 %.1f %% | 💡 %d\n",
                data.temp, data.hum, data.light);

  radio.stopListening();
  delay(5);

  bool success = radio.write(&data, sizeof(data));

  Serial.println(success ? "✓ Data sent" : "✗ Send failed");

  delay(5);
  radio.startListening();
}

// ================= RECEIVE COMMAND =================
void receiveCommand() {
  if (!radio.available()) return;

  radio.read(&cmd, sizeof(cmd));

  if (cmd.node_id != NODE_ID) return;

  Serial.println("\n📥 Command Received");
  Serial.printf("Device %d → %s\n",
                cmd.device_id,
                cmd.state ? "ON" : "OFF");

  digitalWrite(LED_PIN, cmd.state ? HIGH : LOW);
}
