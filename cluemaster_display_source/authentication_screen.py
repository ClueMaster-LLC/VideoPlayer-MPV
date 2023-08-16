import time
import os
import shutil
import json
import requests
import simplejson.errors
from apis import *
from requests.structures import CaseInsensitiveDict
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QMovie, QKeySequence
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QShortcut, QProgressBar, QHBoxLayout

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MASTER_DIRECTORY = os.path.join(os.environ.get("HOME"), "CluemasterDisplay")


class AuthenticationBackend(QThread):
    authentication_complete = pyqtSignal()
    authentication_details = pyqtSignal(dict)
    downloading_media = pyqtSignal()
    media_file_downloaded = pyqtSignal()
    downloading_configurations = pyqtSignal()
    proceed = pyqtSignal(bool)
    complete_reset = pyqtSignal()

    def __init__(self):
        super(AuthenticationBackend, self).__init__()

        # default variables
        self.is_killed = False
        self.resetting_game = False

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does """

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as file:
                json_object = json.load(file)

            device_unique_code = json_object["Device Unique Code"]
            api_key = json_object["apiKey"]

            room_info_api_url = ROOM_INFO_API.format(device_unique_code=device_unique_code)
            device_request_url = DEVICE_REQUEST_API.format(device_unique_code=device_unique_code)

            headers = CaseInsensitiveDict()
            headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

            while self.is_killed is False:
                print(">>> Console output - Authentication Screen Backend")
                while True:
                    device_request_api = requests.get(device_request_url, headers=headers)
                    # print("here")
                    # device_request_api.raise_for_status()  # raise error if status code of request is not 200
                    # print("raise_for_status_passed")
                    if device_request_api.status_code != 200:
                        print("Device Registration - Device Request API status not 200")
                        time.sleep(3)
                        pass

                    else:
                        print("Got Request")
                        break

                while not requests.get(device_request_url, headers=headers).content.decode("utf-8") == "No record found":
                    # if there is a response then we assume that the device is being registered and proceed further and
                    # download the media files and the room configurations

                    device_request_api = requests.get(device_request_url, headers=headers)
                    device_request_api.raise_for_status()
                    deviceRequestId = device_request_api.json()["DeviceRequestid"]
                    requestId = device_request_api.json()["RequestID"]
                    deviceConfigurationId = 6

                    if requestId != deviceConfigurationId:
                        # if DeviceRequestid is not 6, then make a post response for that specific requests because
                        # it is a dummy request

                        identify_device_url = POST_DEVICE_API.format(device_unique_code=device_unique_code, deviceRequestId=deviceRequestId)
                        requests.post(identify_device_url, headers=headers).raise_for_status()
                        continue

                    else:
                        self.authentication_complete.emit()
                        time.sleep(3)

                        # if DeviceRequestid is 6 then download the new files
                        room_info_api = requests.get(room_info_api_url, headers=headers)
                        room_info_api.raise_for_status()

                        if room_info_api.content.decode("utf-8") != "No Configurations Files Found":

                            main_folder = "assets/room data"
                            main_room_data_directory = os.path.join(MASTER_DIRECTORY, main_folder)
                            room_data_music_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "music")
                            room_data_picture_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "picture")
                            room_data_video_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "video")
                            room_data_intro_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "intro media")
                            room_data_fail_end_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "fail end media")
                            room_data_success_end_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "success end media")
                            main_clue_media_file_directory = os.path.join(MASTER_DIRECTORY, "assets", "clue medias")

                            if os.path.isdir(main_room_data_directory):
                                shutil.rmtree(main_room_data_directory, ignore_errors=True)

                            if os.path.isdir(main_clue_media_file_directory):
                                shutil.rmtree(main_clue_media_file_directory, ignore_errors=True)

                            os.mkdir(main_room_data_directory)
                            os.mkdir(main_clue_media_file_directory)
                            os.mkdir(room_data_music_subfolder)
                            os.mkdir(room_data_picture_subfolder)
                            os.mkdir(room_data_video_subfolder)
                            os.mkdir(room_data_intro_media_subfolder)
                            os.mkdir(room_data_fail_end_media_subfolder)
                            os.mkdir(room_data_success_end_media_subfolder)

                            response_of_room_info_api = requests.get(room_info_api_url, headers=headers)
                            response_of_room_info_api.raise_for_status()
                            json_response_of_room_info_api = response_of_room_info_api.json()

                            # emit authentication details
                            self.authentication_details.emit(
                                {"media_files": len(response_of_room_info_api.json()["ClueMediaFiles"]) + 6})

                            music_file_url = json_response_of_room_info_api["MusicPath"]
                            picture_file_url = json_response_of_room_info_api["PhotoPath"]
                            video_file_url = json_response_of_room_info_api["VideoPath"]
                            intro_video_file_url = json_response_of_room_info_api["IntroVideoPath"]
                            end_success_file_url = json_response_of_room_info_api["SuccessVideoPath"]
                            end_fail_file_url = json_response_of_room_info_api["FailVideoPath"]

                            # emit downloading media slot
                            self.downloading_media.emit()

                            # music directory
                            try:
                                if music_file_url is not None:
                                    music_file = requests.get(music_file_url, headers=headers)
                                    music_file.raise_for_status()
                                    file_name = music_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_music_subfolder, file_name), "wb") as file:
                                        file.write(music_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # picture directory
                            try:
                                if picture_file_url is not None:
                                    picture_file = requests.get(picture_file_url, headers=headers)
                                    picture_file.raise_for_status()
                                    file_name = picture_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_picture_subfolder, file_name), "wb") as file:
                                        file.write(picture_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # video directory
                            try:
                                if video_file_url is not None:
                                    video_file = requests.get(video_file_url, headers=headers)
                                    video_file.raise_for_status()
                                    file_name = video_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_video_subfolder, file_name), "wb") as file:
                                        file.write(video_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # intro media directory
                            try:
                                if intro_video_file_url is not None:
                                    intro_video_file = requests.get(intro_video_file_url, headers=headers)
                                    intro_video_file.raise_for_status()
                                    file_name = intro_video_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_intro_media_subfolder, file_name), "wb") as file:
                                        file.write(intro_video_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # end media directory
                            try:
                                if end_success_file_url is not None:
                                    end_success_file = requests.get(end_success_file_url, headers=headers)
                                    end_success_file.raise_for_status()
                                    file_name = end_success_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_success_end_media_subfolder, file_name), "wb") as file:
                                        file.write(end_success_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # end media directory
                            try:
                                if end_fail_file_url is not None:
                                    end_fail_file = requests.get(end_fail_file_url, headers=headers)
                                    end_fail_file.raise_for_status()
                                    file_name = end_fail_file_url.split("/")[5].partition("?X")[0]
                                    with open(os.path.join(room_data_fail_end_media_subfolder, file_name), "wb") as file:
                                        file.write(end_fail_file.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                            except IndexError:
                                pass

                            except requests.exceptions.HTTPError as request_error:
                                if "401 Client Error" in str(request_error):
                                    self.check_api_token_status()
                                else:
                                    print(">> Console output - Not a 401 error")

                            # clue medias
                            index = 0

                            while index <= len(response_of_room_info_api.json()["ClueMediaFiles"]) - 1:
                                url = response_of_room_info_api.json()["ClueMediaFiles"][index]["FilePath"]

                                if url is not None:
                                    clue_media_content = requests.get(url, headers=headers)
                                    clue_media_content.raise_for_status()
                                    try:
                                        file_name = url.split("/")[5].partition("?X")[0]
                                    except IndexError:
                                        index += int(1)
                                        continue
                                    else:
                                        with open(os.path.join(main_clue_media_file_directory, file_name), "wb") as file:
                                            file.write(clue_media_content.content)

                                        # emit file downloaded signal
                                        self.media_file_downloaded.emit()

                                        index += int(1)
                                        continue
                                else:
                                    index += int(1)

                            identify_device_url = POST_DEVICE_API.format(device_unique_code=device_unique_code, deviceRequestId=deviceRequestId)
                            requests.post(identify_device_url, headers=headers).raise_for_status()
                            continue

                        else:
                            identify_device_url = POST_DEVICE_API.format(device_unique_code=device_unique_code, deviceRequestId=deviceRequestId)
                            requests.post(identify_device_url, headers=headers).raise_for_status()
                            continue
                else:
                    # emit downloading configurations signal
                    self.downloading_configurations.emit()
                    time.sleep(3)

                    room_info_api = requests.get(room_info_api_url, headers=headers)
                    room_info_api.raise_for_status()
                    if room_info_api.content.decode("utf-8") != "No Configurations Files Found":
                        # downloading the new room configurations into device configurations.json file

                        json_data_of_configuration_files = room_info_api.json()

                        data = {"Room Minimum Players": json_data_of_configuration_files["RoomMinPlayers"],
                                "Room Maximum Players": json_data_of_configuration_files["RoomMaxPlayers"],
                                "Clues Allowed": json_data_of_configuration_files["CluesAllowed"],
                                "Clue Size On Screen": json_data_of_configuration_files["ClueSizeOnScreen"],
                                "Maximum Number Of Clues": json_data_of_configuration_files["MaxNoOfClues"],
                                "Clue Position Vertical": json_data_of_configuration_files["CluePositionVertical"],
                                "IsTimeLimit": json_data_of_configuration_files["IsTimeLimit"],
                                "Time Limit": json_data_of_configuration_files["TimeLimit"],
                                "Time Override": json_data_of_configuration_files["TimeOverride"]}

                        with open(os.path.join(MASTER_DIRECTORY, "assets/application data", "device configurations.json"), "w") as file:
                            json.dump(data, file)

                    self.proceed.emit(True)
                    self.stop()

        except simplejson.errors.JSONDecodeError:
            # when the app faces simplejson decode error during opening json files, then pass
            pass

        except requests.exceptions.ConnectionError:
            # if the app faces connection error when making api calls, then pass
            pass

        except json.decoder.JSONDecodeError:
            # if the app faces json decode error when opening json files then pass
            pass

        except requests.exceptions.HTTPError as request_error:
            if "401 Client Error" in str(request_error):
                self.check_api_token_status()
            else:
                print(">> Console output - Not a 401 error Master Except Block")
                print(request_error)

    def check_api_token_status(self):
        if self.resetting_game is False:
            print("401 Client Error - Device Removed or Not Registered")
            self.resetting_game = True
            self.complete_reset.emit()
            self.stop()
        else:
            pass

    def stop(self):
        """ this method stops the thread by setting the is_killed attribute to False and then calling the run() methods
            which when validated with a while loop turns False and thus breaks """

        self.is_killed = True
        self.run()


class AuthenticationWindow(QWidget):

    def __init__(self):
        super().__init__()

        # default variables
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()
        self.auth_details = None

        self.setStyleSheet("""
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
        """)

        # instance methods
        self.load_unique_id()
        self.window_config()
        self.frontend()

    def load_unique_id(self):
        """ this method opens up the unique code.json file and then loads the device unique code for displaying in the
            authentication screen"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as file:
            json_object = json.load(file)

        device_unique_code = json_object["Device Unique Code"]
        self.get_mac = device_unique_code

    def window_config(self):
        """ this method contains the codes for the configurations of the window """

        self.move(0, 0)
        self.setMinimumSize(self.screen_width, self.screen_height)

        fullScreen_shortCut = QShortcut(QKeySequence("F11"), self)
        fullScreen_shortCut.activated.connect(self.go_fullScreen)

        self.setStyleSheet("background-color: #191F26;")
        self.setCursor(Qt.BlankCursor)
        self.showFullScreen()

    def go_fullScreen(self):
        """ this method checks if the F11 key is pressed, if yes then check if the window is in full screen mode, if
            yes then put it back to normal else show full screen"""

        if self.isFullScreen() is True:
            # window is in full game screen mode
            self.showNormal()
            self.setCursor(Qt.ArrowCursor)

        else:
            # window is in normal screen mode
            self.setCursor(Qt.BlankCursor)
            self.showFullScreen()

    def frontend(self):
        """ this method contains all the codes for the labels and the animations in the authentications window"""

        self.main_layout = QVBoxLayout()
        self.footer_layout = QHBoxLayout()

        alpha_label = QLabel(self)
        alpha_label.setText("ClueMaster TV Display Timer")
        alpha_label.setAlignment(Qt.AlignHCenter)
        alpha_label.setFont(QFont("IBM Plex Mono", 30))
        alpha_label.font().setWeight(500)
        alpha_label.setStyleSheet("color: #ffffff;")

        device_key_label = QLabel(self)
        device_key_label.setFont(QFont("IBM Plex Mono", 45))
        device_key_label.setAlignment(Qt.AlignHCenter)
        device_key_label.setText("DEVICE KEY")
        device_key_label.setStyleSheet("color: #ffffff;")

        device_code = QLabel(self)
        device_code.setText(self.get_mac)
        device_code.setAlignment(Qt.AlignHCenter)
        device_code.setFont(QFont("IBM Plex Mono", 60))
        device_code.setStyleSheet("color: #4e71cf;")

        loading_gif = QMovie(os.path.join(ROOT_DIRECTORY, "assets/icons/security_loading.gif"))
        loading_gif.start()

        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignHCenter)
        self.loading_label.setText("waiting for authentication ...")
        self.loading_label.setFont(QFont("IBM Plex Mono", 20))
        self.loading_label.setStyleSheet("color: white; margin-bottom : 50px;")
        self.loading_label.show()

        self.download_media_files_progressbar = QProgressBar(self)
        self.download_media_files_progressbar.setAlignment(Qt.AlignHCenter)
        self.download_media_files_progressbar.setTextVisible(False)
        self.download_media_files_progressbar.setFixedWidth(int(30/100 * self.screen_width))
        self.download_media_files_progressbar.setFixedHeight(int(4/100 * self.screen_height))

        stylesheet = """QProgressBar{background-color: transparent; border: 3px solid #4e71cf; border-radius: 5px;}
        QProgressBar::chunk{background-color: #4e71cf;}"""

        self.download_media_files_progressbar.setStyleSheet(stylesheet)
        self.download_media_files_progressbar.hide()

        self.footer_layout.addStretch(1)
        self.footer_layout.addWidget(self.download_media_files_progressbar, alignment=Qt.AlignHCenter)
        self.footer_layout.addStretch(1)

        self.main_layout.addStretch()
        self.main_layout.addWidget(alpha_label)
        self.main_layout.addSpacing(40)
        self.main_layout.addWidget(device_key_label)
        self.main_layout.addSpacing(90)
        self.main_layout.addWidget(device_code)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.loading_label)
        self.main_layout.addLayout(self.footer_layout)
        self.setLayout(self.main_layout)

        self.connect_backend_thread()

    def connect_backend_thread(self):
        """ this method starts the backend authentication thread"""

        self.authentication_thread = AuthenticationBackend()
        self.authentication_thread.start()
        self.authentication_thread.authentication_complete.connect(self.authentication_complete)
        self.authentication_thread.authentication_details.connect(self.authentication_details)
        self.authentication_thread.downloading_media.connect(self.downloading_media)
        self.authentication_thread.media_file_downloaded.connect(self.update_media_files_downloader_progressbar)
        self.authentication_thread.downloading_configurations.connect(self.downloading_configurations)
        self.authentication_thread.proceed.connect(self.switch_window)
        self.authentication_thread.complete_reset.connect(self.reset_game)

    def authentication_complete(self):
        """updating the self.loading_label and setting its text as authentication complete"""

        self.loading_label.setText("authentication complete ...")

    def authentication_details(self, details):
        """updating the self.auth_details variable with latest authentication details from backend
        details = {"media_files": "media+clue"}
        """

        self.auth_details = details

    def downloading_media(self):
        """hiding the self.loading_label and replacing it with the self.download_media_files_progressbar"""

        self.loading_label.hide()

        self.download_media_files_progressbar.setMaximum(self.auth_details["media_files"])
        self.main_layout.insertSpacing(-1, 30)
        self.download_media_files_progressbar.show()

    def update_media_files_downloader_progressbar(self):
        """check the latest files_downloaded field from self.auth_details and updates the progressbar"""

        files_downloaded = self.download_media_files_progressbar.value()
        files_downloaded += 1

        self.download_media_files_progressbar.setValue(files_downloaded)

    def downloading_configurations(self):
        """hide the progressbar and show the self.loading_label and update its text to downloading configurations ..."""
        self.download_media_files_progressbar.hide()

        self.loading_label.setText("downloading configurations ...")
        self.loading_label.show()

    def reset_game(self):
        import splash_screen
        self.splash_screen_window = splash_screen.SplashWindow()
        self.splash_screen_window.show()
        self.deleteLater()

    def switch_window(self, proceed):
        """ this method is triggered as soon as the proceed signal is emitted by the backend thread"""

        if proceed is True:
            # if True is emitted by the proceed signal then move to the next window or screen

            import loading_screen
            self.window = loading_screen.LoadingScreen()
            self.window.show()
            self.deleteLater()

        else:
            pass
