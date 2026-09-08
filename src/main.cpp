#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <Ethernet.h>

// Initialize the TFT display
TFT_eSPI tft = TFT_eSPI();

// Ethernet configuration (Assuming SPI Ethernet like W5500)
// You may need to change these pins based on how you wire the Ethernet module
// to the CYD, since the CYD already uses several SPI pins.
const int ETHERNET_CS_PIN = 22; 
const int ETHERNET_RST_PIN = 27;

// MAC address for the Ethernet module
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

void setupDisplay() {
  tft.init();
  tft.setRotation(1); // Landscape
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("CYD Sandbox");
  tft.println("Initializing...");
}

void setupEthernet() {
  tft.println("Starting Ethernet...");
  
  // Optional: Reset the Ethernet module
  pinMode(ETHERNET_RST_PIN, OUTPUT);
  digitalWrite(ETHERNET_RST_PIN, LOW);
  delay(10);
  digitalWrite(ETHERNET_RST_PIN, HIGH);
  delay(100);

  // Initialize Ethernet with DHCP
  Ethernet.init(ETHERNET_CS_PIN);
  
  if (Ethernet.begin(mac) == 0) {
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.println("Failed to configure Ethernet using DHCP");
    // Check for Ethernet hardware present
    if (Ethernet.hardwareStatus() == EthernetNoHardware) {
      tft.println("Ethernet shield was not found.");
    } else if (Ethernet.linkStatus() == LinkOFF) {
      tft.println("Ethernet cable is not connected.");
    }
  } else {
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.println("Ethernet connected!");
    tft.print("IP: ");
    tft.println(Ethernet.localIP());
  }
}

void setup() {
  Serial.begin(115200);
  
  // Set up the display
  setupDisplay();
  
  delay(2000); // Give the user time to read the screen
  
  // Set up the Ethernet
  setupEthernet();
}

void loop() {
  // Main logic for the sandbox
  // e.g., handling network requests, updating display
  
  switch (Ethernet.maintain()) {
    case 1:
      // renewed fail
      Serial.println("Error: renewed fail");
      break;
    case 2:
      // renewed success
      Serial.println("Renewed success");
      Serial.print("My IP address: ");
      Serial.println(Ethernet.localIP());
      break;
    case 3:
      // rebind fail
      Serial.println("Error: rebind fail");
      break;
    case 4:
      // rebind success
      Serial.println("Rebind success");
      Serial.print("My IP address: ");
      Serial.println(Ethernet.localIP());
      break;
    default:
      // nothing happened
      break;
  }
  
  delay(1000);
}
