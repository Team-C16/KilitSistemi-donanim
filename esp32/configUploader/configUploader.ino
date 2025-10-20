#include <Preferences.h> // NVS kütüphanesini dahil et

// NVS işlemleri için bir nesne oluştur
Preferences preferences;

//*******************************************************************
// BİLGİLERİ BURAYA GİRİN
// Her cihaza yüklemeden önce bu iki satırı o cihaza özel bilgilerle güncelleyin.
//*******************************************************************
const int room_id = 13; 
const char* jwt_secret = "";
const char* ssid = "";
const char* password = "";
const int accessType = 1;
//*******************************************************************


void setup() {
  Serial.begin(115200);
  delay(1000); // Seri monitörün açılması için kısa bir bekleme

  Serial.println("NVS'e veri yazma islemi baslatiliyor...");

  // 1. "config" isimli ayar alanını yazma modunda AÇ.
  // Yazma işlemi için sadece .begin("alan_adi") kullanmak yeterlidir.
  preferences.begin("config");

  // 2. Verileri NVS'e YAZ.
  // putString("anahtar", "değer") formatını kullanıyoruz.
  preferences.putInt("room_id", room_id);
  preferences.putInt("accessType", accessType);
  preferences.putString("jwtSecret", jwt_secret);
  preferences.putString("ssid", ssid);
  preferences.putString("password", password);

  Serial.println("Veriler NVS'e basariyla yazildi!");
  Serial.println("-------------------------------------");

  // 3. DOĞRULAMA: Yazdığımız verileri hemen geri okuyup kontrol edelim.
  int okunan_id = preferences.getInt("room_id", 0);
  String okunan_secret = preferences.getString("jwtSecret", "HATA");
  String okunan_ssid = preferences.getString("ssid", "HATA");
  String okunan_pass = preferences.getString("password", "HATA");
  int okunan_type = preferences.getInt("accessType", 0);
  
  Serial.println("Dogrulama icin NVS'ten okunan veriler:");
  Serial.printf("Oda ID: %d\n", okunan_id);
  Serial.printf("JWT Secret: %s\n", okunan_secret.c_str());
  Serial.printf("SSID: %s\n", okunan_ssid.c_str());
  Serial.printf("Password: %s\n", okunan_pass.c_str());
  Serial.printf("Access Type: %d\n", okunan_type);
  
  Serial.println("-------------------------------------");


  // 4. İşin bittiğinde alanı KAPAT.
  preferences.end();
  
  Serial.println("Islem tamamlandi. Cihaza artik ana yaziliminizi yukleyebilirsiniz.");
  Serial.println("Bu yazilim sadece bir kerelik kurulum icindir.");
}

void loop() {
  // Bu programın loop içinde bir şey yapmasına gerek yok.
  delay(5000);
}
