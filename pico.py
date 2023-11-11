import os
import sys
import time
import argparse
import subprocess
import requests
from datetime import datetime
import threading
from threading import Thread, Lock

from apa102 import APA102

import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107

from picovoice import Picovoice
from pvrecorder import PvRecorder

import gtts
from io import BytesIO
import pydub
from pydub import AudioSegment
from pydub.playback import play

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

METEO = {
    1000: "Sereno",
    1003: "Parzialmente nuvoloso",
    1006: "Nuvoloso",
    1009: "Cielo coperto",
    1030: "Nebbia",
    1063: "Possibilità di pioggia sporadica",
    1066: "Possibilità di neve sporadica",
    1069: "Possibilità di nevischio sporadico",
    1072: "Possibilità di pioggerella con gelicidio sporadico",
    1087: "Possibilità di rovesci temporaleschi",
    1114: "Blizzard",
    1135: "Nebbia",
    1147: "Nebbia gelata",
    1150: "Possibilità di pioggerella leggera",
    1153: "Pioggerella leggera",
    1168: "Gelicidio leggero",
    1171: "Gelicidio intenso",
    1180: "Possibilità di pioggerella leggera",
    1183: "Pioggia leggera",
    1186: "Pioggia moderata a tratti",
    1189: "Pioggia moderata",
    1192: "Pioggia intensa a tratti",
    1195: "Pioggia intensa",
    1198: "Pioggia leggera con gelicidio",
    1201: "Gelicidio moderato o intenso",
    1204: "Nevischio leggero",
    1207: "Nevischio moderato o intenso",
    1210: "Possibilità di neve leggera",
    1213: "Neve leggera",
    1216: "Possibilità di neve moderata",
    1219: "Neve moderata",
    1222: "Possibilità di neve intensa",
    1225: "Neve intensa",
    1237: "Grandine",
    1240: "Rovescio di pioggia leggera",
    1243: "Rovescio di pioggia moderato o intenso",
    1246: "Rovescio di pioggia torrenziale",
    1249: "Rovescio di gelicidio leggero",
    1252: "Rovescio di gelicidio moderato o intenso",
    1255: "Rovescio di neve leggera",
    1258: "Rovescio di neve moderato o intenso",
    1261: "Rovescio di grandine leggera",
    1264: "Rovescio di grandine moderato o intenso",
    1273: "Possibilità di pioggia leggera con tuoni",
    1276: "Pioggia moderata o intensa con tuoni",
    1279: "Possibilità di neve leggera con tuoni",
    1282: "Neve moderata o intensa con tuoni"
}

num_led = 3
led_driver = APA102(num_led=num_led)
    
class DisplayManager:
    def __init__(self):
        displayio.release_displays()
        self.i2c = board.I2C()
        self.display_bus = displayio.I2CDisplay(self.i2c, device_address=0x3c)
        self.width = 128
        self.height = 128
        self.display = adafruit_displayio_sh1107.SH1107(self.display_bus, width=self.width, height=self.height, display_offset=adafruit_displayio_sh1107.DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297, rotation=180)
        
        self.show_stats = False        
        self.display_lock = Lock()
        self.display_condition = threading.Condition(lock=self.display_lock)
        
    def show_image(self, path, duration=3):
        group = displayio.Group()
        self.display.show(group)
        bitmap = displayio.OnDiskBitmap(path)
        tile_grid = displayio.TileGrid(bitmap, pixel_shader = bitmap.pixel_shader)            
        group.append(tile_grid)
        self.display.show(group)
        if duration > 0:
            time.sleep(duration)
            self.reset_display()

    def show_text(self, text, duration=3):
        group = displayio.Group()
        self.display.show(group)
        for label in text:
            group.append(label)
        self.display.show(group)
        if duration > 0:
            time.sleep(duration)
            self.reset_display()
            
    def reset_display(self):
        group = displayio.Group()
        self.display.show(group)
    
    def get_show_stats(self):
        return self.show_stats
    
    def set_show_stats(self, value):
        self.show_stats = value

class StatsCollector(Thread):
    def __init__(self, display_manager):
        super().__init__()
        self.display_manager = display_manager
        
    def run(self):
        while True:
            if self.display_manager.get_show_stats():
                #CALCOLA STATS
                cmd = "top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'"
                CPU = subprocess.check_output(cmd, shell = True, text=True)

                cmd = "free -m | awk 'NR==2{printf \"%s/%sMB\", $3, $2}'"    
                MemUsage = subprocess.check_output(cmd, shell = True, text=True)
                
                cmd = "df -h | awk '$NF==\"/\"{printf \"%d/%dGB %s\", $3,$2,$5}'"
                Disk = subprocess.check_output(cmd, shell = True, text=True)
                
                cmd = "vcgencmd measure_temp | cut -d '=' -f 2 | head --bytes -1"
                Temperature = subprocess.check_output(cmd, shell = True, text=True)
                
                text_area = []
                text_area.append(label.Label(terminalio.FONT, text="CPU:"+ CPU + "%", scale=2, color=0xFFFFFF, x=4, y=25))
                text_area.append(label.Label(terminalio.FONT, text=MemUsage, scale=2, color=0xFFFFFF, x=4, y=50))
                text_area.append(label.Label(terminalio.FONT, text=Disk, scale=2, color=0xFFFFFF, x=4, y=75))
                text_area.append(label.Label(terminalio.FONT, text=Temperature, scale=2, color=0xFFFFFF, x=4, y=100))
                #CHIAMA FUNZIONE PER MOSTRARE LE STATS
                lock_acquired = self.display_manager.display_lock.acquire(blocking=False)
                if lock_acquired:
                    try:
                        self.display_manager.show_text(text_area, duration=0)
                        time.sleep(0.2)
                    finally:
                        self.display_manager.display_lock.release()
            #SLEEP
            time.sleep(1)
            
