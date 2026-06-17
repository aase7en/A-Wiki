---
tags: [iot, esp32, lora, sensor, monitoring, web]
type: source
title: "ESP32 LoRa Sensor Monitoring with Web Server (Long Range Communication)"
slug: esp32-lora-sensor-monitoring-with-web-server-long-range-communication
date_ingested: 2026-05-24
original_file: raw/ESP32 LoRa Sensor Monitoring with Web Server (Long Range Communication).md
---

```yaml
---
title: "ESP32 LoRa Sensor Monitoring with Web Server (Long Range Communication)"
source: "https://randomnerdtutorials.com/esp32-lora-sensor-web-server/"
author: ""
published: "2019-11-20"
created: "2026-04-18"
description: "Build a sensor monitoring system with ESP32 TTGO LoRa32 SX1276 board that sends temperature, humidity and pressure readings via LoRa to a LoRa receiver web server."
tags: ""
---
```

In this project, you’ll build a sensor monitoring system using a TTGO LoRa32 SX1276 OLED board that sends temperature, humidity and pressure readings via LoRa radio to an ESP32 LoRa receiver. The receiver displays the latest sensor readings on a web server.

ESP32 LoRa Sensor Monitoring with Web Server Long Range Communication

With this project you’ll learn how to:

- Send sensor readings via LoRa radio between two ESP32 boards;
- Add LoRa and Wi-Fi capabilities simultaneously to your projects (LoRa + Web Server on the same ESP32 board);
- Use the TTGO LoRa32 SX1276 OLED board or similar development boards for IoT projects.

