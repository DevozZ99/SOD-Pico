import subprocess

oled_exe = "./C/main"

arguments = ["time"]

sudo_command = f"sudo -S {oled_exe} {' '.join(arguments)}"

try:
    result = subprocess.check_output(sudo_command, shell=True, text=True)
    print(result)
except subprocess.CalledProcessError as e:
    print(e)
