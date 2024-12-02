#include <SPI.h>
#include <Ethernet.h>

// Ethernet konfigürasyonu
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED }; // Ethernet kartınızın MAC adresi
IPAddress ip(192, 168, 1, 131); // Arduino'nuzun statik IP adresi
EthernetServer server(80); // Port 80'de bir sunucu oluşturuluyor

const int signalPin = 6; // Sinyal pinini belirliyoruz

// Kabul edilecek IP adresini tanımlıyoruz
IPAddress allowedIP(192, 168, 1,33); // Örneğin 192.168.1.100 IP adresi

void setup() {
  pinMode(signalPin, OUTPUT);
  analogWrite(signalPin, 0);

  Ethernet.begin(mac, ip);  // Ethernet'i başlat
  server.begin();           // Sunucuyu başlat
  Serial.begin(9600);       // Seri haberleşmeyi başlat
  Serial.println("Server Started!");
}

void loop() {
  EthernetClient client = server.available();
  if (client) {
    // Gelen istemcinin IP adresini al
    IPAddress clientIP = client.remoteIP();

    // Sadece izin verilen IP'den gelen istekleri kabul et
    if (clientIP == allowedIP) {
      String request = "";

      int index=0;
      // Tüm veriyi okuma işlemi
      while(client.connected()) {
        if (client.available()) {
          char c = client.read();
          request += c;
          index+=1;
        }
        if(index==3)
        {
          break;
        }
      }

      // Gelen request'i konsola yazdırıyoruz
      Serial.println("Request received from allowed IP:");
      Serial.println(request);

      // GET isteği geldiğinde pin 6'yı aktif et
      if (request.indexOf("GET") != -1) {
        analogWrite(signalPin, 255); // Pin 6'yı aktif et
        delay(5000); // 5 saniye pin 6'yı açık tut
        analogWrite(signalPin,0 );  // Pin 6'yı kapat
      }

      // HTTP yanıtı gönder
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: text/plain");
      client.println("Connection: close");
      client.println();
      client.println("Request received and processed");

      // Bağlantıyı kapatıyoruz
      client.stop();
      Serial.println("Client disconnected.");
    } else {
      // Eğer istemci IP adresi izin verilen IP ile eşleşmiyorsa, bağlantıyı kes
      Serial.println("Unauthorized IP address. Connection closed.");
      Serial.println(clientIP);
      client.stop();
    }
  }
}
