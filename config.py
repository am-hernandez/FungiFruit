import os

API_KEY = os.environ.get('THINGSPEAK_KEY')
WIFI_SSID =  os.environ.get('W_ID')
WIFI_PASSWORD =  os.environ.get('W_PW')
LED_PIN = 2  # D4
DEBUG_PIN = 14  # D5
I2C_SCL = 0 #D4
I2C_SDA = 4 #D3
DHT11_PIN = 12  # D6
DISPLAY_I2C_SCL = 0 #D4
DISPLAY_I2C_SDA = 1 #D3
FAN_IN_T_PIN = 2 #P02
FAN_IN_B_PIN = 3 #P03
FAN_OUT_T_PIN = 4 #P04
FAN_OUT_B_PIN = 5 #P05
DIFFUSER_PIN = 6 #P06
FAHRENHEIT = False
WEBHOOK_URL = 'https://api.thingspeak.com/update?api_key={api_key}&field1={temperature}&field2={humidity}'
LOG_INTERVAL = 60 #seconds

