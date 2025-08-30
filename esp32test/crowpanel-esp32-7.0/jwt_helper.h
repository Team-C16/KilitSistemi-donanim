#ifndef JWT_HELPER_H
#define JWT_HELPER_H

#include <Arduino.h>
#include <mbedtls/md.h>
#include "base64.hpp"

// Base64URL encode helper
String base64UrlEncode(const String& input) {
  unsigned char out[256]; // yeterli büyüklük ver
  unsigned int out_len = encode_base64((unsigned char*)input.c_str(), input.length(), out);
  out[out_len] = '\0';
  String encoded = String((char*)out);

  // Base64URL dönüşümü
  encoded.replace("+", "-");
  encoded.replace("/", "_");
  encoded.replace("=", "");
  return encoded;
}

// Base64URL decode helper
String base64UrlDecode(const String& input) {
  String temp = input;
  temp.replace("-", "+");
  temp.replace("_", "/");
  while (temp.length() % 4 != 0) temp += "=";

  unsigned char out[256];
  unsigned int out_len = decode_base64((unsigned char*)temp.c_str(), out);
  out[out_len] = '\0';
  return String((char*)out);
}


// JWT oluşturma fonksiyonu
String createJWT(const String& secret, unsigned long expirationSeconds = 30) {
  String header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}";

  time_t now = time(nullptr);
  String payload = "{\"exp\":" + String(now + expirationSeconds) + "}";

  String encodedHeader = base64UrlEncode(header);
  String encodedPayload = base64UrlEncode(payload);
  String toSign = encodedHeader + "." + encodedPayload;

  // SHA256 HMAC imzası
  byte hmacResult[32];

  mbedtls_md_context_t ctx;
  const mbedtls_md_info_t *md = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, md, 1);
  mbedtls_md_hmac_starts(&ctx, (const unsigned char *)secret.c_str(), secret.length());
  mbedtls_md_hmac_update(&ctx, (const unsigned char *)toSign.c_str(), toSign.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  String signature = base64::encode(hmacResult, 32);
  signature.replace("+", "-");
  signature.replace("/", "_");
  signature.replace("=", "");

  return toSign + "." + signature;
}

// JWT doğrulama fonksiyonu
bool verifyJWT(const String& token, const String& secret) {
  Serial.println(token);
  int firstDot = token.indexOf('.');
  int secondDot = token.indexOf('.', firstDot + 1);
  if (firstDot == -1 || secondDot == -1) return false;

  String encodedHeader = token.substring(0, firstDot);
  String encodedPayload = token.substring(firstDot + 1, secondDot);
  String signature = token.substring(secondDot + 1);

  String toSign = encodedHeader + "." + encodedPayload;

  // Yeniden imzala
  byte hmacResult[32];
  mbedtls_md_context_t ctx;
  const mbedtls_md_info_t *md = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, md, 1);
  mbedtls_md_hmac_starts(&ctx, (const unsigned char *)secret.c_str(), secret.length());
  mbedtls_md_hmac_update(&ctx, (const unsigned char *)toSign.c_str(), toSign.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  String expectedSig = base64::encode(hmacResult, 32);
  expectedSig.replace("+", "-");
  expectedSig.replace("/", "_");
  expectedSig.replace("=", "");

  if (expectedSig != signature) {
    Serial.println("Invalid Signature");
    return false; // imza tutmadı
  }

  // Payload decode et
  String payloadJson = base64UrlDecode(encodedPayload);

  // exp alanını bul
  int expIndex = payloadJson.indexOf("\"exp\":");
  if (expIndex == -1) return false;

  long exp = payloadJson.substring(expIndex + 6).toInt();
  time_t now = time(nullptr);

  if (now > exp) {
    
    Serial.println("Expired");
    return false; // süre dolmuş
  }
  
    Serial.println("true");
  return true;
}

#endif // JWT_HELPER_H