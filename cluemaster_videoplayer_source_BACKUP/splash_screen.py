import os
import json
import socket
import uuid
import re
import random
import time
import subprocess
import requests

import threads
from apis import *
from settings import *

import main
from string import Template
from requests.structures import CaseInsensitiveDict
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QMovie, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QDesktopWidget

snap_version = os.environ.get("SNAP_VERSION")


def fetch_ipv4_device_address():
    ip_address = None
    i_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        i_socket.connect(('10.255.255.255', 1))
        ip_address = i_socket.getsockname()[0]
    except socket.error:
        ip_address = "127.0.0.1"
    finally:
        i_socket.close()
        print(">>> auto_startup - Device IP Address: " + ip_address)
        main.ipv4 = ip_address
        threads.IP_ADDRESS = ip_address
    return ip_address


class SplashBackend(QThread):
    skip_authentication = pyqtSignal(bool)

    def __init__(self):
        super(SplashBackend, self).__init__()

        # default variables
        self.var_skip_authentication = None
        self.is_killed = False
        self.unique_code_file = os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        time.sleep(2)

        if os.path.isdir(os.path.join(MASTER_DIRECTORY, "assets/application data")) is False:
            # if there is no directory named application data inside the assets directory then create one
            os.makedirs(os.path.join(MASTER_DIRECTORY, "assets/application data"))
        else:
            # if the directory already exists then pass
            pass

        if os.path.isdir(os.path.join(MASTER_DIRECTORY, "assets/media")) is False:
            # if there is no directory named application data inside the assets directory then create one
            os.makedirs(os.path.join(MASTER_DIRECTORY, "assets/media"))
        else:
            # if the directory already exists then pass
            pass

        if os.path.isfile(self.unique_code_file):
            # checking if unique code.json file exists in the application data directory, if yes then get the unique
            # device id and check if there are any device files for it

            with open(self.unique_code_file) as unique_code_json_file:
                json_object_of_unique_code_file = json.load(unique_code_json_file)

            # Load the Unique Device key into memory for the first time
            threads.UNIQUE_CODE = json_object_of_unique_code_file

            device_unique_code = json_object_of_unique_code_file["Device Unique Code"]
            api_key = json_object_of_unique_code_file["apiKey"]
            device_files_url = DEVICES_FILES_API.format(device_unique_code=device_unique_code)

            while self.is_killed is False:
                print(">>> Console output - Splash Screen Backend")
                try:
                    headers = CaseInsensitiveDict()
                    headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

                    if requests.get(device_files_url, headers=headers).status_code == 401:
                        # if response is 401 from the GetDeviceFiles api then, register the device
                        api_key = self.generate_secure_api_key(device_id=device_unique_code)
                        json_object_of_unique_code_file["apiKey"] = api_key
                        self.skip_authentication.emit(False)

                    else:
                        # else jump to loading screen
                        self.skip_authentication.emit(True)

                    json_object_of_unique_code_file["IPv4 Address"] = main.ipv4

                    with open(self.unique_code_file, "w") as unique_code_json_file:
                        json.dump(json_object_of_unique_code_file, unique_code_json_file)

                    threads.UNIQUE_CODE = json_object_of_unique_code_file

                except requests.exceptions.ConnectionError:
                    # if api call is facing connection error, jump to loading screen
                    # time.sleep(2)
                    self.skip_authentication.emit(True)
                    print(f'splash_screen - No Connection to Internet. Skipping to Load Screen.')

                else:
                    break

        else:
            # if there is no unique code.json file then generate a unique device id and secure api key and then save
            # them to unique code.json file and register device
            print(f'No Unique Registration Code File Exists')
            try:

                with open("/proc/cpuinfo") as master_cpu_info_file:
                    file_data = master_cpu_info_file.read()

                    if "hypervisor" in file_data:
                        dictionary = {"platform": "VirtualMachine", "mpv_configurations": {"vo": "x11"}}
                    elif "Intel" in file_data:
                        dictionary = {"platform": "Intel", "mpv_configurations": {"hwdec": "auto", "vo": "gpu", "gpu_context": "auto"}}
                    elif "AMD" in file_data:
                        dictionary = {"platform": "AMD", "mpv_configurations": {"hwdec": "auto", "vo": "gpu", "gpu_context": "auto"}}
                    else:
                        dictionary = {"platform": "Unspecified"}

                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/platform_specs.json"), "w") as specs_file:
                        json.dump(dictionary, specs_file)
            except Exception as master_cpu_info_file_error:
                print(f'{master_cpu_info_file_error}')

            numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
            alphabets = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
                         "T", "U", "V", "W", "X", "Y", "Z"]

            random_pair = [random.choice(alphabets), random.choice(numbers), random.choice(alphabets),
                           random.choice(numbers)]
            get_raw_mac = ':'.join(re.findall('..', '%012x' % uuid.getnode())).replace(":", "").upper()

            splitting_each_character = [character for character in get_raw_mac]

            first_pair = "".join(splitting_each_character[:4])
            second_pair = "".join(splitting_each_character[4:8])
            third_pair = "".join(splitting_each_character[8:12])
            fourth_pair = "".join(random_pair)

            full_unique_code = first_pair + "-" + second_pair + "-" + third_pair + "-" + fourth_pair
            api_key = self.generate_secure_api_key(device_id=full_unique_code)
            # main.ipv4 = fetch_device_ipv4_address()
            # ipv4_address = main.ipv4

            json_object = {"Device Unique Code": full_unique_code, "apiKey": api_key, "IPv4 Address": main.ipv4}
            try:
                with open(self.unique_code_file, "w") as file:
                    json.dump(json_object, file)

                threads.UNIQUE_CODE = json_object

            except Exception as error:
                print(f'splash_screen - Error = {error}')

            self.skip_authentication.emit(False)

    def generate_secure_api_key(self, device_id):
        """ this method takes the device_id and then generates a secure api key for it"""

        while True:
            try:
                authentication_api_url = GENERATE_API_TOKEN_API
                device_id = device_id

                headers = CaseInsensitiveDict()
                headers["Content-Type"] = "application/json"

                initial_template = Template("""{"DeviceKey": "${device_key}", "Username": "ClueMasterAPI", "Password": "8BGIJh27uBtqBTb2%t*zho!z0nS62tq2pGN%24&5PS3D"}""")
                data = initial_template.substitute(device_key=device_id)

                response = requests.post(url=authentication_api_url, headers=headers, data=data).json()
                print(response)
                print(">>> Console output - API Auth status - ", response["status"])
                return response["apiKey"]

            except requests.exceptions.ConnectionError:
                time.sleep(3)
                pass

    # def fetch_ipv4_device_address(self):
    #     """ this method fetches the device ipv4 address"""
    #
    #     initial_output = subprocess.getoutput("hostname -I")
    #     return initial_output

    def stop(self):
        """ this method stops the thread by setting the is_killed attribute to False and then calling the run() methods
            which when validated with a while loop turns False and thus breaks"""

        self.is_killed = True
        self.run()


