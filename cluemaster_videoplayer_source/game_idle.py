import sys
import time

import mpv
import simplejson.errors
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
import os
from apis import *
from settings import *
import json
import threads
from requests.structures import CaseInsensitiveDict

# Setting up base directories
# ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
# MASTER_DIRECTORY = os.path.join(os.environ.get("HOME"), "CluemasterDisplay")

# Pulling up platform specifications
with open(os.path.join(MASTER_DIRECTORY, "assets/application data/platform_specs.json")) as platform_specs_file:
    PLATFORM = json.load(platform_specs_file)["platform"]

print(f"Game Idle Screen Loading")


class GameIdleMPVPlayer(QWidget):

    def __init__(self, file_name):
        super(GameIdleMPVPlayer, self).__init__()

        # default variables
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()

        # configs
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)

        # loading mpv configurations
        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/platform_specs.json")) as master_specs:
            config = json.load(master_specs)["mpv_configurations"]

        # widget
        if PLATFORM == "Intel":
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())), hwdec=config["hwdec"], vo=config["vo"])
        elif PLATFORM == "AMD":
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())), hwdec=config["hwdec"], vo=config["vo"])
        else:
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())), vo=config["vo"])

        # variables
        self.file_name = file_name

        # instance methods
        self.window_configurations()
        self.frontend()

    def window_configurations(self):
        """ this method contains code for the configurations of the window"""

        self.resize(self.screen_width, self.screen_height)
        self.setCursor(Qt.BlankCursor)

    def frontend(self):
        """ this method contains the codes for showing the video clue"""

        self.master_animated_image_player.loop = True
        self.master_animated_image_player.play(self.file_name)


class GameIdle(QMainWindow):
    def __init__(self):
        super(GameIdle, self).__init__()

        # default variables and instances
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()

        # threads
        self.shutdown_restart_request = threads.ShutdownRestartRequest()
        self.shutdown_restart_request.start()
        self.shutdown_restart_request.shutdown.connect(self.shutdown_device)
        self.shutdown_restart_request.restart.connect(self.restart_device)

        self.update_room_info_thread = threads.UpdateRoomInfo()
        self.update_room_info_thread.start()
        self.update_room_info_thread.update_detected.connect(self.restart_device)

        self.master_background = QLabel(self)

        # variables
        self.shutdownRequestReceived = False
        self.restartRequestReceived = False
        self.no_media_files = False
        self.mpv_player_triggered = False
        self.app_root = os.path.abspath(os.path.dirname(sys.argv[0]))

        self.setStyleSheet("background-color: #191F26;")

        # apis
        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_responses = initial_dictionary

        self.device_unique_code = unique_code_responses["Device Unique Code"]
        self.api_key = unique_code_responses["apiKey"]

        self.room_info_api = ROOM_INFO_API.format(device_unique_code=self.device_unique_code)

        self.headers = CaseInsensitiveDict()
        self.headers["Authorization"] = f"Basic {self.device_unique_code}:{self.api_key}"

        # instance methods
        self.window_configurations()
        self.frontend()

    def window_configurations(self):
        """ this method contains the codes for the configurations of the window """

        self.move(0, 0)
        self.setFixedSize(self.screen_width, self.screen_height)
        self.setCursor(Qt.BlankCursor)

    def frontend(self):
        """this method sets the available background image to the window as the central widget"""

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/device_configurations.json")) as configurations_json_file:
                initial_dictionary = json.load(configurations_json_file)

            room_info_response = initial_dictionary
            self.media_folder = os.path.join(MASTER_DIRECTORY, "assets/clue medias")

            # Let's try to access a usb drive and play videos inserted as well
            try:
                import re
                import subprocess
                device_re = re.compile(
                    b"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
                df = subprocess.check_output("lsusb")
                devices = []
                for i in df.split(b'\n'):
                    if i:
                        info = device_re.match(i)
                        if info:
                            dinfo = info.groupdict()
                            dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                            devices.append(dinfo)

                print(devices)
            except Exception as usberror:
                print(f'game_idle - Error Accessing USB: {usberror}')

            # if there are files then play them.

            if len(self.media_folder) != 0:
            # if self.no_media_files is False:

                # if room_info_response["IsPhoto"] is True:
                    # checking if photo is enabled in the webapp
                # self.picture_location = os.path.join(MASTER_DIRECTORY, "assets/room data/picture/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/picture/"))[0]))
                # self.video_location = os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/"))[0]))
                # self.media_assets_location = os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/"))[0]))
                self.media_assets_location = os.path.join(MASTER_DIRECTORY, "assets/clue medias/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/clue medias/"))[0]))
                # print(f'{self.media_assets_location}')

                if self.media_assets_location.endswith(".mp4") or self.media_assets_location.endswith(".mkv") or \
                        self.media_assets_location.endswith(".mpg") or self.media_assets_location.endswith(".mpeg") or \
                        self.media_assets_location.endswith(".m4v"):

                    print(f"game_idle = MP4 Background Video Found")
                    self.mpv_player_triggered = True
                    self.external_master_mpv_players = GameIdleMPVPlayer(file_name=self.media_assets_location)
                    self.external_master_mpv_players.setParent(self)
                    self.external_master_mpv_players.showFullScreen()
                    # self.external_master_mpv_players.loop = True

                elif self.media_assets_location.endswith(".apng") or self.media_assets_location.endswith(".ajpg") or \
                        self.media_assets_location.endswith(".gif"):

                    print(f"game_idle = Photo Background Found")
                    self.mpv_player_triggered = True
                    self.external_master_mpv_players = GameIdleMPVPlayer(file_name=self.media_assets_location)
                    self.external_master_mpv_players.setParent(self)
                    self.external_master_mpv_players.show()

                elif self.media_assets_location.endswith(".svg"):

                    print(f"game_idle = SVG Animated Background Found")
                    self.svg_widget = QSvgWidget(self.media_assets_location)
                    self.svg_widget.resize(self.screen_width, self.screen_height)
                    self.svg_widget.setParent(self)
                    self.svg_widget.show()

                else:
                    try:
                        self.master_background.setPixmap(QPixmap(self.media_assets_location).scaled(self.screen_width, self.screen_height))
                        self.setCentralWidget(self.master_background)
                    except Exception as error:
                        print(f'game_idle - Error: {error}')

            else:
                print(f"game_idle - No videos found in folder. Nothing to play.")
                self.setStyleSheet("background-color:#191F26;")

        except json.decoder.JSONDecodeError:
            # if the code inside the try block faces json decode error, then pass
            pass

        except simplejson.errors.JSONDecodeError:
            # if the code inside the try block faces simplejson decode error then pass
            pass


    def restart_device(self):
        """ this method is triggered as soon as the restart signal is emitted by the shutdown restart thread"""

        if self.restartRequestReceived is False:
            self.restartRequestReceived = True
            
            import dbus

            bus = dbus.SystemBus()
            bus_object = bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
            bus_object.Reboot(True, dbus_interface="org.freedesktop.login1.Manager")
            
            self.close()

        else:
            pass

    def shutdown_device(self):
        """ this method is triggered as soon as the shutdown signal is emitted by the shutdown restart thread"""

        if self.shutdownRequestReceived is False:
            self.shutdownRequestReceived = True

            import dbus

            bus = dbus.SystemBus()
            bus_object = bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
            bus_object.PowerOff(True, dbus_interface="org.freedesktop.login1.Manager")

            self.close()

        else:
            pass

    def stop_threads(self):
        """ this method when triggered stops every threads related to this window"""

        self.shutdown_restart_request.stop()
        self.update_room_info_thread.stop()
