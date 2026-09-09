#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>
#include <TinyGPSPlus.h>

// Pins
const int ETHERNET_CS_PIN = 27; 
const int ETHERNET_INT_PIN = 22;
const int GPS_RX_PIN = 33; // ESP32 RX (from GPS TX)
const int GPS_TX_PIN = 32; // ESP32 TX (to GPS RX)
const int GPS_PPS_PIN = 34;

// Objects
TFT_eSPI tft = TFT_eSPI();
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);
EthernetUDP Udp;

const int NTP_PORT = 123;
byte packetBuffer[48];

// Ethernet MAC
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

// PPS Interrupt state
volatile unsigned long lastPPSMillis = 0;
volatile bool ppsTriggered = false;

// Time state
uint32_t currentUnixTime = 0;
unsigned long timeSetMillis = 0;
uint32_t ntpRequestsServed = 0;

void IRAM_ATTR handlePPS() {
  lastPPSMillis = millis();
  ppsTriggered = true;
}

uint32_t getUnixTime(uint16_t year, uint8_t month, uint8_t day, uint8_t h, uint8_t m, uint8_t s) {
  const uint16_t days[12] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
  uint32_t y = year - 1970;
  uint32_t d = days[month - 1] + day - 1 + y * 365 + (y + 1) / 4;
  if (month > 2 && (year % 4 == 0)) {
    d++;
  }
  return ((d * 24 + h) * 60 + m) * 60 + s;
}

uint32_t getSecondsNow() {
  return currentUnixTime + (millis() - timeSetMillis) / 1000;
}

uint32_t getFractionNow() {
  uint32_t ms = (millis() - timeSetMillis) % 1000;
  return ms * 4294967; // 2^32 / 1000
}

void setupDisplay() {
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("CYD NTP Stratum-1");
  tft.println("Initializing...");
}

void updateDisplay() {
  tft.setCursor(10, 40);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.printf("Served: %-8lu\n", ntpRequestsServed);
  
  if (currentUnixTime > 0) {
    tft.setCursor(10, 70);
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.printf("Sync: %02d:%02d:%02d UTC   \n", gps.time.hour(), gps.time.minute(), gps.time.second());
  }
}

void setupEthernet() {
  tft.println("Starting Ethernet...");
  Ethernet.init(ETHERNET_CS_PIN);
  
  if (Ethernet.begin(mac) == 0) {
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.println("Failed to configure DHCP");
  } else {
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.print("IP: ");
    tft.println(Ethernet.localIP());
    Udp.begin(NTP_PORT);
  }
}

void setupGPS() {
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  pinMode(GPS_PPS_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(GPS_PPS_PIN), handlePPS, RISING);
  
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.println("GPS Serial & PPS active");
}

void setup() {
  Serial.begin(115200);
  setupDisplay();
  delay(1000);
  setupEthernet();
  setupGPS();
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(10, 10);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.println("CYD NTP Server Active");
  tft.print("IP: ");
  tft.println(Ethernet.localIP());
}

void handleNTPRequest() {
  int packetSize = Udp.parsePacket();
  if (packetSize >= 48) {
    Udp.read(packetBuffer, 48);
    
    if (currentUnixTime == 0) {
      // No valid time yet, ignore request
      return;
    }
    
    uint8_t version = (packetBuffer[0] >> 3) & 0x07;
    packetBuffer[0] = 0b00000100 | (version << 3); // LI=0, VN=version, Mode=4 (server)
    packetBuffer[1] = 1; // Stratum 1
    packetBuffer[2] = 0; // Poll
    packetBuffer[3] = -20; // Precision
    
    // Root delay & dispersion
    memset(&packetBuffer[4], 0, 8);
    
    // Reference ID "GPS\0"
    packetBuffer[12] = 'G'; packetBuffer[13] = 'P'; packetBuffer[14] = 'S'; packetBuffer[15] = 0;
    
    const uint32_t SEVENTY_YEARS = 2208988800UL;
    uint32_t sec = getSecondsNow() + SEVENTY_YEARS;
    uint32_t frac = getFractionNow();
    
    // Copy Transmit Timestamp to Originate Timestamp
    for (int i = 0; i < 8; i++) {
      packetBuffer[24 + i] = packetBuffer[40 + i];
    }
    
    // Reference timestamp
    uint32_t refSec = currentUnixTime + SEVENTY_YEARS;
    packetBuffer[16] = (refSec >> 24) & 0xFF;
    packetBuffer[17] = (refSec >> 16) & 0xFF;
    packetBuffer[18] = (refSec >> 8) & 0xFF;
    packetBuffer[19] = (refSec) & 0xFF;
    memset(&packetBuffer[20], 0, 4);
    
    // Receive & Transmit timestamp
    packetBuffer[32] = (sec >> 24) & 0xFF;
    packetBuffer[33] = (sec >> 16) & 0xFF;
    packetBuffer[34] = (sec >> 8) & 0xFF;
    packetBuffer[35] = (sec) & 0xFF;
    packetBuffer[36] = (frac >> 24) & 0xFF;
    packetBuffer[37] = (frac >> 16) & 0xFF;
    packetBuffer[38] = (frac >> 8) & 0xFF;
    packetBuffer[39] = (frac) & 0xFF;
    
    memcpy(&packetBuffer[40], &packetBuffer[32], 8);
    
    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.write(packetBuffer, 48);
    Udp.endPacket();
    
    ntpRequestsServed++;
  }
}

void loop() {
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  if (ppsTriggered) {
    ppsTriggered = false;
    if (gps.date.isValid() && gps.time.isValid()) {
      currentUnixTime = getUnixTime(gps.date.year(), gps.date.month(), gps.date.day(), gps.time.hour(), gps.time.minute(), gps.time.second());
      timeSetMillis = lastPPSMillis;
    }
  }
  
  handleNTPRequest();
  
  static unsigned long lastDisplayUpdate = 0;
  if (millis() - lastDisplayUpdate > 1000) {
    lastDisplayUpdate = millis();
    updateDisplay();
  }
  
  Ethernet.maintain();
}
