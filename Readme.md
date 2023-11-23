# SOD - Pico

Python application capable of recognising simple spoken commands.

## Devices required
- Raspberry 4 Model B
- [Seeed ReSpeaker 2-Mics](https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT_Raspberry/)
- [Seeed Grove OLED Display 1.12 V2](https://wiki.seeedstudio.com/Grove-OLED-Display-1.12-SH1107_V3.0/)
- A speaker (optional)

## Prerequisites
### ReSpeaker 2 Mics Pi Hat Drivers
```bash
sudo apt-get update									
git clone https://github.com/seeed-studio-projects/seeed-voicecard.git
cd seeed-voicecard								     	   
sudo ./install.sh									
sudo reboot now
```
### Raspi-blinka
```bash
sudo mv /usr/lib/python3.11/EXTERNALLY-MANAGED /usr/lib/python3.11/EXTERNALLY-MANAGED.old
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
```

## Installation
```bash
git clone https://github.com/DevozZ99/SOD-Pico
cd SOD-Pico
pip3 install -r requirements.txt
```
Replace the default (English) Picovoice models parameters (in "/home/user/.local/lib/python3.11/site-packages/pvrhino/lib/common" and "/home/user/.local/lib/python3.11/site-packages/pvporcupine/lib/common") with the ones included in the PvModel directory.

Write down your [Picovoice AccessKey](https://console.picovoice.ai/) and [WeatherApi ApiKey](https://www.weatherapi.com/my/) respectively in the first and second line of the keys.txt file.

## Usage
Make sure the Raspberry is connected to the internet.

Run the application with the command:
```bash
python3 pico.py
```
It is also possible to select which audio input device to use with the option --microphone_index:
```bash
python3 pico.py --microphone_index 2
```
