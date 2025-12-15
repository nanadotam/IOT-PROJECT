/*
 *  TRANSMITTER NODE 0 (Device ID 0)
 *  Sends sensor data via nRF24L01+ to Gateway
 *  Uses NODE1 address (pipe 1) for device_id 0
 */

#include <DHT.h>
#include <RF24.h>
#include <SPI.h>
#include <nRF24L01.h>

// ------------------ NRF24 SETUP ------------------
RF24 radio(5, 17);               // CE, CSN pins for NRF24
const byte address[6] = "NODE1"; // Device 0 uses NODE1 (pipe 1)

// ------------------ DHT22 SETUP ------------------
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ------------------ LDR SETUP ------------------
int LDR_PIN = 15; // LDR analog pin

// ------------------ DATA STRUCTURE ------------------
// MUST MATCH RECEIVER EXACTLY
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

SensorPacket packet;

// ------------------ SETUP ------------------
void setup() {
  Serial.begin(9600);
  dht.begin();

  // Initialize nRF24
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MIN);   // Match receiver
  radio.setDataRate(RF24_250KBPS); // Match receiver
  radio.stopListening();

  Serial.println("=================================");
  Serial.println("  TRANSMITTER NODE 0 (Device 0)");
  Serial.println("  Address: NODE1");
  Serial.println("=================================");
  delay(1000);
}

// ------------------ LOOP ------------------
void loop() {

  // ---- Read sensors ----
  packet.temperature = dht.readTemperature();
  packet.humidity = dht.readHumidity();
  packet.lightLevel = analogRead(LDR_PIN); // 0-4095 on ESP32

  // Safety check for DHT read
  if (isnan(packet.temperature) || isnan(packet.humidity)) {
    Serial.println("❌ DHT read error");
    delay(2000);
    return;
  }

  // ---- Print to Serial Monitor ----
  Serial.print("Temp: ");
  Serial.print(packet.temperature, 2);
  Serial.print(" | Humidity: ");
  Serial.print(packet.humidity, 2);
  Serial.print(" | LDR: ");
  Serial.println(packet.lightLevel);

  // ---- Send packet over RF ----
  bool sent = radio.write(&packet, sizeof(packet));

  if (sent) {
    Serial.println("✅ TX OK");
  } else {
    Serial.println("❌ TX FAIL");
  }

  delay(1500);
}
