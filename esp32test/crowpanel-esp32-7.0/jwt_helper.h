#ifndef JWT_HELPER_H
#define JWT_HELPER_H

#include <Arduino.h>
#include <mbedtls/md.h>
#include <base64.h>  // Arduino'nun Base64 modülü (platforma göre değişebilir)

// Base64URL encode helper
String base64UrlEncode(const String& input) {
  String encoded = base64::encode((uint8_t*)input.c_str(), input.length());
  encoded.replace("+", "-");
  encoded.replace("/", "_");
  encoded.replace("=", "");
  return encoded;
}

// JWT oluşturma fonksiyonu
String createJWT(const String& secret, unsigned long expirationSeconds = 300) {
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

#endif // JWT_HELPER_H
