import os
import sys
import time
import argparse
import subprocess
import requests
from datetime import datetime
from threading import Thread

from apa102 import APA102

import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107

from picovoice import Picovoice
from pvrecorder import PvRecorder

RGB_COLORS = dict(
    blu=(0, 0, 255),
    bianco=(255 , 255 , 255),
    giallo=(255, 255, 255),
    rosso=(255, 0, 0),
    azzurro=(0, 255, 255),
    verde=(0, 255, 0),
    arancione=(255, 128, 0),
    rosa=(255, 51, 153),
    viola=(204, 0, 204),
    off=(0, 0, 0),
)

ROOMS = {
    'cucina' : 0,
    'soggiorno' : 1,
    'salotto' : 1,
    'camera' : 2,
    'camera da letto' : 2,
    'stanza' : 2,
    'stanza da letto' : 2,
}

num_led = 3
led_driver = APA102(num_led=num_led)

displayio.release_displays()
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
WIDTH = 128
HEIGHT = 128
display = adafruit_displayio_sh1107.SH1107(display_bus, width=WIDTH, height=HEIGHT, display_offset=adafruit_displayio_sh1107.DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297, rotation=180)


class PiVoice(Thread):

    def __init__(self, keyword_path, context_path, access_key, device_index, recorder, porcupine_sensitivity=0.75, rhino_sensitivity=0.25):
        super(PiVoice, self).__init__()

        def inference_callback(inference):
            return self.inference_callback(inference)

        self.picovoice = Picovoice(access_key=access_key, keyword_path=keyword_path, wake_word_callback=self.wakeword_callback, context_path=context_path, inference_callback=inference_callback, porcupine_sensitivity=porcupine_sensitivity, rhino_sensitivity=rhino_sensitivity)

        self.context = self.picovoice.context_info

        self._default_color = 'bianco'
        self._default_brightness = 20
        self._device_index = device_index
        self.recorder = recorder
        
        for i in range(0, num_led):
            led_driver.set_brightness(i, self._default_brightness)

    @staticmethod
    def set_color(led_index, color):
        led_driver.set_pixel(led_index, color[0], color[1], color[2])
        led_driver.show()
        
    def set_led_brightness(self, room, brightness):
        if room is not None:
            led_driver.set_brightness(ROOMS[room], brightness)
        else:
            for i in range(0, num_led):
                led_driver.set_brightness(i, brightness)
        led_driver.show()
        
    def set_led_color(self, room, color):
        new_color = self._default_color
        if color is not None:
            new_color = color
        if room is not None:
            led_driver.set_pixel(ROOMS[room], RGB_COLORS[new_color][0], RGB_COLORS[new_color][1], RGB_COLORS[new_color][2])
        else:
            for i in range(0, num_led):
                led_driver.set_pixel(i, RGB_COLORS[new_color][0], RGB_COLORS[new_color][1], RGB_COLORS[new_color][2])
        led_driver.show()
    
    def show_image(self, path):
        group = displayio.Group()
        bitmap = displayio.OnDiskBitmap(path)
        tile_grid = displayio.TileGrid(bitmap, pixel_shader = bitmap.pixel_shader)
        group.append(tile_grid)
        display.show(group)
        time.sleep(3)
        group = displayio.Group()
        display.show(group)
        
    def show_text(self, text):
        group = displayio.Group()
        for label in text:
            group.append(label)
        display.show(group)
        time.sleep(3)
        group = displayio.Group()
        display.show(group)

    @staticmethod
    def wakeword_callback():
        print('[wake word]\n')

    def inference_callback(self, inference):
        print("is_understood: " + str(inference.is_understood))
        if inference.is_understood:
            print("intent: " + str(inference.intent))
            if (len(inference.slots) > 0):
                print("slots:")
                
                for slot, value in inference.slots.items():
                    print(str(slot) + " : " + str(value))

            if inference.intent == "accendereLuce":
                self.set_led_color(inference.slots.get("stanza"), inference.slots.get("colore"))
                
            elif inference.intent == "cambiareColore":         
                self.set_led_color(inference.slots.get("stanza"), inference.slots.get("colore"))
                
            elif inference.intent == "spegnereLuce":
                self.set_led_color(inference.slots.get("stanza"), "off")
                
            elif inference.intent == "cambiareLuminosità":      
                self.set_led_brightness(inference.slots.get("stanza"), int(inference.slots.get("lumdec")))
                
            elif inference.intent == "mostraOrario":
                self.recorder.stop()
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                text_area = [label.Label(terminalio.FONT, text=current_time, scale=4, color=0xFFFFFF, x=4, y=64)]
                self.show_text(text_area)
                self.recorder.start()
                    
            elif inference.intent == "mostraMeteo":
                
                city = inference.slots.get("citta")
                url = f"http://api.weatherapi.com/v1/current.json?key=06754c26bc8542fe9b0122754230410&q={city}&aqi=no"            
                
                try:
                    r = requests.get(url)
                    if r.status_code == 200:
                        body = r.json()['current']
                        temp = str(body['temp_c']) + "C"
                        cond_code = str(body['condition']['code'] - 887)
                        path = "./pic/weather/" + cond_code + ".bmp"
                        hum = str(body['humidity']) + "%"
                        
                        self.recorder.stop()
                        self.show_image(path)
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="TEMP", scale=5, color=0xFFFFFF, x=4, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=temp, scale=4, color=0xFFFFFF, x=4, y=96))
                        self.show_text(text_area)
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="HUM", scale=6, color=0xFFFFFF, x=8, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=hum, scale=6, color=0xFFFFFF, x=8, y=96))
                        self.show_text(text_area)
                        self.recorder.start()
                    else:
                        print(r.json())
                except requests.ConnectionError:
                    print("Failed to connect!")                
            else:
                raise NotImplementedError()                 #Gestire

    def run(self):
        self.recorder = None

        try:
            self.recorder = PvRecorder(device_index=self._device_index, frame_length=self.picovoice.frame_length)
            self.recorder.start()

            print(self.context)

            print("Listening")

            while True:
                pcm = self.recorder.read()
                self.picovoice.process(pcm)
        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print("Exiting...")
        finally:
            if self.recorder is not None:
                self.recorder.delete()

            self.picovoice.delete()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--microphone_index",
                        help="Index of input audio device",
                        type=int,
                        default=-1)

    args = parser.parse_args()

    recorder = None
    access_key = "gLEeR53xMGRwaC2Bd1G7xEtpA21zkSZJW2GDp1783UbsCcBJ9ceMDQ=="
    app = PiVoice(os.path.join(os.path.dirname(__file__), 'porcupine.ppn'),
                  os.path.join(os.path.dirname(__file__), 'rhino.rhn'),
                  access_key,
                  args.microphone_index,
                  recorder)

    app.run()

