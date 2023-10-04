import os
import argparse
import subprocess

from threading import Thread

from apa102 import APA102

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

oled_exe = "./C/main"

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
                arguments = ["time"]
                sudo_command = f"sudo -S {oled_exe} {' '.join(arguments)}"
                try:
                    result = subprocess.Popen(sudo_command, shell=True, text=True)
                    print(result)
                except subprocess.CalledProcessError as e:
                    print(e)
                finally:
                    self.recorder.start()
                
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

    parser.add_argument("--access_key",
                        help="AccessKey obtained from Picovoice Console (https://picovoice.ai/console/)",
                        required=True)

    parser.add_argument("--microphone_index",
                        help="Index of input audio device",
                        type=int,
                        default=-1)

    args = parser.parse_args()

    recorder = None
    app = PiVoice(os.path.join(os.path.dirname(__file__), 'porcupine.ppn'),
                  os.path.join(os.path.dirname(__file__), 'rhino.rhn'),
                  args.access_key,
                  args.microphone_index,
                  recorder)

    app.run()

    
        
        
