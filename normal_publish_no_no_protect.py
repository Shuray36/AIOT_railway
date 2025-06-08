import time
import ssl
import uuid
import paho.mqtt.client as mqtt

# Broker 設定
BROKER   = "d66bc0b5d19d43cdb7363a4ceb915803.s1.eu.hivemq.cloud"
PORT     = 8883
USERNAME = "esp8266client"
PASSWORD = "Aa123456"
TOPIC    = "test/railway/status"

# MQTT 事件回呼函式
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("")
#     else:
#         print(f"❌ 連線失敗，錯誤碼：{rc}")

# def on_disconnect(client, userdata, rc):
#     print(f"🔌 與 Broker 斷線，錯誤碼：{rc}")

def on_publish(client, userdata, mid):
    print(f"📤 已發佈訊息（mid={mid}）")

def main():
    # 產生唯一 client_id（避免重複被踢掉）
    client_id = f"ESP8266_Railway_{uuid.uuid4()}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

    # 設定帳密
    client.username_pw_set(USERNAME, PASSWORD)

    # 設定 TLS（HiveMQ Cloud 要求）
    client.tls_set(
        ca_certs=None,
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )

    # 綁定事件處理函式
    # client.on_connect = on_connect
    # client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    # 設定自動重連延遲（1秒~2分鐘）
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    try:
        client.connect(BROKER, PORT)
    except Exception as e:
        print(f"❌ 初次連線失敗：{e}")
        return

    client.loop_start()

    try:
        while True:
            msg = input("請輸入要傳送的訊息（YES / NO / q 離開）：").strip().upper()
            if msg == "Q":
                print("🛑 結束程式")
                break
            elif msg not in ["YES", "NO"]:
                print("⚠️ 請只輸入 YES 或 NO")
                continue

            if not client.is_connected():
                print("❌ 尚未連線，請稍後再試")
                continue

            result = client.publish(TOPIC, payload=msg, qos=1)
            result.wait_for_publish()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 成功送出 {msg}")

    except KeyboardInterrupt:
        print("\n🛑 使用者中止程式")

    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
