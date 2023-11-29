import os
import sys
import time
import argparse
import configparser
import subprocess
import requests
from datetime import datetime
import threading
from threading import Thread, Lock

from apa102 import APA102

import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107

from picovoice import Picovoice
from pvrecorder import PvRecorder

import gtts
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play

#Definition of RGB colors for LEDs
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

#Definition of room names to LED indices
ROOMS = {
    'cucina' : 0,
    'soggiorno' : 1,
    'salotto' : 1,
    'camera' : 2,
    'camera da letto' : 2,
    'stanza' : 2,
    'stanza da letto' : 2,
}

#Weather conditions descriptions for TTS
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

#Number of LEDs and LED driver initialization
num_led = 3
led_driver = APA102(num_led=num_led)
    
class DisplayManager:
    '''
    Manages the Grove OLED display
    '''
    def __init__(self):
        #Display initialization
        displayio.release_displays()
        self.i2c = board.I2C()
        self.display_bus = displayio.I2CDisplay(self.i2c, device_address=0x3c)	#use command 'i2cdetect -y 1' to get the address
        self.width = 128
        self.height = 128
        try:
            self.display = adafruit_displayio_sh1107.SH1107(self.display_bus, width=self.width, height=self.height, display_offset=adafruit_displayio_sh1107.DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297, rotation=180)
        except:
            print("Display initialization failed!")
            sys.exit(-1)
        #Variables for synchronization
        self.show_stats = False        
        self.display_lock = Lock()
        
    def show_image(self, path, duration=3):
        '''
        Shows an image on the display.
        
        Args:
            path (str): Path to the .bmp file.
            duration (int): Time in seconds for which the image is displayed. If 0 display is not reset.
        '''
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
        '''
        Shows text on the display.
        
        Args:
            text (list): List of labels.
            duration (int): Time in seconds for which the text is displayed. If 0 display is not reset.
        '''
        group = displayio.Group()
        self.display.show(group)
        for label in text:
            group.append(label)
        self.display.show(group)
        if duration > 0:
            time.sleep(duration)
            self.reset_display()
            
    def reset_display(self):
        '''
        Resets the display to default state.
        '''
        group = displayio.Group()
        self.display.show(group)
    
    def get_show_stats(self):
        '''
        Returns the current value of show_stats.
        '''
        return self.show_stats
    
    def set_show_stats(self, value):
        '''
        Sets show_stats to value
        '''
        self.show_stats = value

class StatsCollector(Thread):
    '''
    Thread for collecting and displaying system statistics
    '''
    def __init__(self, display_manager):
        super().__init__()
        self.display_manager = display_manager
        
    def run(self):
        while True:
            if self.display_manager.get_show_stats():
                #Collect system statistics
                cmd = "top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'"
                CPU = subprocess.check_output(cmd, shell = True, text=True)

                cmd = "free -m | awk 'NR==2{printf \"%s/%sMB\", $3, $2}'"    
                MemUsage = subprocess.check_output(cmd, shell = True, text=True)
                
                cmd = "df -h | awk '$NF==\"/\"{printf \"%d/%dGB %s\", $3,$2,$5}'"
                Disk = subprocess.check_output(cmd, shell = True, text=True)
                
                cmd = "vcgencmd measure_temp | cut -d '=' -f 2 | head --bytes -1"
                Temperature = subprocess.check_output(cmd, shell = True, text=True)
                
                #Create labels
                text_area = []
                text_area.append(label.Label(terminalio.FONT, text="CPU:"+ CPU + "%", scale=2, color=0xFFFFFF, x=4, y=25))
                text_area.append(label.Label(terminalio.FONT, text=MemUsage, scale=2, color=0xFFFFFF, x=4, y=50))
                text_area.append(label.Label(terminalio.FONT, text=Disk, scale=2, color=0xFFFFFF, x=4, y=75))
                text_area.append(label.Label(terminalio.FONT, text=Temperature, scale=2, color=0xFFFFFF, x=4, y=100))
                #Display labels
                lock_acquired = self.display_manager.display_lock.acquire(blocking=False)
                if lock_acquired:
                    try:
                        self.display_manager.show_text(text_area, duration=0)
                        time.sleep(0.2)
                    finally:
                        self.display_manager.display_lock.release()
            #Sleep for 1 second before next iteration
            time.sleep(1)
            
            
