#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>    // 支援 TLS
#include <PubSubClient.h>

// Wi-Fi 設定
const char* ssid = "A53";
const char* password = "a1478529";

// MQTT Broker 設定（HiveMQ Cloud）
const char* mqtt_server = "d66bc0b5d19d43cdb7363a4ceb915803.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqttUser = "esp8266client";
const char* mqttPassword = "Aa123456";

WiFiClientSecure espClient;
PubSubClient client(espClient);

// 控制綠燈腳位
// 如果你實際用 NodeMCU 板子的 D4（標示為 2）的話，就是 GPIO2。
// 若你要用 D2（標示為 4）請改成 const int greenPin = 4;
const int greenPin = 2;  // 這裡假設接在 GPIO2 (NodeMCU 上的 D4)

// 當收到 MQTT 訊息時的 callback
void callback(char* topic, byte* payload, unsigned int length) {
  // 先把 payload 轉成 String，完整取出所有字元
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  msg.trim();  // 去掉前後空白(若有)

  Serial.print("Received message: ");
  Serial.println(msg);

  // 如果收到 "NO"，關燈 10 秒，再打開
  if (msg == "NO") {
    Serial.println("=> Turn GREEN OFF for 10 seconds");
    digitalWrite(greenPin, LOW);         // 關綠燈

  }
  // 如果收到 "Y"，則馬上打開綠燈（防止之前被關掉還沒重開）
  else if (msg == "YES") {
    Serial.println("=> Received Y -> Turn GREEN ON immediately");
    digitalWrite(greenPin, HIGH);
  }
  // 其他訊息不處理
}

void setup() {
  Serial.begin(115200);
  delay(10);

  pinMode(greenPin, OUTPUT);
  digitalWrite(greenPin, HIGH);  // 一開始就讓綠燈常亮

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    yield();
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("connected");
      client.subscribe("test/railway/status");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
      yield();
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  // 綠燈的開關都在 callback 處理，這裡不需要額外動作
}