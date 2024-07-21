from machine import Pin, ADC
from config import utelegram_config, wifi_config
import utelegram
import network
import utime
import urequests
import ntptime

led = Pin(2, Pin.OUT)  # Integrated LED
adc = ADC(Pin(35))  # Light sensor
adc.atten(ADC.ATTN_11DB)

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()
sta_if.connect(wifi_config['ssid'], wifi_config['password'])

utime.sleep(10)


def get_last_chat_id():
    token = utelegram_config['token']
    configs = f"https://api.telegram.org/bot{token}/getUpdates"
    resp = urequests.get(configs)
    result = resp.json()
    last_message = None
    last_update_id = -1

    for update in result.get('result', []):
        if update['update_id'] > last_update_id:
            last_update_id = update['update_id']
            last_message = update['message']

    if last_message:
        return last_message['chat']['id']
    else:
        return None


def sync_time():
    try:
        ntptime.settime()  # Synchronize with NTP server
        print("Time synchronized")
    except Exception as e:
        print(f"Failed to synchronize time: {e}")


if sta_if.isconnected():
    sync_time()  # Synchronize time with NTP server
    bot = utelegram.ubot(utelegram_config['token'])
    print('Wi-Fi connected')
    print('BOT LISTENING')
    chat_id = get_last_chat_id()
    print(chat_id)
    prev_state = None

    while True:
        b = adc.read()
        print(f"Sensor value: {b}")  # Debug print to check sensor value
        current_state = "no_light" if b >= 4000 else "light"  # no lights when more than 4000

        if current_state != prev_state:
            current_time = utime.localtime(utime.time() + 3 * 3600)  # Adjust to UTC+3 for Ukraine
            time_str = f"{current_time[3]:02}:{current_time[4]:02}"

            if current_state == "no_light":
                print('send no light')
                bot.send(chat_id, f"No lights at {time_str}")
                led.on()

            elif current_state == "light":
                print('send light is on')
                bot.send(chat_id, f"Light is on at {time_str}")
                led.off()

            prev_state = current_state

        utime.sleep(3)