'''
group = displayio.Group()
display.show(group)
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle in black
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

# Draw some white squares
sm_bitmap = displayio.Bitmap(8, 8, 1)
sm_square = displayio.TileGrid(sm_bitmap, pixel_shader=color_palette, x=58, y=17)
splash.append(sm_square)

med_bitmap = displayio.Bitmap(16, 16, 1)
med_square = displayio.TileGrid(med_bitmap, pixel_shader=color_palette, x=71, y=15)
splash.append(med_square)

lrg_bitmap = displayio.Bitmap(32, 32, 1)
lrg_square = displayio.TileGrid(lrg_bitmap, pixel_shader=color_palette, x=91, y=28)
splash.append(lrg_square)

# Draw some label text
text1 = "0123456789ABCDEF123456789AB"  # overly long to see where it clips
text_area = label.Label(terminalio.FONT, text=text1, color=0xFFFFFF, x=8, y=8)
splash.append(text_area)
text2 = "SH1107"
text_area2 = label.Label(
    terminalio.FONT, text=text2, scale=2, color=0xFFFFFF, x=9, y=44
)
splash.append(text_area2)
bitmap = displayio.OnDiskBitmap("pic/rasplogo2.bmp")
tile_grid = displayio.TileGrid(bitmap, pixel_shader = bitmap.pixel_shader)
splash.append(tile_grid)
display.show(splash)

time.sleep(2)

splash = displayio.Group()
display.show(splash)
'''
        
        