def play_tts(text):
    '''
    Converts text to speech and plays it.
    
    Args:
        text (str): Message to be played.
    '''
    mp3_fo = BytesIO()
    #Specify the text and the language to use to create spoken message
    tts = gtts.gTTS(text, lang="it")
    try:
        #Make the API request and write response into a file-like object
        tts.write_to_fp(mp3_fo) 
        mp3_fo.seek(0)
        #Use pydub to play the audio
        audio = AudioSegment.from_file(mp3_fo, format="mp3")
        play(audio)
    except:
        print("The text-to-speech transformation has failed. Please check your internet connection and try again.")    


class PiVoice(Thread):
    '''
    Thread for handling Picovoice functionality.
    '''
    def __init__(self, keyword_path, context_path, access_key, weather_key, device_index, recorder, display_manager, porcupine_sensitivity=0.75, rhino_sensitivity=0.25):
        super(PiVoice, self).__init__()

        def inference_callback(inference):
            return self.inference_callback(inference)

        #Picovoice initialization
        self.picovoice = Picovoice(
            access_key=access_key, keyword_path=keyword_path,
            wake_word_callback=self.wakeword_callback,
            context_path=context_path, inference_callback=inference_callback,
            porcupine_sensitivity=porcupine_sensitivity, rhino_sensitivity=rhino_sensitivity
        )
        #Initialize context information
        self.context = self.picovoice.context_info
        #Initialize default LED color and brightness value
        self._default_color = 'bianco'
        self._default_brightness = 10
        #Initialize microphone device_index and pvrecorder
        self._device_index = device_index
        self.recorder = recorder
        #Initialize display manager and synchronization variable
        self.display_manager =  display_manager
        self.show_stats = False
        #Set weather api key
        self.weather_key = weather_key
        #Set brightness to the default value for all of the LEDs
        for i in range(0, num_led):
            led_driver.set_brightness(i, self._default_brightness)
            
    def set_led_brightness(self, room, brightness):
        '''
        Sets the brightness of LEDs.

        Args:
            room (str): Room name (optional, set to None for all LEDs).
            brightness (int): Brightness level.
        '''
        if room is not None:
            led_driver.set_brightness(ROOMS[room], brightness)
        else:
            for i in range(0, num_led):
                led_driver.set_brightness(i, brightness)
        led_driver.show()
        
    def set_led_color(self, room, color):
        '''
        Sets the color of LEDs.

        Args:
            room (str): Room name (optional, set to None for all LEDs).
            color (str): Color name.
        '''
        #If a color wasn't specified in the spoken command use the default one
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
        '''
        Callback function for when the wake word is detected.
        '''
        print('[wake word]\n')
        #Show a 'wake word recognised' image on the display
        self.display_manager.display_lock.acquire()
        time.sleep(0.2)
        self.show_stats = self.display_manager.get_show_stats()
        self.display_manager.set_show_stats(False)
        self.display_manager.show_image("pic/pico.bmp", duration=0)

    def inference_callback(self, inference):
        '''
        Callback function for Picovoice inference results.

        Args:
            inference (PicovoiceInference): Inference result.
        '''
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
                self.show_stats = True
                self.recorder.start()
                
            elif inference.intent == "spegnereSchermo":
                self.recorder.stop()
                self.show_stats = False
                self.display_manager.reset_display()
                self.recorder.start()
                
            elif inference.intent == "mostraOrario":
                self.recorder.stop()
                #Get current time
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                
                #Play TTS message
                tts_text = "Sono le ore " + current_time
                tts_thread = Thread(target=play_tts, args=(tts_text,))
                tts_thread.start()
                
                #Display current time on the display as text
                text_area = [label.Label(terminalio.FONT, text=current_time, scale=4, color=0xFFFFFF, x=4, y=64)]
                self.display_manager.show_text(text_area)
                tts_thread.join()
                self.recorder.start()
                    
            elif inference.intent == "mostraMeteo":
                
                city = inference.slots.get("citta")
                url = f"http://api.weatherapi.com/v1/current.json?key={self.weather_key}&q={city}&aqi=no"          
                
                try:
                    #Make a request to WeatherAPI
                    r = requests.get(url)
                    if r.status_code == 200:
                        body = r.json()['current']
                        #Get temperature in Celsius
                        temp = str(body['temp_c'])
                        #Get weather condition code
                        cond_code = body['condition']['code']
                        #Translate weather condition code into the corresponding bitmap image code
                        bmp_code = str(cond_code - 887)
                        path = "./pic/weather/" + bmp_code + ".bmp"
                        #Get humidity level
                        hum = str(body['humidity']) + "%"
                        
                        self.recorder.stop()
                        
                        #Play TTS message
                        tts_text = METEO.get(cond_code) + " con una temperatura di " + temp + "gradi e umidità al " + hum
                        tts_thread = Thread(target=play_tts, args=(tts_text,))
                        tts_thread.start()
                        
                        #Show weather condition image
                        self.display_manager.show_image(path)
                        #Show temperature on the display as text
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="TEMP", scale=5, color=0xFFFFFF, x=4, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=temp + "°C", scale=4, color=0xFFFFFF, x=4, y=96))
                        self.display_manager.show_text(text_area)
                        #Show humidity level on the display as text
                        text_area = []
                        text_area.append(label.Label(terminalio.FONT, text="HUM", scale=6, color=0xFFFFFF, x=8, y=32))
                        text_area.append(label.Label(terminalio.FONT, text=hum, scale=6, color=0xFFFFFF, x=8, y=96))
                        self.display_manager.show_text(text_area)                        
                    else:
                        print("HTTP Error " + r.status_code)
                except:
                    print("Connection failed. Please check your internet connection and try again.")
                finally:
                    self.recorder.start()
            else:
                raise NotImplementedError()
        else:
            #Play a TTS 'command not understood' message
            self.recorder.stop()
            play_tts("Non ho capito")
            self.recorder.start()
        #Reset display and 'show_stats' value
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
            print("PiVoice Exiting...")
        finally:
            if self.recorder is not None:
                self.recorder.delete()
                
            self.set_led_color(None, "off")
                
            self.display_manager.set_show_stats(False)
                
            time.sleep(1)
            self.display_manager.reset_display()
            time.sleep(0.3)

            self.picovoice.delete()

if __name__ == "__main__":
    #Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--microphone_index",
                        help="Index of input audio device",
                        type=int,
                        default=2)
    args = parser.parse_args()
    
    #Create a DisplayManager object
    display_manager = DisplayManager()
    
    #Create and start stats collecting thread
    stats_thread = StatsCollector(display_manager)
    stats_thread.daemon = True 
    stats_thread.start()

    recorder = None
    
    #Get API Keys from 'config.ini'
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        access_key = config['Keys']['picovoice']
        weather_key = config['Keys']['weatherapi']
    except:
        print("Configuration file (config.ini) not found or contains errors.")
        sys.exit(-1)

    #Create and run Picovoice application thread
    app = PiVoice(os.path.join(os.path.dirname(__file__), 'porcupine.ppn'),
                  os.path.join(os.path.dirname(__file__), 'rhino.rhn'),
                  access_key, weather_key,
                  args.microphone_index,
                  recorder, display_manager)    
    app.run()