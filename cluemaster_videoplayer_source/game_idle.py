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


# Pulling up platform specifications
with open(os.path.join(MASTER_DIRECTORY, "assets/application data/platform_specs.json")) as platform_specs_file:
    PLATFORM = json.load(platform_specs_file)["platform"]

print(f"Game Idle Screen Loading")


class GameIdleMPVPlayer(QWidget):

    def __init__(self, files):
        super(GameIdleMPVPlayer, self).__init__()

        # default variables
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()
        self.playlist_files = files

        # configs
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)

        # loading mpv configurations
        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/platform_specs.json")) as master_specs:
            config = json.load(master_specs)["mpv_configurations"]

        # widget
        if PLATFORM == "Intel":
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())),
                                                        hwdec=config["hwdec"],
                                                        vo=config["vo"],
                                                        input_default_bindings=True,
                                                        input_vo_keyboard=True,
                                                        loop_playlist="inf",
                                                        image_display_duration="5"
                                                        )
        elif PLATFORM == "AMD":
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())),
                                                        hwdec=config["hwdec"],
                                                        vo=config["vo"],
                                                        input_default_bindings=True,
                                                        input_vo_keyboard=True,
                                                        loop_playlist="inf",
                                                        image_display_duration="5"
                                                        )
        else:
            print("game_idle - GPU TYPE: VM MPV Player")
            self.master_animated_image_player = mpv.MPV(wid=str(int(self.winId())),
                                                        vo=config["vo"],
                                                        input_default_bindings=True,
                                                        input_vo_keyboard=True,
                                                        loop_playlist="inf",
                                                        image_display_duration="5"
                                                        )

        # instance methods
        self.window_configurations()
        self.frontend()

    def window_configurations(self):
        """ this method contains code for the configurations of the window"""

        self.resize(self.screen_width, self.screen_height)
        self.setCursor(Qt.BlankCursor)

    def frontend(self):
        """ this method contains the codes for showing the video clue"""

        # adding file to mpv playlist
        try:
            print(f'>>> game_idle - PlayList Files: {self.playlist_files}')
            for file in self.playlist_files:
                # if file.endswith(".mp4") or file.endswith(".mkv") or file.endswith(".mpg") or file.endswith(".mpeg") or file.endswith(".m4v"):
                # print(">>> File appended to playlist - ", file)
                self.master_animated_image_player.playlist_append(file)

                # else:
                #     print(f'game_idle - no video files found to load into playlist')
                #     pass

            # print(self.master_animated_image_player.playlist_filenames)

            self.master_animated_image_player.playlist_pos = 0

            # self.master_animated_image_player.loop = True
            self.master_animated_image_player.playlist_play_index(0)
            # while True:
            #     self.master_animated_image_player.wait_for_playback()

        except Exception as error_playlist:
            print(f'game_idle - Error Loading PlayList Files: {error_playlist}')


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
        self.media_folder = None
        self.filtered_usb_files = None
        self.clue_media = None
        self.external_master_mpv_players = None
        self.media_assets_location = None

        self.setStyleSheet("background-color: #191F26;")

        # apis
        # with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
        #     initial_dictionary = json.load(unique_code_json_file)
        # print(f'game_idle - loading unique code file on HDD')
        #
        # unique_code_responses = initial_dictionary

        self.device_unique_code = threads.UNIQUE_CODE["Device Unique Code"]
        self.api_key = threads.UNIQUE_CODE["apiKey"]

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
            # with open(os.path.join(MASTER_DIRECTORY, "assets/application data/device_configurations.json"))
            # as configurations_json_file:
            #     initial_dictionary = json.load(configurations_json_file)
            #
            # room_info_response = initial_dictionary
            self.media_folder = os.path.join(MASTER_DIRECTORY, "assets/media/")

            # Let's try to access an usb drive and play videos inserted as well
            try:
                # Define the file extensions you want to filter
                file_extensions = ['.mp4', '.mpg', '.mpeg', '.m4v', '.mkv', '.avi', '.png', '.mp3', '.wav', '.gif'
                                   , '.jpg', '.jpeg']

                # Function to list files in a directory and its subdirectories
                def list_files(path):
                    files = []
                    for root, _, filenames in os.walk(path):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
                    return files

                # Function to filter files by extensions
                def filter_files_by_extension(files, extensions):
                    filtered_files = []
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in extensions):
                            filtered_files.append(file)
                    return filtered_files

                # Function to list files on USB drives
                def list_usb_files():
                    usb_drive_paths = ["./media/{}".format(user) for user in os.listdir("./media")]
                    usb_files = []
                    for usb_drive_path in usb_drive_paths:
                        if os.path.exists(usb_drive_path):
                            usb_files.extend(list_files(usb_drive_path))
                    return usb_files

                # List all USB drive files with the specified extensions
                usb_files = list_usb_files()
                self.filtered_usb_files = filter_files_by_extension(usb_files, file_extensions)

                # # Print or process the filtered files as needed
                # for usb_file in self.filtered_usb_files:
                #     print(f'FILES ON USB: {usb_file}')

            except Exception as usb_error:
                print(f'game_idle - Error Accessing USB: {usb_error}')
                self.filtered_usb_files = []

            # if there are files then play them.
            media_folder_dir = os.listdir(self.media_folder)

            # test if USB media files exist
            if self.filtered_usb_files:
                print(f'game_idle - USB FILES LIST HAS : {self.filtered_usb_files}')
            if not self.filtered_usb_files:
                print("game_idle - USB LIST IS EMPTY ", self.filtered_usb_files)

            if len(media_folder_dir) != 0 or self.filtered_usb_files:
            # if self.no_media_files is False:

                # if room_info_response["IsPhoto"] is True:
                    # checking if photo is enabled in the webapp
                # self.picture_location = os.path.join(MASTER_DIRECTORY, "assets/room data/picture/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/picture/"))[0]))
                # self.video_location = os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/"))[0]))
                # self.media_assets_location = os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/room data/intro media/"))[0]))
                # self.media_assets_location = os.path.join(MASTER_DIRECTORY, "assets/clue medias/{}".format(os.listdir(os.path.join(MASTER_DIRECTORY, "assets/clue medias/"))[0]))

                self.clue_media = os.path.join(MASTER_DIRECTORY, "assets/media/")
                self.media_assets_location = ([self.clue_media + file for file in os.listdir(self.clue_media)])

                if self.filtered_usb_files:
                    self.media_assets_location = self.media_assets_location + self.filtered_usb_files

                print(">>> Console output - Media Files ", self.media_assets_location)

                try:
                    self.mpv_player_triggered = True
                    self.external_master_mpv_players = GameIdleMPVPlayer(files=self.media_assets_location)
                    self.external_master_mpv_players.setParent(self)
                    self.external_master_mpv_players.showFullScreen()
                    self.external_master_mpv_players.show()

                except Exception as error:
                    print(f'game_idle - Error: {error}')

            else:
                print(f"game_idle - No videos found in folder. Nothing to play.")
                self.setStyleSheet("background-color:#191F26;")
                self.no_media()

        except json.decoder.JSONDecodeError:
            # if the code inside the try block faces json decode error, then pass
            pass

        except simplejson.errors.JSONDecodeError:
            # if the code inside the try block faces simplejson decode error then pass
            pass

    def no_media(self):

        self.main_layout = QVBoxLayout()

        font = QFont("IBM Plex Mono", 19)

        application_name = QLabel(self)
        application_name.setFont(font)
        application_name.setText("ClueMaster Video Player")
        application_name.setStyleSheet("color: white; font-size: 30px; font-weight: 700;")
        application_name.setGeometry(self.screen_width // 2, 100, 1000, 100)
        application_name.show()

        screensize_txt = QLabel(self)
        screensize_txt.setText(f"Screen Size: {self.screen_width} X {self.screen_height}")
        screensize_txt.setFont(font)
        screensize_txt.setStyleSheet("color: white; font-size: 40px; font-weight:bold;")
        screensize_txt.setGeometry(self.screen_width // 2, 200, 1000, 100)
        screensize_txt.show()

        message = QLabel(self)
        message.setFont(font)
        message.setStyleSheet("color: white; font-size: 20px; font-weight:bold;")
        message.setText("Idle Screen: No Media Files Found")
        message.setGeometry(self.screen_width // 2, 300, 1000, 100)
        message.show()


        gif = QMovie(os.path.join(ROOT_DIRECTORY, "assets/icons/security_loading.gif"))
        gif.start()

        loading_gif = QLabel(self)
        loading_gif.setMovie(gif)
        loading_gif.setGeometry(self.screen_width // 2, self.screen_height // 2, 1000, 200)
        loading_gif.show()

        self.main_layout.addSpacing(self.height() // 9)
        self.main_layout.addWidget(application_name, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(screensize_txt, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(message, alignment=Qt.AlignCenter)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(loading_gif, alignment=Qt.AlignCenter)

        self.setLayout(self.main_layout)

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
