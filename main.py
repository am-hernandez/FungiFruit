import dht
import machine
import network
import sys
import time
import urequests
import framebuf
import ssd1306

import config
import freesans20
import writer
import pcf8574

# set up port expander
i2c = machine.I2C(scl=machine.Pin(config.I2C_SCL), sda=machine.Pin(config.I2C_SDA))
pcf = pcf8574.PCF8574(i2c, 0x20)

def connect_wifi():
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta_if.isconnected():
            time.sleep(1)
    print('Network config:', sta_if.ifconfig())


def show_error():
    led = machine.Pin(config.LED_PIN, machine.Pin.OUT)
    for i in range(3):
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
    led.on()


def is_debug():
    debug = machine.Pin(config.DEBUG_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    if debug.value() == 0:
        print('Debug mode detected.')
        return True
    return False


def get_temperature_and_humidity():
    dht11 = dht.DHT11(machine.Pin(config.DHT11_PIN))
    dht11.measure()
    temperature = dht11.temperature()
    if config.FAHRENHEIT:
        temperature = temperature * 9 / 5 + 32
    return temperature, dht11.humidity()


def log_data(temperature, humidity):
    print('Invoking log webhook')
    url = config.WEBHOOK_URL.format(api_key=config.API_KEY, temperature=temperature,humidity=humidity)
    response = urequests.get(url)
    if response.status_code < 400:
        print('Webhook invoked')
    else:
        print('Webhook failed')
        raise RuntimeError('Webhook failed')


def deepsleep():
    print('Going into deepsleep for {seconds} seconds...'.format(
        seconds=config.LOG_INTERVAL))
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, config.LOG_INTERVAL * 1000)
    machine.deepsleep()


def load_image(filename):
    with open(filename, 'rb') as f:
        f.readline()
        f.readline()
        width, height = [int(v) for v in f.readline().split()]
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)


def display_dht11(temperature, humidity):
    # display_i2c = machine.I2C(scl=pcf.pin(0), sda=pcf.pin(1))
    if 60 not in i2c.scan():
        raise RuntimeError('Cannot find display.')

    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    font_writer = writer.Writer(display, freesans20)

    temperature_pbm = load_image('temperature.pbm')
    units_pbm = load_image('fahrenheit.pbm') if config.FAHRENHEIT \
        else load_image('celsius.pbm')
    humidity_pbm = load_image('humidity.pbm')
    percent_pbm = load_image('percent.pbm')

    display.fill(0)
    display.rect(0, 0, 128, 64, 1)
    display.line(64, 0, 64, 64, 1)
    display.blit(temperature_pbm, 24, 4)
    display.blit(humidity_pbm, 88, 4)
    display.blit(units_pbm, 28, 52)
    display.blit(percent_pbm, 92, 52)

    text = '{:.1f}'.format(temperature)
    textlen = font_writer.stringlen(text)
    font_writer.set_textpos((64 - textlen) // 2, 30)
    font_writer.printstring(text)

    text = '{:.1f}'.format(humidity)
    textlen = font_writer.stringlen(text)
    font_writer.set_textpos(64 + (64 - textlen) // 2, 30)
    font_writer.printstring(text)

    display.show()
    time.sleep(10)
    display.poweroff()

def fanPower(direction, bool):
    if direction == "in" and bool == True:
        pcf.pin(config.FAN_IN_T_PIN, 0)
    elif direction == "in" and bool == False:
        pcf.pin(config.FAN_IN_T_PIN, 1)

    if direction == "out" and bool == True:
        pcf.pin(config.FAN_IN_B_PIN, 0)
    elif direction == "out" and bool == False:
        pcf.pin(config.FAN_IN_B_PIN, 1)

def diffuserPower(bool):
    if bool == True:
        pcf.pin(config.DIFFUSER_PIN, 0)
    elif bool == False:
        pcf.pin(config.DIFFUSER_PIN, 1)


def run():
    while True:
        try:
            # connect to local wifi
            connect_wifi()

            # get temperature and humidity from sensors
            temperature, humidity = get_temperature_and_humidity()

            # prints Temperature and Humidity in console while connected to machine

            print('Temperature = {temperature}, Humidity = {humidity}'.format(
                temperature=temperature, humidity=humidity))

            # prints Temperature and Humidity to OLED screen
            display_dht11(temperature, humidity)

            # sends data to ThingSpeak.io
            log_data(temperature, humidity)

            """
            testing relay switches for fans and diffuser

            intake fans will power on while temperature is above 23C, else they will power off
            
            exhaust fans will power on every even number minutes, else they will power off

            diffuser will power on while relative humidity is below 28%, else it will power off while relative humidity is above 32%
            """
            
            if temperature > 23:
                fanPower("in", True)
            else:
                fanPower("in", False)
        
            if time.gmtime()[4] % 2 == 0:
                fanPower("out", True)
            else:
                fanPower("out", False)
            
            if humidity < 28:
                diffuserPower(True)
            elif humidity > 32:
                diffuserPower(False)
            
        except Exception as exc:
            sys.print_exception(exc)
            show_error()

        if not is_debug():
            deepsleep()


run()

