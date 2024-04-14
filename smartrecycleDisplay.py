import threading
import time
import queue
from sense_hat import SenseHat
import pyrebase
import random
from paho.mqtt import client as mqtt_client

# Initialize SenseHat and Queue
sense = SenseHat()
display_queue = queue.Queue()

#Firebase and MQTT configurations 
firebaseConfig = {
    "apiKey": "AIzaSyDXPz9h_hVZuOQDXwuusSRQPJ-F_w98rqo",
    "authDomain": "smartrecycle-a0d95.firebaseapp.com",
    "databaseURL": "https://smartrecycle-a0d95-default-rtdb.firebaseio.com",
    "projectId": "smartrecycle-a0d95",
    "storageBucket": "smartrecycle-a0d95.appspot.com",
    "messagingSenderId": "188701239795",
    "appId": "1:188701239795:android:bf659674ea9a7884c80a86",
}

broker = 'broker.emqx.io'
port = 1883
topic = "unique_topic/mqtt_test"
client_id = f'python-mqtt-{random.randint(1000, 9999)}'

# Colors and Faces
O = [0, 0, 0]  # Off
G = [0, 255, 0]  # Green
B = [0, 0, 255]  # Blue

neutral_face = [
    O, O, B, B, B, B, O, O,
    O, B, O, O, O, O, B, O,
    B, O, B, O, O, B, O, B,
    B, O, O, O, O, O, O, B,
    B, O, O, O, O, O, O, B,
    B, O, B, B, B, B, O, B,
    O, B, O, O, O, O, B, O,
    O, O, B, B, B, B, O, O,
]

happy_face = [
    O, O, G, G, G, G, O, O,
    O, G, O, O, O, O, G, O,
    G, O, G, O, O, G, O, G,
    G, O, O, O, O, O, O, G,
    G, O, G, O, O, G, O, G,
    G, O, O, G, G, O, O, G,
    O, G, O, O, O, O, G, O,
    O, O, G, G, G, G, O, O,
]

last_mqtt_message_time = time.time()  # Record the last received MQTT message time

def manage_display():
    global last_mqtt_message_time
    while True:
        current_time = time.time()
        # Check if it has been more than 10 seconds since last MQTT message
        if current_time - last_mqtt_message_time > 10:
            sense.set_pixels(neutral_face)
        else:
            instruction = display_queue.get()
            if instruction == "neutral":
                sense.set_pixels(neutral_face)
            elif instruction == "happy":
                sense.set_pixels(happy_face)
            else:
                sense.show_message(instruction, scroll_speed=0.05)
        time.sleep(1)

def display_bin_status():
    firebase = pyrebase.initialize_app(firebaseConfig)
    db = firebase.database()
    while True:
        try:
            status = db.child("bin_status/kqeud7aHRahaomVq7IduCvc77Dq1/status").get().val()
            display_queue.put("Bin is " + status)
        except Exception as e:
            print(f"Failed to fetch from Firebase: {e}")
        time.sleep(60)

def mqtt_task():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(topic)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(client, userdata, msg):
        global last_mqtt_message_time
        print("Message received on MQTT:", msg.payload.decode())
        display_queue.put("happy")
        last_mqtt_message_time = time.time()  # Update the time when message is received

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    client.loop_forever()

if __name__ == '__main__':
    threading.Thread(target=manage_display, daemon=True).start()
    threading.Thread(target=display_bin_status, daemon=True).start()
    threading.Thread(target=mqtt_task).start()
    while True:  # Keep main thread alive
        time.sleep(100)
