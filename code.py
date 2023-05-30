import time
import os, sys, ipaddress, wifi, gc, io
import rtc
import supervisor
# Power on the power led
# Imports for scan and read
import board
import busio
import digitalio

# Reload
try:
    DNS = "gafi.hopto.org"
    # For LCD Display 1.8
    from adafruit_st7735r import ST7735R
    import displayio
    import terminalio
    from adafruit_display_text import label

    LCD_CS = board.GP18
    LCD_RESET = board.GP17
    LCD_DC = board.GP16
    LCD_SDA = board.GP6
    LCD_SCL = board.GP7

    # Initialize the display
    displayio.release_displays()

    SPI_LCD = busio.SPI(clock=LCD_SDA, MOSI=LCD_SCL)
    display_bus = displayio.FourWire(SPI_LCD, command=LCD_DC, chip_select=LCD_CS, reset=LCD_RESET)
    display = ST7735R(display_bus, width=128, height=160)
    splash = displayio.Group()

    # We are on usb
    on_battery = 0
    # Define the digital input pin for the control button
    control_button = digitalio.DigitalInOut(board.GP22)
    control_button.switch_to_input(pull=digitalio.Pull.UP)

    in_min,in_max,out_min,out_max = (0, 65000, -5, 5)
    filter_joystick_deadzone = lambda x: int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min) if abs(x - 32768) > 500 else 0


    # RGB LED
    led_r = digitalio.DigitalInOut(board.GP19)
    led_r.direction = digitalio.Direction.OUTPUT
    led_g = digitalio.DigitalInOut(board.GP20)
    led_g.direction = digitalio.Direction.OUTPUT
    led_b = digitalio.DigitalInOut(board.GP21)
    led_b.direction = digitalio.Direction.OUTPUT

    def busy_status():
        #led_r.value = True
        led_g.value = True
        led_b.value = True

    # Busy status on
    busy_status()

    def ready_status():
        led_r.value = False
        led_g.value = True
        led_b.value = False

    def running_status():
        led_r.value = False
        led_g.value = False
        led_b.value = True

    gc.collect()
    # https://learn.adafruit.com/pico-w-wifi-with-circuitpython/overview
    # https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
    print("Connecting to WiFi")

    try:
        # Connect to the WIFI, use settings.toml to configure SSID and Password
        wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
        print("Connected to WiFi")
    except Exception as e:
        # Handle connection error
        # For this example we will simply print a message and exit the program
        print("Failed to the first network, trying mobile hotspot.")
        try:
            # Connect to the WIFI, use settings.toml to configure SSID and Password
            wifi.radio.connect(os.getenv('WIFI_SSID1'), os.getenv('WIFI_PASSWORD1'))
            print("Connected to WiFi")
        except Exception as e:
            # Handle connection error
            # For this example we will simply print a message and exit the program
            print("Failed to connect to hotspot.")
            print("Error:\n", str(e))
            # Connect to UPB
            try:
                # Connect to the WIFI, use settings.toml to configure SSID and Password
                wifi.radio.connect(os.getenv('WIFI_FAC'))
                print("Connected to WiFi")
            except Exception as e:
                # Handle connection error
                # For this example we will simply print a message and exit the program
                print("Failed to connect, aborting.")
                print("Error:\n", str(e))
                sys.exit()

    # Prints your MAC (Media Access Control) address
    print("MAC addr:", [hex(i) for i in wifi.radio.mac_address])

    # Prints your IP address
    print("IP address is", wifi.radio.ipv4_address)

    import adafruit_requests
    import socketpool
    import ssl
    import json

    import adafruit_dht
    # Temperature sensor
    dht_device = adafruit_dht.DHT11(board.GP4)

    # Current language
    current_language = "en-us"

    # https://learn.adafruit.com/pico-w-wifi-with-circuitpython/pico-w-requests-test-adafruit-quotes
    # https://learn.adafruit.com/generating-text-with-chatgpt-pico-w-circuitpython?view=all
    # https://learn.adafruit.com/generating-text-with-chatgpt-pico-w-circuitpython/code-walkthrough
    # https://learn.adafruit.com/circuitpython-essentials/circuitpython-uart-serial
    # https://www.instructables.com/Bluetooth-ModuleHC-05-With-Raspberry-Pi-Pico/

    import adafruit_sdcard
    import storage
    import microcontroller


    SCK = board.GP10
    MOSI = board.GP11
    MISO = board.GP12
    CS = board.GP13


    # Set up the pins
    sd_cs = digitalio.DigitalInOut(CS)

    spi = busio.SPI(SCK, MOSI, MISO)

    # Mount the SD card
    try:
        sdcard = adafruit_sdcard.SDCard(spi, sd_cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
    except Exception as e:
        print("Error mounting SD card:", e)
        supervisor.reload()
    else:
        print("SD card mounted!")
    del SCK
    del MOSI
    del MISO
    del CS
    gc.collect()


    # Audio pin for tracks
    # https://community.element14.com/products/raspberry-pi/f/forum/49722/mp3-playback-on-pi-pico
    import audiomp3
    import audiopwmio
    import audiocore

    AUDIO_PIN = board.GP26
    #AUDIO_PIN_RIGHT = board.GP27

    def fun_audio_silent():
        audio_silent = digitalio.DigitalInOut(AUDIO_PIN)
        audio_silent.direction = digitalio.Direction.OUTPUT
        audio_silent.value = 0

    #fun_audio_silent()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    weather_api_key = os.getenv("WEATHER_API_KEY")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    esp32_api_key = os.getenv("ESP32_API_KEY")

    TXD = board.GP0
    RXD = board.GP1
    uart = busio.UART(TXD, RXD, baudrate=9600, timeout=2)
    del TXD
    del RXD
    gc.collect()

    prefix = "!"

    def to_display():
        # Draw a label
        # Set text, font, and color
        text = "HELLO WORLD"
        font = terminalio.FONT
        color = 0xFFFFFF

        # Create the text label
        text_area = label.Label(font, text=text, color=color)

        # Set the location
        text_area.x = 5
        text_area.y = 5

        # Show it
        display.show(text_area)
        del text_area
        del text
        del font
        del color
        gc.collect()
        return


    # Intrerupt button
    PIN_BUTTON_RED = board.GP5
    button_stop = digitalio.DigitalInOut(PIN_BUTTON_RED)
    button_stop.switch_to_input(pull=digitalio.Pull.UP)
    del PIN_BUTTON_RED
    gc.collect()

    # For joystick
    from analogio import AnalogIn
    import usb_hid
    from adafruit_hid.mouse import Mouse

    try:
        mouse = Mouse(usb_hid.devices)
    except:
        uart.write(bytes("Powered by battery!\n", "ascii"))
        on_battery = 1

    xAxis = AnalogIn(board.GP27)
    yAxis = AnalogIn(board.GP28)



    def gpt_response_play():
        uart.write(bytes("Playing audio ...\n", "ascii"))
        print("Playing audio ...")
        #del audio_silent
        #gc.collect()
        audio = audiopwmio.PWMAudioOut(AUDIO_PIN)
        file_input = open("/sd/reply.mp3", "rb")
        decoder = audiomp3.MP3Decoder(file_input)
        audio.play(decoder)
        running_status()
        while audio.playing:
            # Button stop
            if not button_stop.value:
                break
            if uart.in_waiting > 0:
                data = uart.readline()
                data_string = ''.join([chr(b) for b in data])
                if data_string is not None and len(data) > 1:
                    # Stop command
                    if data_string.startswith(prefix + "stop"):
                        break
                    # Pause command
                    if data_string.startswith(prefix + "pause"):
                        audio.pause()
                    # Resume command
                    if data_string.startswith(prefix + "resume"):
                        audio.resume()
            pass
        audio.deinit()
        file_input.close()
        del audio
        del file_input
        del decoder
        gc.collect()
        uart.write(bytes("Done playing!\n", "ascii"))
        print("Done playing!")
        #fun_audio_silent()
        return

    def gpt_download_voice(content):
        uart.write(bytes("Downloading ...\n", "ascii"))
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        content.replace("\n\n"," ")
        content.replace("\n"," ")
        # Voice action
        if (current_language == "ro-ro"):
            querystring = {f"hl":"ro-ro","src":{content},"key":"64c8a7091a0340809da0b2293e977757","f":"32khz_16bit_mono","c":"mp3","r":"0"}
        if (current_language == "en-us"):
            querystring = {f"hl":"en-us","src":{content},"key":"64c8a7091a0340809da0b2293e977757","f":"32khz_16bit_mono","c":"mp3","r":"0"}

        url_voice = "https://voicerss-text-to-speech.p.rapidapi.com/"

        url_voice += "?" + "&".join([f"{key}={value}" for key, value in querystring.items()])

        headers = {
        "X-RapidAPI-Key": "6286c9481dmsh0572b524c693813p1e7022jsn262937025a7b",
        "X-RapidAPI-Host": "voicerss-text-to-speech.p.rapidapi.com"
        }

        response = requests.get(url_voice, headers=headers)
        del querystring
        del url_voice
        del headers

        print("Saving mp3 ...")
        uart.write(bytes("Saving mp3 ...\n", "ascii"))
        output_file_name = "/sd/reply.mp3"
        with open(output_file_name, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=2048):
                if chunk:
                    output_file.write(chunk)
                    #del chunk
                    #gc.collect()

        del content
        del output_file_name
        del response
        del requests
        del pool
        del ssl_context
        gc.collect()
        return

    import array
    import math
    def gpt_download_wave_voice(content):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        content.replace("\n\n"," ")
        content.replace("\n"," ")
        # Voice action
        if (current_language == "ro-ro"):
            querystring = {f"hl":"ro-ro","src":{content},"key":"64c8a7091a0340809da0b2293e977757","f":"32khz_16bit_mono","c":"wav","r":"0"}
        if (current_language == "en-us"):
            querystring = {f"hl":"en-us","src":{content},"key":"64c8a7091a0340809da0b2293e977757","f":"32khz_16bit_mono","c":"wav","r":"0"}

        url_voice = "https://voicerss-text-to-speech.p.rapidapi.com/"

        url_voice += "?" + "&".join([f"{key}={value}" for key, value in querystring.items()])

        headers = {
        "X-RapidAPI-Key": "6286c9481dmsh0572b524c693813p1e7022jsn262937025a7b",
        "X-RapidAPI-Host": "voicerss-text-to-speech.p.rapidapi.com"
        }

        response = requests.get(url_voice, headers=headers, stream=True)
        del querystring
        del url_voice
        del headers
        # Try to save and play

        print("Saving wav ...")
        output_file_name = "/sd/reply.wav"
        audio = audiopwmio.PWMAudioOut(AUDIO_PIN)
        total_len = 0
        my_chunk = array.array("b", [])
        for chunk in response.iter_content(8):
            total_len += len(chunk)
            my_chunk.extend(chunk)
            if (total_len % 2 == 0):
                decoder = array.array("b", my_chunk)
                decoder = audiocore.RawSample(decoder)
                audio.play(decoder, loop=False)
                total_len = 0
                my_chunk = array.array("b", [])
                del decoder
                del chunk
                gc.collect()
                continue
            del chunk
            gc.collect()

            continue
        del content
        del response
        del requests
        del pool
        del ssl_context
        gc.collect()
        return


    # Create the gpt call
    def gpt_request(payload):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        full_prompt = [{"role": "user", "content": payload},]

        with requests.post("https://api.openai.com/v1/chat/completions",
            json={"model": "gpt-3.5-turbo", "messages": full_prompt},
            headers={
            "Authorization": f"Bearer {openai_api_key}",
            },
            ) as response:
                json_data = json.loads(response.content)
                content = json_data['choices'][0]['message']['content']
                del response
                del json_data
                gc.collect()

        del payload
        del full_prompt
        del requests
        del pool
        del ssl_context
        gc.collect()
        content.strip()
        content.replace("\n\n"," ")
        content.replace('\n',' ')
        return content

    def current_weather(location):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        api_key = weather_api_key
        lat = "44.439"
        lon = "26.102"
        if location is not None and len(location) > 2:
            payload_gpt = f"Compute a text about the weather using the bellow json and the location being {location}, without time and give directly the answer"
            # Get current longitute and latitude of location
            url_location = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit={3}&appid={api_key}"
            response = requests.get(url_location)
            json_data = json.loads(response.content)
            lat = json_data[0]['lat']
            lon = json_data[0]['lon']
            del response
            del url_location
            gc.collect()
        else:
            payload_gpt = f"Compute a text about the weather using the bellow json and the location being Bucharest, without time and give directly the answer"

        if (current_language == "ro-ro"):
            payload_gpt = payload_gpt + "\n" + "show only the translation in romanian"
        if (current_language == "en-us"):
            payload_gpt = payload_gpt + "\n" + "in English"

        # This is working for resolved lat and lon
        exclude = "hourly,daily"
        units = "metric"
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={exclude}&appid={api_key}&units={units}"
        response = requests.get(url)
        json_data = json.loads(response.content)
        payload_gpt = payload_gpt + "\n" + json.dumps(json_data)

        del json_data
        del response
        del exclude
        del units
        del url
        del lat
        del lon
        del api_key
        del requests
        del pool
        del ssl_context
        gc.collect()

        content = gpt_request(payload_gpt)
        print(content)
        content_uart = bytearray("\n" + content + "\n")
        uart.write(content_uart)
        gpt_download_voice(content)
        gpt_response_play()
        del content
        del content_uart
        del payload_gpt
        gc.collect()
        # https://openweathermap.org/api/one-call-3

    def current_esp32_stats_voice():
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        if (current_language == "ro-ro"):
            payload_gpt = f"Scrie un scurt text despre statisticile: "
        if (current_language == "en-us"):
            payload_gpt = f"Compute a short text about the stats: "

        # Request to my ESP32_API
        url = f"http://{DNS}:5001/bme_get?api_key={esp32_api_key}"
        response = requests.get(url)
        json_data = json.loads(response.content)

        del response
        del url
        del requests
        del pool
        del ssl_context
        gc.collect()

        content = json.loads(json_data['content'])
        room_temperature = content['room_temperature']
        room_pressure = content['room_pressure']
        altitude = content['altitude']
        humidity = content['humidity']
        gas = content['gas']
        text = f"Room Temperature: {room_temperature} C\nRoom Pressure: {room_pressure}\nRoom Humidity: {humidity} %\nAltitude: {altitude}\nGas: {gas}"
        print(text)
        content_uart = bytes(text + "\n", "ascii")
        uart.write(content_uart)
        payload_gpt = payload_gpt + "\n" + text

        resp = gpt_request(payload_gpt)
        gpt_download_voice(resp)
        gpt_response_play()
        del room_temperature
        del room_pressure
        del altitude
        del humidity
        del gas
        del text
        del content_uart
        del json_data
        del content
        del payload_gpt
        del resp
        gc.collect()

    def current_esp32_stats():
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        # Request to my ESP32_API
        url = f"http://{DNS}:5001/bme_get?api_key={esp32_api_key}"
        response = requests.get(url)
        json_data = json.loads(response.content)
        del response
        del url
        del requests
        del pool
        del ssl_context
        gc.collect()

        content = json.loads(json_data['content'])
        room_temperature = content['room_temperature']
        room_pressure = content['room_pressure']
        altitude = content['altitude']
        humidity = content['humidity']
        gas = content['gas']
        text = f"Room Temperature: {room_temperature} C\nRoom Pressure: {room_pressure}\nRoom Humidity: {humidity} %\nAltitude: {altitude}\nGas: {gas}"
        print(text)
        content_uart = bytes(text + "\n", "ascii")
        uart.write(content_uart)
        del room_temperature
        del room_pressure
        del altitude
        del humidity
        del gas
        del text
        del content_uart
        del json_data
        del content
        gc.collect()
        # https://openweathermap.org/api/one-call-3


    def five_days_weather(location):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        api_key = weather_api_key
        lat = "44.439"
        lon = "26.102"
        if location is not None and len(location) > 2:
            payload_gpt = f"Compute a text about the weather using the bellow json and the location being {location}, without time and give directly the answer, without talking about based data provided"
            # Get current longitute and latitude of location
            url_location = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=3&appid={api_key}"
            response = requests.get(url_location)
            json_data = json.loads(response.content)
            lat = json_data[0]['lat']
            lon = json_data[0]['lon']
            print("Searching for weather in {}...".format(location))
            uart.write(bytes(f"Searching for weather in {location} ...\n", "ascii"))
        else:
            payload_gpt = f"Compute a text about the weather using the bellow json and the location being Bucharest, without time and give directly the answer"
            print("Searching for weather in Bucharest ... ")
            uart.write(bytes("Searching for weather in Bucharest ...\n", "ascii"))

        if (current_language == "ro-ro"):
            payload_gpt = payload_gpt + "\n" + "show only the translation in romanian"
        if (current_language == "en-us"):
            payload_gpt = payload_gpt + "\n" + "in English"

        # This is working for resolved lat and lon
        exclude = ""
        units = "metric"
        lang = "en-us"
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&cnt=2&appid={api_key}&units={units}"
        response = requests.get(url)
        json_data = json.loads(response.content)
        payload_gpt = payload_gpt + "\n" + json.dumps(json_data)
        del json_data
        del response
        del exclude
        del units
        del url
        del lat
        del lon
        del api_key
        del requests
        del pool
        del ssl_context
        gc.collect()

        content = gpt_request(payload_gpt)
        print(content)
        content_uart = bytearray("\n" + content + "\n")
        uart.write(content_uart)
        gpt_download_voice(content)
        gpt_response_play()
        del content
        del payload_gpt
        gc.collect()
        # https://openweathermap.org/api/one-call-3#multi

    def play_from_sd(track):
        #audio_silent.deinit()
        #del audio_silent
        #gc.collect()
        print("Playing audio")
        uart.write(bytes("Playing audio\n", "ascii"))
        buffer = bytearray(1024)
        # audio = audiopwmio.PWMAudioOut(left_channel=AUDIO_PIN, right_channel=AUDIO_PIN_RIGHT, quiescent_value=32768)
        audio = audiopwmio.PWMAudioOut(AUDIO_PIN)
        file_input = open(track, "rb")
        decoder = audiomp3.MP3Decoder(file_input, buffer)
        #decoder.sample_rate = 32000
        audio.play(decoder)
        running_status()
        while audio.playing:
            # Button stop
            if not button_stop.value:
                break
            if uart.in_waiting > 0:
                data = uart.readline()
                data_string = ''.join([chr(b) for b in data])
                if data_string is not None and len(data) > 1:
                    # Stop command
                    if data_string.startswith(prefix + "stop"):
                        break
                    # Pause command
                    if data_string.startswith(prefix + "pause"):
                        audio.pause()
                    # Resume command
                    if data_string.startswith(prefix + "resume"):
                        audio.resume()
            pass

        print("Done playing!")
        uart.write(bytes("Done playing!\n", "ascii"))
        audio.deinit()
        del decoder
        del audio
        file_input.close()
        del file_input
        del buffer
        gc.collect()
        #fun_audio_silent()
        return

    def youtube_music(payload):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        print("Searching for {}...".format(payload))
        uart.write(bytes(f"Searching for {payload} ...\n", "ascii"))
        url_ytb = f"http://{DNS}:5000/get_link?api_key={youtube_api_key}&payload={payload}"
        response = requests.get(url_ytb)
        url_song = json.loads(response.content)
        song_id = url_song['video_id']
        song_id += ".mp3"
        url_song = url_song['message']
        print("Gasit link:")
        print(url_song)
        uart.write(bytes(f"Gasit link: {url_song}\n", "ascii"))
        del payload
        del url_ytb
        del requests
        del pool
        del ssl_context
        gc.collect()
        song_location = "/sd/" + song_id
        # If we already have this track saved
        if song_id in os.listdir("/sd/"):
            print("Piesa gasita!")
            uart.write(bytes("Piesa gasita!\n", "ascii"))
            play_from_sd(song_location)
            del song_location
            del song_id
            gc.collect()
            return
        # We don't have the track saved
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        url_ytb = f"http://{DNS}:5000/download_mp3_url?api_key={youtube_api_key}&payload={url_song}"
        response = requests.get(url_ytb, stream=True)

        output_file_name = song_location
        print("Downloading track ...")
        uart.write(bytes("Downloading track ...\n", "ascii"))
        with open(output_file_name, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    output_file.write(chunk)
                    #del chunk
                    #gc.collect()
        time.sleep(1)
        del url_song
        del url_ytb
        del requests
        del pool
        del ssl_context
        del song_id
        del song_location
        gc.collect()
        play_from_sd(output_file_name)
        del output_file_name
        del response
        gc.collect()

    def play_music(payload):
        # We need this for connection
        pool = socketpool.SocketPool(wifi.radio)
        ssl_context = ssl.create_default_context()
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

        print("Searching for {}...".format(payload))
        uart.write(bytes(f"Searching for {payload} ...\n", "ascii"))
        # Find the SoundCloud URL for this track
        payload = payload.replace(" ", "+")
        url_search = f"https://soundcloud-downloader4.p.rapidapi.com/soundcloud/search?query={payload}"
        headers = {
        "X-RapidAPI-Key": "6286c9481dmsh0572b524c693813p1e7022jsn262937025a7b",
        "X-RapidAPI-Host": "soundcloud-downloader4.p.rapidapi.com"
        }
        response = requests.get(url_search, headers=headers, stream=True)
        song_list = []
        for chunk in response.iter_content(chunk_size=1024):
            song_list.append(chunk)
            del chunk
            gc.collect()
        song_list = json.loads(b''.join(song_list).decode('utf-8'))
        print("Gasit link:")
        print(song_list['result'][0]['url'])
        uart.write(bytes(f"\nGasit link: {song_list['result'][0]['url']}\n", "ascii"))
        url_song = song_list['result'][0]['url']
        #url_file = "https://cf-media.sndcdn.com/e7WcAPIUi51X.128.mp3?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiKjovL2NmLW1lZGlhLnNuZGNkbi5jb20vZTdXY0FQSVVpNTFYLjEyOC5tcDMqIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNjgxNTAxNjI0fX19XX0_&Signature=MoSXpysLyiWiLAgZfLTD6zvUO2q5Nbl-urN1i2ssv18iem~u8FNI2kWg-CPXFu0byZxxx6FY6Hdm7O6pvxVM2UCGdmMDDlkdZuiC~Hz0YuIWRyuz1vGslXuEdkY0a2iBhK-03qhAojQH1PdQ-TTGmEdfDjlBofUOhS7TXGQq8dIdKwhIMIMmSk4DkDBGHJEL9qIF8caEyP0Xw9hWF8pRTCAz4Jx~P-dEcbC1BrhQg0gx-YdqELkqKdqFEuSLKg7iL6kUCPrijyCAss7ANZ9XbtumSaDR7hjVJKMUX0OMb1nGgplKfGAIUxQpDm359JQfVmsqjr3NA15dcTPyN0xszw__&Key-Pair-Id=APKAI6TU7MMXM5DG6EPQ"

        # Remove variables
        del url_search
        del headers
        del payload
        del song_list
        del response
        gc.collect()

        # Find the url song
        headers = {
        "X-RapidAPI-Key": "6286c9481dmsh0572b524c693813p1e7022jsn262937025a7b",
        "X-RapidAPI-Host": "soundcloud-downloader4.p.rapidapi.com"
        }

        url_song = f"https://soundcloud-downloader4.p.rapidapi.com/soundcloud/track?url={url_song}"
        url_file = requests.get(url_song, headers=headers)
        url_file = json.loads(url_file.content)
        url_file = url_file['music']['download_url']

        response = requests.get(url_file)

        output_file_name = "/sd/song.mp3"

        print("Downloading track ...")
        uart.write(bytes("Downloading track ...\n", "ascii"))
        with open(output_file_name, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    output_file.write(chunk)
                    #del chunk
                    #gc.collect()
        time.sleep(1)
        del url_file
        del url_song
        del ssl_context
        del pool
        del requests
        del response
        gc.collect()
        play_from_sd(output_file_name)
        print("Done playing!")
        uart.write(bytes("Done playing!\n", "ascii"))
        return

    def play_game(no_letters):
        payload = f"Trimite-mi raspunsul doar sub forma de text json, fara introducere, un cuvant in campul 'cuvant' de {no_letters} litere si definitia acestuia in 'definitie' fara alt text in romana, fara diacritice in raspuns"
        #response = gpt_request(payload)
        #response = json.loads(response)
        #print("Cuvantul", response['cuvant'])
        #print("Definitie", response['definitie'])

        # Initialize the display
        displayio.release_displays()

        # Draw a label
        # Fill the screen with black color to clear it
        color_bitmap = displayio.Bitmap(display.width, display.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x1573ED  # Set the color to black
        bg_sprite = displayio.TileGrid(color_bitmap, x=0, y=0, pixel_shader=color_palette)
        splash.append(bg_sprite)
        text_group = displayio.Group(scale=1, x=11, y=12)
        text = "Jocul cuvintelor"
        current_time = rtc.RTC()
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
        text_group.append(text_area)  # Subgroup for text scaling
        splash.append(text_group)
        display.show(splash)
        del text_group
        del text
        gc.collect()

        splash = displayio.Group()
        return



    def mouse_move():
        uart.write(bytes("Mouse Control\n", "ascii"))
        running_status()
        is_pressed = 0
        while True:
            # Intrerupt
            if not button_stop.value:
                return
            x_offset = filter_joystick_deadzone(xAxis.value) * -1
            y_offset = filter_joystick_deadzone(yAxis.value)
            mouse.move(2 * x_offset, - 2 * y_offset, 0)
            if not control_button.value and is_pressed == 0:
                # Perform a mouse click
                is_pressed = 1
                mouse.click(Mouse.LEFT_BUTTON)
                #mouse.press(Mouse.LEFT_BUTTON)
                time.sleep(0.1)
            if control_button.value and is_pressed == 1:
                #mouse.release(Mouse.LEFT_BUTTON)
                is_pressed = 0
                time.sleep(0.1)
            if uart.in_waiting > 0:
                data = uart.readline()
                data_string = ''.join([chr(b) for b in data])
                if data_string is not None and len(data) > 1:
                    # Stop command
                    if data_string.startswith(prefix + "stop"):
                        del data
                        del data_string
                        gc.collect()
                        break
        del is_pressed
        uart.write(bytes("Mouse oprit\n", "ascii"))
        gc.collect()
        return

    while True:
        # Not busy
        ready_status()
        if uart.in_waiting > 0:
            # Busy
            busy_status()
            gc.collect()
            data = uart.readline()
            data_string = ''.join([chr(b) for b in data])
            if data_string is not None and len(data) > 1:
                # Help command
                if data_string.startswith(prefix + "help"):
                    uart.write(bytes("Text interesant\n", "ascii"))
                    continue
                # Ping command
                if data_string.startswith(prefix + "ping"):
                    uart.write(bytes("Pong!\n", "ascii"))
                    print("Pong!")
                    continue
                if data_string.startswith(prefix + "psd"):
                    print("Playing the last track ...")
                    uart.write(bytes("Playing the last track ...\n", "ascii"))
                    play_from_sd("/sd/song.mp3")
                    continue
                # Music command
                if data_string.startswith(prefix + "p") or data_string.startswith(prefix + "play"):
                    words = data_string.split()
                    payload = ' '.join(words[1:])
                    youtube_music(payload)
                    del words
                    del payload
                    gc.collect()
                    continue
                # Act as a mouse
                if data_string.startswith(prefix + "mouse"):
                    if on_battery == 1:
                        uart.write(bytes("You have to be connected via microUSB to a device!\n", "ascii"))
                        print("You have to be connected via microUSB to a device!")
                    else:
                        mouse_move()
                    continue
                if data_string.startswith(prefix + "psc") or data_string.startswith(prefix + "playsc"):
                    words = data_string.split()
                    payload = ' '.join(words[1:])
                    play_music(payload)
                    del words
                    del payload
                    gc.collect()
                    continue
                # Restart command
                if data_string.startswith(prefix + "restart") or data_string.startswith(prefix + "reload"):
                    print("Reloading ...")
                    uart.write(bytes("Reloading ...\n", "ascii"))
                    time.sleep(3)
                    supervisor.reload()
                    continue
                # Tell command
                if data_string.startswith(prefix + "tell") or data_string.startswith(prefix + "say"):
                    words = data_string.split()
                    payload = ' '.join(words[1:])
                    gpt_download_voice(payload)
                    gpt_response_play()
                    del words
                    del payload
                    gc.collect()
                    continue
                # Memory available command
                if data_string.startswith(prefix + "memory") or data_string.startswith(prefix + "mem"):
                    my_data_string = f"Available memory: {gc.mem_free()}\n"
                    my_data = bytearray(my_data_string)
                    print(my_data_string)
                    uart.write(my_data)
                    del my_data
                    del my_data_string
                    gc.collect()
                    continue

                # Menu
                if data_string.startswith(prefix + "menu") or data_string.startswith(prefix + "meniu"):
                    to_display()
                    continue


                # ESP32 Stats Voice
                if data_string.startswith(prefix + "espv"):
                    current_esp32_stats_voice()
                    continue

                # ESP32 Stats
                if data_string.startswith(prefix + "esp"):
                    current_esp32_stats()
                    continue
                # Weather command
                if data_string.startswith(prefix + "wf") or data_string.startswith(prefix + "weather_future"):
                    words = data_string.split()
                    location = ' '.join(words[1:])
                    five_days_weather(location)
                    del words
                    del location
                    gc.collect()
                    continue
                # Weather future
                if data_string.startswith(prefix + "w") or data_string.startswith(prefix + "weather"):
                    words = data_string.split()
                    location = ' '.join(words[1:])
                    current_weather(location)
                    del words
                    del location
                    del data
                    del data_string
                    gc.collect()
                    continue
                # Repeat last answer GPT
                if data_string.startswith(prefix + "last"):
                    gpt_response_play()
                    continue
                # Language command
                if data_string.startswith(prefix + "lan") or data_string.startswith(prefix + "language"):
                    words = data_string.split()
                    lang_select = ' '.join(words[1:])
                    if (lang_select == "ro"):
                        print("Limba selectata: Romana")
                        uart.write(bytes("Limba selectata: Romana\n", "ascii"))
                        current_language = "ro-ro"
                    if (lang_select == "en"):
                        print("Selected language: English")
                        uart.write(bytes("Selected language: English\n", "ascii"))
                        current_language = "en-us"
                    continue
                # CPU Stats
                if data_string.startswith(prefix + "cpu"):
                    print("CPU Temperature: ", microcontroller.cpu.temperature)
                    uart.write(bytes(f"CPU Temperature: {microcontroller.cpu.temperature}°C\n", "ascii"))
                    continue
                # All stats
                if data_string.startswith(prefix + "stats"):
                    print("CPU temp:", microcontroller.cpu.temperature, "°C")
                    uart.write(bytes(f"CPU temp: {microcontroller.cpu.temperature}\n", "ascii"))
                    print(f"Mem: {gc.mem_free() / 1000}Kb")
                    uart.write(bytes(f"Mem: {gc.mem_free() / 1000}Kb\n", "ascii"))
                    print("Room temp:", dht_device.temperature,"°C")
                    uart.write(bytes(f"Room temp: {dht_device.temperature}\n", "ascii"))
                    print("Humidity:", dht_device.humidity,"%")
                    uart.write(bytes(f"Humidity: {dht_device.humidity}%\n", "ascii"))
                    gc.collect()
                    continue
                # Jocul cuvintelor
                if data_string.startswith(prefix + "game"):
                    print("Limba selectata: Romana")
                    current_language = "ro-ro"
                    words = data_string.split()
                    no_letters = ' '.join(words[1:])
                    no_letters = int(no_letters)
                    play_game(no_letters)
                    continue
                # Skip any message that starts with prefix
                if data_string.startswith(prefix):
                    continue
                # GPT Communication Message
                print("You: ")
                print(data_string)
                content = gpt_request(data_string)
                print("ChatGPT:")
                print(content)
                uart.write(bytes(f"ChatGPT: {content}\n", "ascii"))
                gpt_download_voice(content)
                gpt_response_play()
                del content
                gc.collect()
except Exception as e:
    print(e)
    time.sleep(7)
    supervisor.reload()