**Recommended reading:** [TTGO LoRa32 SX1276 OLED Board: Getting Started with Arduino IDE](https://randomnerdtutorials.com/ttgo-lora32-sx1276-arduino-ide/)

## Watch the Video Demonstration

Watch the video demonstration to see what you’re going to build throughout this tutorial.

## Project Overview

The following image shows a high-level overview of the project we’ll build throughout this tutorial.

Project Overview ESP32 LoRa Sender and ESP32 LoRa32 Receiver board

- The LoRa sender sends BME280 sensor readings via LoRa radio every 10 seconds;
- The LoRa receiver gets the readings and displays them on a web server;
- You can monitor the sensor readings by accessing the web server;
- The LoRa sender and the Lora receiver can be several hundred meters apart depending on their location. So, you can use this project to monitor sensor readings from your fields or greenhouses if they are a bit apart from your house;
- The LoRa receiver is running an asynchronous web server and the web page files are saved on the ESP32 filesystem (LittleFS);
- The LoRa receiver also shows the date and time the last readings were received. To get date and time, we use the [Network Time Protocol with the ESP32](https://randomnerdtutorials.com/esp32-ntp-client-date-time-arduino-ide/).

**For an introduction to LoRa communication:** what’s LoRa, LoRa frequencies, LoRa applications and more, read our [Getting Started ESP32 with LoRa using Arduino IDE](https://randomnerdtutorials.com/esp32-lora-rfm95-transceiver-arduino-ide/).

## Parts Required

TTGO LoRa32 SX1276 OLED board with antenna

For this project, we’ll use the following components:

- **[TTGO LoRa32 SX1276 OLED board](https://makeradvisor.com/tools/ttgo-lora32-sx1276-esp32-oled/) (2x):** this is an ESP32 development board with a LoRa chip and a built-in OLED. You can use similar boards, or you can use an [ESP32 + LoRa chip + OLED separately](https://randomnerdtutorials.com/esp32-lora-rfm95-transceiver-arduino-ide/).
- [BME280 temperature, humidity and pressure sensor](https://randomnerdtutorials.com/esp32-lora-rfm95-transceiver-arduino-ide/). You should be able to modify this project to use any other sensor.

You’ll also need some [jumper wires](https://makeradvisor.com/tools/jumper-wires-kit-120-pieces/) and a [breadboard](https://makeradvisor.com/tools/mb-102-solderless-breadboard-830-points/).

You can use the preceding links or go directly to [MakerAdvisor.com/tools](https://makeradvisor.com/tools/?utm_source=rnt&utm_medium=post&utm_campaign=post) to find all the parts for your projects at the best price!

[](https://makeradvisor.com/tools/?utm_source=rnt&utm_medium=post&utm_campaign=post)

## Preparing the Arduino IDE

To program the TTGO LoRa32 SX1276 OLED boards we’ll use [Arduino IDE](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/). To upload files to the ESP32 filesystem, we’ll use the [ESP32 LittleFS filesystem uploader plugin](https://randomnerdtutorials.com/arduino-ide-2-install-esp32-littlefs/).

**So, before proceeding, you need to install the [ESP32 boards](https://randomnerdtutorials.com/installing-esp32-arduino-ide-2-0/) and the [ESP32 filesystem uploader plugin](https://randomnerdtutorials.com/arduino-ide-2-install-esp32-littlefs/)** in your Arduino IDE.

## Installing libraries

For this project, you need to install several libraries.

### LoRa, BME280, OLED, and Web Server Libraries

The following libraries can be installed through the Arduino Library Manager. Go to **Sketch** > **Include Library** > **Manage Libraries** and search for the libraries’ name.

- LoRa library: [arduino-LoRa library by sandeep mistry](https://github.com/sandeepmistry/arduino-LoRa)
- OLED libraries: [Adafruit\_SSD1306 library](https://github.com/adafruit/Adafruit_SSD1306) and [Adafruit\_GFX library](https://github.com/adafruit/Adafruit-GFX-Library)
- BME280 libraries: [Adafruit\_BME280 library](https://github.com/adafruit/Adafruit_BME280_Library) and [Adafruit unified sensor library](https://github.com/adafruit/Adafruit_Sensor)
- Web Server libraries: [ESPAsyncWebServer](https://github.com/ESP32Async/ESPAsyncWebServer) (by ESP32Async) and [AsyncTCP](https://github.com/ESP32Async/AsyncTCP) (by ESP32Async)

### NTPClient Library

Everytime the LoRa receiver picks up a new a LoRa message, it will request the date and time from an NTP server so that we know when the last packet was received.

For that we’ll be using the [NTPClient library forked by Taranais](https://github.com/taranais/NTPClient). Follow the next steps to install this library in your Arduino IDE:

**IMPORTANT**: we’re not using the default NTPClient library. To follow this tutorial you need to install the library we recommend using the following steps.

1. [Click here to download the NTP Client library](https://github.com/taranais/NTPClient/archive/master.zip). You should have a.zip folder in your *Downloads*
2. In your Arduino IDE, go to **Sketch** > **Include Library** > **Add. ZIP library** …
3. Select the.ZIP file of the library you just downloaded.
4. The library will be installed after a few seconds.

## LoRa Sender

The LoRa Sender is connected to a [BME280 sensor](https://randomnerdtutorials.com/esp32-bme280-arduino-ide-pressure-temperature-humidity/) and sends temperature, humidity, and pressure readings every 10 seconds. You can change this period of time later in the code.

**Recommended reading:** [ESP32 with BME280 Sensor using Arduino IDE (Pressure, Temperature, Humidity)](https://randomnerdtutorials.com/esp32-bme280-arduino-ide-pressure-temperature-humidity/)

### LoRa Sender Circuit

The BME280 we’re using communicates with the ESP32 using I2C communication protocol. Wire the sensor as shown in the next schematic diagram:

TTGO LoRa32 SX1276 OLED board ESP32 Sender

| **BME280** | **ESP32** |
| --- | --- |
| VIN | 3.3 V |
| GND | GND |
| SCL | GPIO 13 |
| SDA | GPIO 21 |

### LoRa Sender Code

The following code reads temperature, humidity and pressure from the BME280 sensor and sends the readings via LoRa radio.

Copy the following code to your Arduino IDE.

```c
/*********
  Rui Santos & Sara Santos - Random Nerd Tutorials
  Complete project details at https://RandomNerdTutorials.com/esp32-lora-sensor-web-server/
  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.
  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*********/

//Libraries for LoRa
#include 
#include 

//Libraries for OLED Display
#include 
#include 
#include 

//Libraries for BME280
#include 
#include 

//define the pins used by the LoRa transceiver module
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26

//433E6 for Asia
//866E6 for Europe
//915E6 for North America
#define BAND 866E6

//OLED pins
#define OLED_SDA 4
#define OLED_SCL 15 
#define OLED_RST 16
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

//BME280 definition
#define SDA 21
#define SCL 13

TwoWire I2Cone = TwoWire(1);
Adafruit_BME280 bme;

//packet counter
int readingID = 0;

int counter = 0;
String LoRaMessage = "";

float temperature = 0;
float humidity = 0;
float pressure = 0;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);

//Initialize OLED display
void startOLED(){
  //reset OLED display via software
  pinMode(OLED_RST, OUTPUT);
  digitalWrite(OLED_RST, LOW);
  delay(20);
  digitalWrite(OLED_RST, HIGH);

  //initialize OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3c, false, false)) { // Address 0x3C for 128x32
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("LORA SENDER");
}

//Initialize LoRa module
void startLoRA(){
  //SPI LoRa pins
  SPI.begin(SCK, MISO, MOSI, SS);
  //setup LoRa transceiver module
  LoRa.setPins(SS, RST, DIO0);

  while (!LoRa.begin(BAND) && counter 
#include 

//Libraries for OLED Display
#include 
#include 
#include 

//Libraries for BME280
#include 
#include 
```

Define the pins used by the LoRa transceiver module. We’re using the [TTGO LoRa32 SX1276 OLED board V1.0](https://makeradvisor.com/esp32-sx1276-lora-ssd1306-oled/) and these are the pins used by the LoRa chip:

```c
//define the pins used by the LoRa transceiver module
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26
```

**Note:** if you’re using another LoRa board, check the pins used by the LoRa transceiver chip.

Select the LoRa frequency:

```c
#define BAND 866E6
```

Define the OLED pins.

```c
#define OLED_SDA 4
#define OLED_SCL 15 
#define OLED_RST 16
```

Define the OLED size.

```c
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
```

Define the pins used by the BME280 sensor.

```c
//BME280 definition
#define SDA 21
#define SCL 13
```

Create an I2C instance for the BME280 sensor and a bme object.

```c
TwoWire I2Cone = TwoWire(1);
Adafruit_BME280 bme;
```

Create some variables to hold the LoRa message, temperature, humidity, pressure and reading ID.

```c
int readingID = 0;

int counter = 0;
String LoRaMessage = "";

float temperature = 0;
float humidity = 0;
float pressure = 0;
```

Create a display object for the OLED display.

```c
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);
```

#### setup()

In the setup(), we call several functions that were created previously in the code to initialize the OLED display, the BME280 and the LoRa transceiver module.

```c
void setup() {
  Serial.begin(115200);
  startOLED();
  startBME();
  startLoRA();
}
```

#### loop()

In the loop(), we call the getReadings() and sendReadings() functions that were also previously created. These functions are responsible for getting readings from the BME280 sensor, and to send those readings via LoRa, respectively.

```c
void loop() {
  getReadings();
  sendReadings();
  delay(10000);
}
```

**getReadings()**

Getting sensor readings is as simple as using the readTemperature(), readHumidity(), and readPressure() methods on the bme object:

```c
void getReadings(){
  temperature = bme.readTemperature();
  humidity = bme.readHumidity();
  pressure = bme.readPressure() / 100.0F;
}
```

**sendReadings()**

To send the readings via LoRa, we concatenate all the readings on a single variable, LoRaMessage:

```c
void sendReadings() {
  LoRaMessage = String(readingID) + "/" + String(temperature) + "&" + String(humidity) + "#" + String(pressure);
```

Note that each reading is separated with a special character, so the receiver can easily identify each value.

Then, send the packet using the following:

```c
LoRa.beginPacket();
LoRa.print(LoRaMessage);
LoRa.endPacket();
```

Each time we send a LoRa packet, we increase the readingID variable so that we have an idea on how many packets were sent. You can delete this variable if you want.

```c
readingID++;
```

The loop() is repeated every 10000 milliseconds (10 seconds). So, new sensor readings are sent every 10 seconds. You can change this delay time if you want.

```c
delay(10000);
```

### Testing the LoRa Sender

Upload the code to your ESP32 LoRa Sender Board.

Go to **Tools** > **Port** and select the COM port it is connected to. Then, go to **Tools** > **Board** and select the board you’re using. In our case, it’s the TTGO LoRa32-OLED V1.

Arduino IDE selecting TTGO LoRa32-OLED-V1 board

Finally, press the upload button.

Open the Serial Monitor at a baud rate of 115200. You should get something as shown below.

Arduino IDE: ESP32 LoRa Sender Circuit Demonstration

The OLED of your board should be displaying the latest sensor readings.

TTGO LoRa32 SX1276 OLED board ESP32 Sender Circuit Schematic

Your LoRa Sender is ready. Now, let’s move on to the LoRa Receiver.

## LoRa Receiver

The LoRa Receiver gets incoming LoRa packets and displays the received readings on an asynchronous web server. Besides the sensor readings, we also display the last time those readings were received and the RSSI (received signal strength indicator).

The following figure shows the web server we’ll build.

TTGO LoRa32 board ESP32 Receiver Web Server Example

As you can see, it contains a background image and styles to make the web page more appealing. There are several ways to [display images on an ESP32 web server](https://randomnerdtutorials.com/display-images-esp32-esp8266-web-server/). We’ll store the image on the ESP32 filesystem (LittleFS). We’ll also store the HTML file on LittleFS.

### Organizing your Files

To build the web server you need three different files: the Arduino sketch, the HTML file and the image. The HTML file and the image should be saved inside a folder called ***data*** inside the Arduino sketch folder, as shown below.

ESP32 Filesystem plugin files structure organized data folder HTML jpg

### Creating the HTML File

Create an *index.html* file with the following content or **[download all the project files here](https://github.com/RuiSantosdotme/Random-Nerd-Tutorials/raw/master/Projects/ESP32/ESP3_LoRa/ESP3_LoRa.zip)**:

```html

  
  
  ESP32 (LoRa + Server)
  
  
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      text-align: center;
    }
    header {
      margin: 0;
      padding-top: 5vh;
      padding-bottom: 5vh;
      overflow: hidden;
      background-image: url(winter);
      background-size: cover;
      color: white;
    }
    h2 {
      font-size: 2.0rem;
    }
    p { font-size: 1.2rem; }
    .units { font-size: 1.2rem; }
    .readings { font-size: 2.0rem; }
  

  
    ESP32 (LoRa + Server)
    Last received packet:%TIMESTAMP%
    LoRa RSSI: %RSSI%
  

  
     Temperature: %TEMPERATURE%
    &deg;C
  
  
     Humidity: %HUMIDITY%
    &#37;
  
  
     Pressure: %PRESSURE%
    hpa
  

setInterval(updateValues, 10000, "temperature");
setInterval(updateValues, 10000, "humidity");
setInterval(updateValues, 10000, "pressure");
setInterval(updateValues, 10000, "rssi");
setInterval(updateValues, 10000, "timestamp");

function updateValues(value) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById(value).innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "/" + value, true);
  xhttp.send();
}

```

[View raw code](https://github.com/RuiSantosdotme/Random-Nerd-Tutorials/raw/master/Projects/ESP32/ESP3_LoRa/LoRa_Receiver_Web_Server/data/index.html)

We’ve also included the CSS styles on the HTML file as well as some JavaScript that is responsible for updating the sensor readings automatically.

Something important to notice are the placeholders. The placeholders go between **%** signs: %TIMESTAMP%, %TEMPERATURE%, %HUMIDITY%, %PRESSURE% and %RSSI%.

These placeholders will then be replaced with the actual values by the Arduino code.

The styles are added between the  and  tags.

```html

  body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    text-align: center;
  }
  header {
    margin: 0;
    padding-top: 10vh;
    padding-bottom: 5vh;
    overflow: hidden;
    width: 100%;
    background-image: url(winter.jpg);
    background-size: cover;
    color: white;
  }
  h2 {
    font-size: 2.0rem;
  }
  p { font-size: 1.2rem; }
  .units { font-size: 1.2rem; }
  .readings { font-size: 2.0rem; }

```

If you want a different image for your background, you just need to modify the following line to include your image’s name. In our case, it is called *winter.jpg*.

```
background-image: url(winter.jpg);
```

The JavaScript goes between the  and  tags.

```javascript

setInterval(updateValues("temperature"), 5000);
setInterval(updateValues("humidity"), 5000);
setInterval(updateValues("pressure"), 5000);
setInterval(updateValues("rssi"), 5000);
setInterval(updateValues("timeAndDate"), 5000);

function updateValues(value) {
  console.log(value);
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById(value).innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "/" + value, true);
  xhttp.send();
}

```

We won’t explain in detail how the HTML and CSS works, but a good place to learn is the [W3Schools website](https://www.w3schools.com/css/default.asp).

### LoRa Receiver Arduino Sketch

Copy the following code to your Arduino IDE or [**download all the project files here**](https://github.com/RuiSantosdotme/Random-Nerd-Tutorials/raw/master/Projects/ESP32/ESP3_LoRa/ESP3_LoRa.zip). Then, you need to type your network credentials (SSID and password) to make it work.

```c
/*********
  Rui Santos & Sara Santos - Random Nerd Tutorials
  Complete project details at https://RandomNerdTutorials.com/esp32-lora-sensor-web-server/
  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.
  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*********/
// Import Wi-Fi library
#include 
#include "ESPAsyncWebServer.h"

#include 

//Libraries for LoRa
#include 
#include 

//Libraries for OLED Display
#include 
#include 
#include 

// Libraries to get time from NTP Server
#include 
#include 

//define the pins used by the LoRa transceiver module
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26

//433E6 for Asia
//866E6 for Europe
//915E6 for North America
#define BAND 866E6

//OLED pins
#define OLED_SDA 4
#define OLED_SCL 15 
#define OLED_RST 16
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

// Replace with your network credentials
const char* ssid     = "REPLACE_WITH_YOUR_SSID";
const char* password = "REPLACE_WITH_YOUR_PASSWORD";

// Define NTP Client to get time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);

// Variables to save date and time
String formattedDate;
String day;
String hour;
String timestamp;

// Initialize variables to get and save LoRa data
int rssi;
String loRaMessage;
String temperature;
String humidity;
String pressure;
String readingID;

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);

// Replaces placeholder with DHT values
String processor(const String& var){
  //Serial.println(var);
  if(var == "TEMPERATURE"){
    return temperature;
  }
  else if(var == "HUMIDITY"){
    return humidity;
  }
  else if(var == "PRESSURE"){
    return pressure;
  }
  else if(var == "TIMESTAMP"){
    return timestamp;
  }
  else if (var == "RRSI"){
    return String(rssi);
  }
  return String();
}

//Initialize OLED display
void startOLED(){
  //reset OLED display via software
  pinMode(OLED_RST, OUTPUT);
  digitalWrite(OLED_RST, LOW);
  delay(20);
  digitalWrite(OLED_RST, HIGH);

  //initialize OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3c, false, false)) { // Address 0x3C for 128x32
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("LORA SENDER");
}

//Initialize LoRa module
void startLoRA(){
  int counter;
  //SPI LoRa pins
  SPI.begin(SCK, MISO, MOSI, SS);
  //setup LoRa transceiver module
  LoRa.setPins(SS, RST, DIO0);

  while (!LoRa.begin(BAND) && counter send(LittleFS, "/index.html", String(), false, processor);
  });
  server.on("/temperature", HTTP_GET, {
    request->send(200, "text/plain", temperature.c_str());
  });
  server.on("/humidity", HTTP_GET, {
    request->send(200, "text/plain", humidity.c_str());
  });
  server.on("/pressure", HTTP_GET, {
    request->send(200, "text/plain", pressure.c_str());
  });
  server.on("/timestamp", HTTP_GET, {
    request->send(200, "text/plain", timestamp.c_str());
  });
  server.on("/rssi", HTTP_GET, {
    request->send(200, "text/plain", String(rssi).c_str());
  });
  server.on("/winter", HTTP_GET, {
    request->send(LittleFS, "/winter.jpg", "image/jpg");
  });
  // Start server
  server.begin();
  
  // Initialize a NTPClient to get time
  timeClient.begin();
  // Set offset time in seconds to adjust for your timezone, for example:
  // GMT +1 = 3600
  // GMT +8 = 28800
  // GMT -1 = -3600
  // GMT 0 = 0
  timeClient.setTimeOffset(0);
}

void loop() {
  // Check if there are LoRa packets available
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    getLoRaData();
    getTimeStamp();
  }
}
```

[View raw code](https://github.com/RuiSantosdotme/Random-Nerd-Tutorials/raw/master/Projects/ESP32/ESP3_LoRa/LoRa_Receiver_Web_Server/LoRa_Receiver_Web_Server.ino)

### How the Code Works

You start by including the necessary libraries. You need libraries to:

- build the asynchronous web server;
- access the ESP32 filesystem (LittleFS);
- communicate with the LoRa chip;
- control the OLED display;
- get date and time from an NTP server.
```c
// Import Wi-Fi library
#include 
#include "ESPAsyncWebServer.h"

#include 

//Libraries for LoRa
#include 
#include 

//Libraries for OLED Display
#include 
#include 
#include 

// Libraries to get time from NTP Server
#include 
#include 
```

Define the pins used by the LoRa transceiver module.

```c
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26
```

**Note:** if you’re using another LoRa board, check the pins used by the LoRa transceiver chip.

Define the LoRa frequency:

```c
//433E6 for Asia
//866E6 for Europe
//915E6 for North America
#define BAND 866E6
```

Set up the OLED pins:

```c
#define OLED_SDA 4
#define OLED_SCL 15 
#define OLED_RST 16
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
```

Enter your network credentials in the following variables so that the ESP32 can connect to your local network.

```c
const char* ssid     = "REPLACE_WITH_YOUR_SSID";
const char* password = "REPLACE_WITH_YOUR_PASSWORD";
```

Define an NTP Client to get date and time:

```c
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);
```

Create variables to save date and time:

```c
String formattedDate;
String day;
String hour;
String timestamp;
```

More variables to store the sensor readings received via LoRa radio.

```c
int rssi;
String loRaMessage;
String temperature;
String humidity;
String pressure;
String readingID;
```

Create an AsyncWebServer object called server on port 80.

```c
AsyncWebServer server(80);
```

Create an object called display for the OLED display:

```c
AsyncWebServer server(80);
```

#### processor()

The processor() function is what will attribute values to the placeholders we’ve created on the HTML file.

It accepts as argument the placeholder and should return a String that will replace that placeholder.

For example, if it finds the TEMPERATURE placeholder, it will return the temperature String variable.

```c
// Replaces placeholder with DHT values
String processor(const String& var){
  //Serial.println(var);
  if(var == "TEMPERATURE"){
    return temperature;
  }
  else if(var == "HUMIDITY"){
    return humidity;
  }
  else if(var == "PRESSURE"){
    return pressure;
  }
  else if(var == "TIMESTAMP"){
    return timestamp;
  }
  else if (var == "RRSI"){
    return String(rssi);
  }
  return String();
}
```

#### setup()

In the setup(), you initialize the OLED display, the LoRa communication, and connect to Wi-Fi.

```c
void setup() { 
  // Initialize Serial Monitor
  Serial.begin(115200);
  startOLED();
  startLoRA();
  connectWiFi();
```

You also initialize LittleFS:

```c
if(!LittleFS.begin()){
  Serial.println("An Error has occurred while mounting LittleFS");
  return;
}
```

**Async Web Server**

The ESPAsyncWebServer library allows us to configure the routes where the server will be listening for incoming HTTP requests.

For example, when a request is received on the route URL, we send the *index.html* file that is saved in the ESP32 LittleFS:

```c
server.on("/", HTTP_GET, {
  request->send(LittleFS, "/index.html", String(), false, processor);
});
```

As mentioned previously, we added a bit of Javascript to the HTML file that is responsible for updating the web page every 10 seconds. When that happens, it makes a request on the **/temperature**, **/humidity**, **/pressure**, **/timestamp**, **/rssi** URLs.

So, we need to handle what happens when we receive those requests. We simply need to send the temperature, humidity, pressure, timestamp and rssi variables. The variables should be sent in char format, that’s why we use the.c\_str() method.

```c
server.on("/temperature", HTTP_GET, {
  request->send_P(200, "text/plain", temperature.c_str());
});
server.on("/humidity", HTTP_GET, {
  request->send_P(200, "text/plain", humidity.c_str());
});
server.on("/pressure", HTTP_GET, {
  request->send_P(200, "text/plain", pressure.c_str());
});
server.on("/timestamp", HTTP_GET, {
  request->send_P(200, "text/plain", timestamp.c_str());
});
server.on("/rssi", HTTP_GET, {
  request->send_P(200, "text/plain", String(rssi).c_str());
});
```

Because we included an image in the web page, we’ll get a request “asking” for the image. So, we need to send the image that is saved on the ESP32 LittleFS.

```c
server.on("/winter", HTTP_GET, {
  request->send(LittleFS, "/winter.jpg", "image/jpg");
});
```

Finally, start the web server.

```c
server.begin();
```

#### NTPClient

Still in the setup(), create an NTP client to get the time from the internet.

```c
timeClient.begin();
```

The time is returned in GMT format, so if you need to adjust for your timezone, you can use the following:

```c
// Set offset time in seconds to adjust for your timezone, for example:
// GMT +1 = 3600
// GMT +8 = 28800
// GMT -1 = -3600
// GMT 0 = 0
timeClient.setTimeOffset(0);
```

### loop()

In the loop(), we listen for incoming LoRa packets:

```c
int packetSize = LoRa.parsePacket();
```

If a new LoRa packet is available, we call the getLoRaData() and getTimeStamp() functions.

```c
if (packetSize) {
  getLoRaData();
  getTimeStamp();
}
```

The getLoRaData() function receives the LoRa message and splits it to get the different readings.

The getTimeStamp() function gets the time and date from the internet at the moment we receive the packet.

### Uploading Code and Files

After inserting your network credentials, save your sketch. Then, in your Arduino IDE go to **Sketch** > **Show Sketch Folder**, and create a folder called ***data***.

Arduino IDE Open Sketch Folder to create data folder

**Inside that folder, you should have the HTML file and the image file.**

After making sure you have all the needed files in the right directories, you need to upload the files to the ESP32 LittleFS filesystem.

Press \[**Ctrl**\] + \[**Shift**\] + \[**P**\] on Windows or \[**⌘**\] + \[**Shift**\] + \[**P**\] on MacOS to open the command palette. Search for the **Upload LittleFS to Pico/ESP8266/ESP32** command and click on it.

If you don’t have this option it’s because you didn’t install the filesystem uploader plugin. [Check this tutorial](https://randomnerdtutorials.com/arduino-ide-2-install-esp32-littlefs/).

ESP32 Sketch Data Upload LittleFS Arduino IDE

**Important:** make sure the Serial Monitor is closed before uploading to the filesystem. Otherwise, the upload will fail.

After a few seconds, the files should be successfully uploaded to LittleFS.

Now, upload the sketch to your board.

Arduino IDE 2 Upload Button

Open the Serial Monitor at a baud rate of 115200.

You should get the ESP32 IP address, and you should start receiving LoRa packets from the sender.

ESP32 Arduino IDE Serial Monitor window

You should also get the IP address displayed on the OLED.

TTGO LoRa32 SX1276 OLED board ESP32 Receiver Circuit Schematic web server

## Demonstration

Open a browser and type your ESP32 IP address. You should see the web server with the latest sensor readings.

ESP32 LoRa + Web Server + Sensor readings

With these boards we were able to get a stable LoRa communication up to 180 meters (590 ft) in open field. These means that we can have the sender and receiver 180 meters apart and we’re still able to get and check the readings on the web server.

LoRa32 SX1276 OLED Board Communication Range Experiment

Getting a stable communication at a distance of 180 meters with such low cost boards and without any further customization is really impressive.

However, in a previous project using an [RFM95 SX1276 LoRa transceiver chip](https://makeradvisor.com/tools/rfm95-lora-transceiver-module/) with an home made antenna, we got better results: more than 250 meters with many obstacles in between.

RFM95 LoRa SX1276 transceiver chip connected to an ESP32

The communication range will really depend on your environment, the LoRa board you’re using and many other variables.

## Wrapping Up

You can take this project further and build an off-the-grid monitoring system by adding solar panels and deep sleep to your LoRa sender. The following articles might help you do that:

- [ESP32 Deep Sleep with Arduino IDE and Wake Up Sources](https://randomnerdtutorials.com/esp32-deep-sleep-arduino-ide-wake-up-sources/)
- [Power ESP32 with Solar Panels](https://randomnerdtutorials.com/power-esp32-esp8266-solar-panels-battery-level-monitoring/)
- [ESP32 with Built-in SX1276 LoRa and SSD1306 OLED Display (Review)](https://makeradvisor.com/esp32-sx1276-lora-ssd1306-oled/)

You may also want to access your sensor readings from anywhere or plot them on a chart:

- [Visualize Your Sensor Readings from Anywhere in the World (ESP32 + MySQL + PHP)](https://randomnerdtutorials.com/visualize-esp32-esp8266-sensor-readings-from-anywhere/)
- [ESP32 Plot Sensor Readings in Real Time Charts – Web Server](https://randomnerdtutorials.com/esp32-esp8266-plot-chart-web-server/)

We hope you’ve found this project interesting. If you’d like to see more projects using LoRa radio, let us know in the comments’ section.

Thanks for reading.
