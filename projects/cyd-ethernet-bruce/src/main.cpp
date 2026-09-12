#ifdef ARDUINO
#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <Ethernet.h>

TFT_eSPI tft = TFT_eSPI();

const int ETHERNET_CS_PIN = 27; 
const int ETHERNET_INT_PIN = 22; 

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
bool ethernetConnected = false;

void setupDisplay() {
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("CYD Sandbox");
  tft.println("Initializing...");
}

void setupEthernet() {
  Serial.println("Starting Ethernet configuration...");
  
  pinMode(ETHERNET_CS_PIN, OUTPUT);
  digitalWrite(ETHERNET_CS_PIN, HIGH);
  
  // Pull SD card CS high just in case it's sharing the bus and interfering
  pinMode(5, OUTPUT);
  digitalWrite(5, HIGH);
  
  delay(250); 
  
  // Initialize the SPI bus for Ethernet using the ACTUAL SD Card slot pins
  // SCK=18, MISO=19, MOSI=23
  SPI.begin(18, 19, 23, -1);
  
  // --- RAW SPI DIAGNOSTIC TEST ---
  Serial.println("Running low-speed SPI diagnostic on W5500...");
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(ETHERNET_CS_PIN, LOW);
  SPI.transfer(0x00); // High address byte
  SPI.transfer(0x39); // Low address byte (0x0039 = Version Register)
  SPI.transfer(0x00); // Control byte (Read, Block 0)
  byte version = SPI.transfer(0x00); // Read data
  digitalWrite(ETHERNET_CS_PIN, HIGH);
  SPI.endTransaction();
  
  Serial.print("W5500 Version Register (Expected 0x04): 0x");
  if (version < 0x10) Serial.print("0");
  Serial.println(version, HEX);
  
  if (version == 0x00 || version == 0xFF) {
    Serial.println("DIAGNOSTIC FAILED: The W5500 is not responding at all.");
    Serial.println("This is 100% a physical issue (crossed wires, floating RST, or bad power).");
  } else if (version == 0x04) {
    Serial.println("DIAGNOSTIC PASSED: SPI is working! The issue is library speed/config.");
  } else {
    Serial.println("DIAGNOSTIC UNKNOWN: Received garbage data. Check wire length/noise.");
  }
  // -------------------------------

  Ethernet.init(ETHERNET_CS_PIN);
  
  Serial.println("Calling Ethernet.begin()...");
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    
    if (Ethernet.hardwareStatus() == EthernetNoHardware) {
      Serial.println("Error: Ethernet shield was not found. (SPI/Wiring issue)");
    } else if (Ethernet.linkStatus() == LinkOFF) {
      Serial.println("Error: Ethernet cable is not connected.");
    }
  } else {
    ethernetConnected = true;
    Serial.println("Ethernet connected successfully!");
    Serial.print("IP: ");
    Serial.println(Ethernet.localIP());
  }
}

void setup() {
  Serial.begin(115200);
  while(!Serial) { delay(10); }
  
  Serial.println("\n--- Booting CYD Sandbox ---");
  
  // 1. Initialize Ethernet FIRST before the TFT grabs the SPI bus
  setupEthernet();
  
  // 2. Now initialize the TFT
  setupDisplay();
  
  if (ethernetConnected) {
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.println("Ethernet connected!");
    tft.print("IP: ");
    tft.println(Ethernet.localIP());
  } else {
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.println("Ethernet Failed!");
  }
  
  delay(1000);
}

void loop() {
  if (ethernetConnected) {
    switch (Ethernet.maintain()) {
      case 1:
        Serial.println("Error: renewed fail");
        break;
      case 2:
        Serial.println("Renewed success");
        break;
      case 3:
        Serial.println("Error: rebind fail");
        break;
      case 4:
        Serial.println("Rebind success");
        break;
      default:
        break;
    }
  } else {
    // If we never connected, just wait and maybe we can try restarting or alerting the user
    delay(5000);
    Serial.println("Waiting for Ethernet connection...");
  }
  
  delay(1000);
}
#endif
