import time
import base64
import uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import paho.mqtt.client as mqtt
import ssl

# 固定 AES 金鑰（需與 ESP8266 相同）
KEY = b"1234567890abcdef"  # 16 bytes

# MQTT 連線設定
BROKER   = "d66bc0b5d19d43cdb7363a4ceb915803.s1.eu.hivemq.cloud"
PORT     = 8883
USERNAME = "esp8266client"
PASSWORD = "Aa123456"
TOPIC    = "test/railway/status"

# AES CBC 加密（附帶 IV）
def aes_encrypt_base64(msg: str) -> str:
    iv = get_random_bytes(16)
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    padded_data = pad(msg.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return base64.b64encode(iv + encrypted).decode("utf-8")

# MQTT 回呼
def on_connect(client, userdata, flags, rc):
    pass
    # # print("✅ 已連線" if rc == 0 else f"❌ 連線失敗，錯誤碼：{rc}")

def on_disconnect(client, userdata, rc):
    print(f"🔌 與 MQTT Broker 斷線（錯誤碼：{rc}）")

def on_publish(client, userdata, mid):
    print(f"📤 發佈完成（mid={mid}）")

def main():
    # 建立唯一 client_id
    client_id = f"RailwayClient_{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.username_pw_set(USERNAME, PASSWORD)

    # TLS 安全連線
    client.tls_set(
        ca_certs=None,
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )

    # 自動重連機制
    client.reconnect_delay_set(min_delay=1, max_delay=60)

    # 綁定回呼
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    try:
        client.connect(BROKER, PORT)
    except Exception as e:
        print(f"❌ 初始連線失敗：{e}")
        return

    client.loop_start()

    try:
        while True:
            msg = input("輸入 YES / NO / q 離開：").strip().upper()
            if msg == "Q":
                break
            if msg not in ["YES", "NO"]:
                print("⚠️ 僅接受 YES 或 NO")
                continue

            # 檢查連線狀態
            if not client.is_connected():
                print("⚠️ 尚未連線，請稍候再試")
                continue

            encrypted_msg = aes_encrypt_base64(msg)
            print(f"🔐 加密後：{encrypted_msg}")
            result = client.publish(TOPIC, payload=encrypted_msg, qos=1)
            result.wait_for_publish()
            print(f"[{time.strftime('%H:%M:%S')}] ✅ 已送出")

    except KeyboardInterrupt:
        print("\n🛑 使用者中斷")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
