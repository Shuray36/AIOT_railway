#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <AESLib.h>
#include <base64.h>

// Wi-Fi 
const char* ssid = "A53";
const char* password = "a1478529";

// MQTT
const char* mqtt_server = "d66bc0b5d19d43cdb7363a4ceb915803.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqttUser = "esp8266client";
const char* mqttPassword = "Aa123456";

WiFiClientSecure espClient;
PubSubClient client(espClient);
AESLib aesLib;

byte aes_key[] = "1234567890abcdef";

const int greenPin = 2;  // GPIO2 (D4)

void callback(char* topic, byte* payload, unsigned int length) {
  String encryptedBase64 = "";
  for (unsigned int i = 0; i < length; i++) {
    encryptedBase64 += (char)payload[i];
  }

  Serial.print("🔐 收到加密訊息 (Base64)：");
  Serial.println(encryptedBase64);

  // 解碼 base64 字串為 byte[]
  char decodedBytes[128];  // base64 decode 輸出緩衝區
  memset(decodedBytes, 0, sizeof(decodedBytes));
  int decodedLen = base64_decode(decodedBytes, encryptedBase64.c_str(), encryptedBase64.length());

  if (decodedLen <= 16) {
    Serial.println("⚠️ 解碼長度異常，忽略訊息");
    return;
  }

  // 取出 IV（前 16 bytes）和密文（剩下的）
  byte iv[16];
  memcpy(iv, decodedBytes, 16);

  byte ciphertext[112];
  int ciphertextLen = decodedLen - 16;
  memcpy(ciphertext, decodedBytes + 16, ciphertextLen);

  // 解密
  char decrypted[64];
  memset(decrypted, 0, sizeof(decrypted));

  uint16_t decryptedLen = aesLib.decrypt(
    ciphertext, ciphertextLen,
    (byte*)decrypted, aes_key, 128, iv
  );
  decrypted[decryptedLen] = '\0';

  String msg = String(decrypted);

  // 過濾非印刷字元
  String clean = "";
  for (unsigned int i = 0; i < msg.length(); i++) {
    if (msg[i] >= 32 && msg[i] <= 126) {
      clean += msg[i];
    }
  }
  msg = clean;
  msg.trim();

  Serial.print("✅ 解密後內容：");
  Serial.println(msg);

  if (msg == "NO") {
    Serial.println("⛔ 收到 NO：關燈");
    digitalWrite(greenPin, LOW);
  } else if (msg == "YES") {
    Serial.println("🟢 收到 YES：開燈");
    digitalWrite(greenPin, HIGH);
  } else {
    Serial.println("⚠️ 非法指令，忽略");
  }
}


void setup() {
  Serial.begin(115200);
  pinMode(greenPin, OUTPUT);
  digitalWrite(greenPin, HIGH);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP8266Client-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("connected");
      client.subscribe("test/railway/status");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

