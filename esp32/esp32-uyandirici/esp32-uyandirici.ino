#include <esp_sleep.h> // Deep sleep kütüphanesi

const int POWER_PIN = 4; 

void setup() {
  delay(1000); 
  Serial.begin(115200);
  delay(1000); 
  // 1. ADIM: Hazirlik
  pinMode(POWER_PIN, OUTPUT);
  delay(1000); 
  digitalWrite(POWER_PIN, HIGH);
  delay(3000);  
  Serial.println("[OK] ESP Uyandi, tetik bekleniyor...");

  // 2. ADIM: Anakart uyanma süresi
  delay(5000); 

  // 3. ADIM: Düğmeye bas (Sert LOW)
  Serial.println("[TETIK] Dugmeye basiliyor...");
  digitalWrite(POWER_PIN, LOW); 
  delay(600); // 600ms basili tut

  // 4. ADIM: Düğmeyi bırak (HIGH yap ve sonra INPUT'a cek)
  digitalWrite(POWER_PIN, HIGH);
  pinMode(POWER_PIN, INPUT);
  Serial.println("[OK] Tetik bitti. Laptop aciliyor.");

  // 5. ADIM: DEEP SLEEP (Koma Modu)
  Serial.println("[UYKU] Islem tamamlandi, ESP derin uykuya giriyor...");
  Serial.flush(); // Serial loglarinin gönderildiğinden emin ol
  
  // Herhangi bir uyandırma süresi belirlemiyoruz (0). 
  // Sadece elektrik kesilip gelirse veya Reset'e basarsan uyanacak.
  esp_deep_sleep_start(); 
}

void loop() {
  // Deep sleep yüzünden buraya asla ulasamayacak
}