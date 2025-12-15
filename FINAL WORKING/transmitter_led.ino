#include <DHT.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ------------------ RF24 ------------------
#define CE_PIN   21
#define CSN_PIN  17
RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// ------------------ DATA STRUCT ------------------
struct ControlPacket {
  uint8_t node_id;
  uint8_t led_state;
};

// ------------------ PINS ------------------
#define DHTPIN   12
#define DHTTYPE  DHT22
#define LDR_PIN  27
#define LED_PIN  2
#define NODE_ID  1

DHT dht(DHTPIN, DHTTYPE);

// ------------------ UTILITY ------------------
float mapLDRToLight(int v) {
  return constrain(map(v, 0, 4095, 0, 100), 0, 100);
}

// ------------------ SETUP ------------------
void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  dht.begin();

  radio.begin();
  radio.openWritingPipe(address);
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_MIN);
  radio.stopListening();

  Serial.println("Node ready");
}

// ------------------ CONTROL RECEIVE ------------------
void checkForControlPacket() {
  if (radio.available()) {
    ControlPacket cmd;
    radio.read(&cmd, sizeof(cmd));

    if (cmd.node_id == NODE_ID) {
      digitalWrite(LED_PIN, cmd.led_state ? HIGH : LOW);
      Serial.println(cmd.led_state ? "LED ON" : "LED OFF");
    }
  }
}

// ------------------ LOOP ------------------
void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  float l = mapLDRToLight(analogRead(LDR_PIN));

  if (isnan(t) || isnan(h)) return;

  char payload[32];
  snprintf(payload, sizeof(payload), "%d,%.1f,%.1f,%.1f", NODE_ID, t, h, l);

  radio.stopListening();
  bool ok = radio.write(payload, strlen(payload) + 1);

  Serial.println(ok ? "TX OK" : "TX FAIL");

  radio.startListening();
  unsigned long start = millis();
  while (millis() - start < 150) {
    checkForControlPacket();
  }

  delay(3000);
}