class SplashWindow(QWidget):
    def __init__(self):
        super().__init__()

        # default variables
        self.splash_thread = None
        self.i_window = None
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()

        # widgets
        self.font = QFont("IBM Plex Mono", 19)

        # instance methods
        self.window_config()
        self.update_thread_info_file()
        self.frontend()

    def window_config(self):
        """ this method contains code for the configurations of the window"""

        self.font.setWordSpacing(2)
        self.font.setLetterSpacing(QFont.AbsoluteSpacing, 1)

        # qtRectangle = self.frameGeometry()
        # centerPoint = QDesktopWidget().availableGeometry().center()
        # qtRectangle.moveCenter(centerPoint)
        # self.move(qtRectangle.topLeft())

        # self.setFixedHeight(int(self.screen_height // 2.5))
        # self.setFixedWidth(int(self.screen_width // 2.75))
        self.setFixedSize(self.screen_width, self.screen_height)
        self.setWindowIcon(QIcon("assets/icons/app_icon.png"))
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.setStyleSheet("""
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
        """)
        self.setStyleSheet("background-color:#191F26; color:white;")

    def update_thread_info_file(self):
        if os.path.isdir(os.path.join(MASTER_DIRECTORY, "assets/application data")):
            print("Configuration Directories Exists")
            thread_info_dictionary = {"IsGameDetailsThreadRunning": False, "IsIdentifyDeviceThreadRunning": False,
                                      "IsGameClueThreadRunning": False, "IsTimerRequestThreadRunning": False,
                                      "IsDownloadConfigsThreadRunning": False, "IsUpdateRoomInfoThreadRunning": False,
                                      "IsShutdownRestartRequestThreadRunning": False, "ResettingGame": False}

            # with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
            #     json.dump(thread_info_dictionary, thread_file)
            threads.THREAD_INFO = thread_info_dictionary

        else:
            print("Creating Configuration Directories")
            os.makedirs(os.path.join(MASTER_DIRECTORY, "assets/application data"))
            thread_info_dictionary = {"IsGameDetailsThreadRunning": False, "IsIdentifyDeviceThreadRunning": False,
                                      "IsGameClueThreadRunning": False, "IsTimerRequestThreadRunning": False,
                                      "IsDownloadConfigsThreadRunning": False, "IsUpdateRoomInfoThreadRunning": False,
                                      "IsShutdownRestartRequestThreadRunning": False, "ResettingGame": False}

            # with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
            #     json.dump(thread_info_dictionary, thread_file)
            threads.THREAD_INFO = thread_info_dictionary

    def frontend(self):
        """ this methods holds the codes for the different labels and animations"""

        self.main_layout = QVBoxLayout()

        # with open(self.unique_code_file) as unique_code_file:
        #     unique_code_json_response = json.load(unique_code_file)

        application_name = QLabel(self)
        application_name.setFont(self.font)
        application_name.setText("ClueMaster Video Player")
        application_name.setStyleSheet("color: white; font-size: 30px; font-weight: 700;")

        version = QLabel(self)
        version.setText(f"Version : {snap_version}")
        version.setFont(self.font)
        version.setStyleSheet("color: white; font-size: 19px; font-weight:bold;")

        # unique_code_json_response = self.fetch_device_ipv4_address()
        # print(f'{unique_code_json_response}')
        local_ipv4_address = QLabel(self)
        local_ipv4_address.setFont(self.font)
        local_ipv4_address.setStyleSheet("color: white; font-size: 19px; font-weight:bold;")
        # local_ipv4_address.setText("Local IP : " + unique_code_json_response["IPv4 Address"].split(" ")[0])
        local_ipv4_address.setText("Local IP : " + fetch_ipv4_device_address())

        gif = QMovie(os.path.join(ROOT_DIRECTORY, "assets/icons/security_loading.gif"))
        gif.start()

        loading_gif = QLabel(self)
        loading_gif.setMovie(gif)
        loading_gif.show()

        self.main_layout.addSpacing(self.height() // 9)
        self.main_layout.addWidget(application_name, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(version, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(local_ipv4_address, alignment=Qt.AlignCenter)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(loading_gif, alignment=Qt.AlignCenter)

        self.setLayout(self.main_layout)
        self.connect_backend_thread()

    def connect_backend_thread(self):
        """ this method starts the splash screen backend thread """

        self.splash_thread = SplashBackend()
        self.splash_thread.start()
        self.splash_thread.skip_authentication.connect(self.switch_window)
        # var_skip = True
        # self.switch_window(var_skip)

    def switch_window(self, skip):
        """ this method is triggered as soon as the skip_authentication signal is emitted by the backend thread"""
        print(f'Thread for splash : skip = {skip}')
        self.splash_thread.stop()

        if skip is True:
            # if True is emitted by the skip_authentication signal then, jump to loading screen
            import loading_screen
            self.i_window = loading_screen.LoadingScreen()
            self.i_window.show()
            self.deleteLater()

        else:
            if skip is False:
                # if False is emitted by the skip_authentication signal then, have the device authenticated
                print(f'Loading Auth Screen')
                import authentication_screen
                self.i_window = authentication_screen.AuthenticationWindow()
                self.i_window.show()
                self.deleteLater()
