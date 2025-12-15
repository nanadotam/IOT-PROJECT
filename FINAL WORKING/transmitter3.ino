//WORKING CODE


/*
* 
*  - Transmitter Code
* 
* Library: TMRh20/RF24, https://github.com/tmrh20/RF24/
*/
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <DHT.h>

RF24 radio(21, 5); // CE, CSN
const uint64_t address = 0xE8E8F0F0C3;

#define LED 2
#define DHTPIN 12
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

int LDR_PIN = 27;  // LDR analog pin

// Data structure to send
struct SensorPacket {
  float temperature;
  float humidity;
  int lightLevel;
};

SensorPacket packet;

void setup() {
  Serial.begin(9600);
  dht.begin();

  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MIN);
  radio.stopListening();

}

void loop() {

  // ---- Read sensors ----
  packet.temperature = dht.readTemperature();
  packet.humidity = dht.readHumidity();
  packet.lightLevel = analogRead(LDR_PIN);  // 0-1023

  // Safety check for DHT read
  if (isnan(packet.temperature) || isnan(packet.humidity)) {
    Serial.println("DHT read error");
    return;
  }

  // ---- Print to Serial Monitor ----
  Serial.print("Temp: "); Serial.print(packet.temperature);
  Serial.print(" | Humidity: "); Serial.print(packet.humidity);
  Serial.print(" | LDR: "); Serial.println(packet.lightLevel);

  // ---- Send packet over RF ----
   radio.write(&packet, sizeof(packet));
   delay(450);
 
  bool ok = radio.write(&packet, sizeof(packet));
if (!ok) {
  Serial.println("NRF24 TX FAILED");
} else {
  Serial.println("NRF24 TX OK");
}

  delay(450);
}