def play_tts(text):
        mp3_fo = BytesIO()
        tts = gtts.gTTS(text, lang="it")
        tts.write_to_fp(mp3_fo)
        mp3_fo.seek(0)
        audio = AudioSegment.from_file(mp3_fo, format="mp3")
        play(audio)

class PiVoice(Thread):

    def __init__(self, keyword_path, context_path, access_key, device_index, recorder, display_manager, porcupine_sensitivity=0.75, rhino_sensitivity=0.25):
        super(PiVoice, self).__init__()

        def inference_callback(inference):
            return self.inference_callback(inference)

        self.picovoice = Picovoice(access_key=access_key, keyword_path=keyword_path, wake_word_callback=self.wakeword_callback, context_path=context_path, inference_callback=inference_callback, porcupine_sensitivity=porcupine_sensitivity, rhino_sensitivity=rhino_sensitivity)

        self.context = self.picovoice.context_info

        self._default_color = 'bianco'
        self._default_brightness = 10
        self._device_index = device_index
        self.recorder = recorder
        self.display_manager =  display_manager
        self.show_stats = False
        
        for i in range(0, num_led):
            led_driver.set_brightness(i, self._default_brightness)
            
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

    def wakeword_callback(self):
        print('[wake word]\n')
        self.display_manager.display_lock.acquire()
        time.sleep(0.2)
        self.show_stats = self.display_manager.get_show_stats()
        self.display_manager.set_show_stats(False)
        self.display_manager.show_image("pic/rasplogo.bmp", duration=0)

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
                
            elif inference.intent == "accendereSchermo":
                self.recorder.stop()
                #self.display_manager.set_show_stats(True)
                self.show_stats = True
                self.recorder.start()
                
            elif inference.intent == "spegnereSchermo":
                self.recorder.stop()
                self.show_stats = False
                self.display_manager.reset_display()
                self.recorder.start()
                
            elif inference.intent == "mostraOrario":
                self.recorder.stop()
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                
                tts_text = "Sono le ore " + current_time
                tts_thread = Thread(target=play_tts, args=(tts_text,))
                tts_thread.start()
                
                text_area = [label.Label(terminalio.FONT, text=current_time, scale=4, color=0xFFFFFF, x=4, y=64)]
                #self.show_stats = self.display_manager.get_show_stats()
                #self.display_manager.set_show_stats(False)
                self.display_manager.show_text(text_area)
                #self.display_manager.set_show_stats(self.show_stats)
                tts_thread.join()
                self.recorder.start()
                    
            elif inference.intent == "mostraMeteo":
                
                city = inference.slots.get("citta")
                url = f"http://api.weatherapi.com/v1/current.json?key=06754c26bc8542fe9b0122754230410&q={city}&aqi=no"            
                
                try:
                    r = requests.get(url)
                    if r.status_code == 200:
                        body = r.json()['current']
                        temp = str(body['temp_c'])
                        cond_code = body['condition']['code']
                        bmp_code = str(cond_code - 887)
                        path = "./pic/weather/" + bmp_code + ".bmp"
                        hum = str(body['humidity']) + "%"
                        
                        self.recorder.stop()
                                                
                        tts_text = METEO.get(cond_code) + " con una temperatura di " + temp + "gradi e umidità al " + hum
                        tts_thread = Thread(target=play_tts, args=(tts_text,))
                        tts_thread.start()
                        
                        #self.show_stats = self.display_manager.get_show_stats()
                        #self.display_manager.set_show_stats(False)
                        self.display_manager.show_image(path)
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="TEMP", scale=5, color=0xFFFFFF, x=4, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=temp + "°C", scale=4, color=0xFFFFFF, x=4, y=96))
                        self.display_manager.show_text(text_area)
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="HUM", scale=6, color=0xFFFFFF, x=8, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=hum, scale=6, color=0xFFFFFF, x=8, y=96))
                        self.display_manager.show_text(text_area)
                        #self.display_manager.set_show_stats(self.show_stats)
                        self.recorder.start()
                    else:
                        print(r.json())
                except requests.ConnectionError:
                    print("Failed to connect!")                
            else:
                raise NotImplementedError()
        else:
            self.recorder.stop()
            #self.display_manager.set_show_stats(self.show_stats)
            play_tts("Non ho capito")
            self.recorder.start()
        self.display_manager.reset_display()
        self.display_manager.display_lock.release()
        self.display_manager.set_show_stats(self.show_stats)

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
    
    display_manager = DisplayManager()
    
    stats_thread = StatsCollector(display_manager)
    stats_thread.daemon = True
    stats_thread.start()

    recorder = None
    access_key = "gLEeR53xMGRwaC2Bd1G7xEtpA21zkSZJW2GDp1783UbsCcBJ9ceMDQ=="
    app = PiVoice(os.path.join(os.path.dirname(__file__), 'porcupine.ppn'),
                  os.path.join(os.path.dirname(__file__), 'rhino.rhn'),
                  access_key,
                  args.microphone_index,
                  recorder, display_manager)

    app.run()