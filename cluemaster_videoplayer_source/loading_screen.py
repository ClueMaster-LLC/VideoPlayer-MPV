import os
import random
import time
import requests
import json
import simplejson
import shutil
import platform_facts
from apis import *
from requests.structures import CaseInsensitiveDict
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QShortcut, QHBoxLayout, QProgressBar
from PyQt5.QtGui import QFont, QMovie, QKeySequence
from PyQt5.QtCore import Qt, QThread, pyqtSignal

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MASTER_DIRECTORY = os.path.join(os.environ.get("HOME"), "CluemasterDisplay")


class LoadingBackend(QThread):
    authentication_details = pyqtSignal(dict)
    downloading_media = pyqtSignal()
    media_file_downloaded = pyqtSignal()
    downloading_configurations = pyqtSignal()
    proceed = pyqtSignal(bool)
    complete_reset = pyqtSignal()

    def __init__(self):
        super(LoadingBackend, self).__init__()

        # default variables
        self.is_killed = False
        self.registering_device = False

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        time.sleep(15)

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
                json_object = json.load(unique_code_json_file)

            device_unique_code = json_object["Device Unique Code"]
            api_key = json_object["apiKey"]

            room_info_api_url = ROOM_INFO_API.format(device_unique_code=device_unique_code)
            download_files_request_api = DOWNLOAD_FILES_REQUEST.format(unique_code=device_unique_code)

            headers = CaseInsensitiveDict()
            headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

            while self.is_killed is False:
                print(">>> Console output - Loading Screen Backend")

                room_info_api = requests.get(room_info_api_url, headers=headers)
                room_info_api.raise_for_status()

                if room_info_api.content.decode("utf-8") != "No Configurations Files Found":
                    # checking responses of room info api, if response is not No Configurations Files Found, then
                    # move forward and validate every media files and check for updated or new files

                    main_folder = "assets/room data"
                    main_room_data_directory = os.path.join(MASTER_DIRECTORY, main_folder)
                    room_data_music_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "music")
                    room_data_picture_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "picture")
                    room_data_video_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "video")
                    room_data_intro_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "intro media")
                    room_data_fail_end_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "fail end media")
                    room_data_success_end_media_subfolder = os.path.join(MASTER_DIRECTORY, main_folder, "success end media")
                    main_clue_media_file_directory = os.path.join(MASTER_DIRECTORY, "assets", "clue medias")

                    response_of_room_info_api = requests.get(room_info_api_url, headers=headers)
                    response_of_room_info_api.raise_for_status()

                    # emit authentication details
                    self.authentication_details.emit(
                        {"media_files": len(response_of_room_info_api.json()["ClueMediaFiles"]) + 6})
                    time.sleep(2)

                    music_file_url = response_of_room_info_api.json()["MusicPath"]
                    picture_file_url = response_of_room_info_api.json()["PhotoPath"]
                    video_file_url = response_of_room_info_api.json()["VideoPath"]
                    intro_video_file_url = response_of_room_info_api.json()["IntroVideoPath"]
                    end_success_file_url = response_of_room_info_api.json()["SuccessVideoPath"]
                    end_fail_file_url = response_of_room_info_api.json()["FailVideoPath"]

                    # emit downloading media slot
                    self.downloading_media.emit()
                    time.sleep(2)

                    if os.path.isdir(main_room_data_directory) is False:
                        os.mkdir(main_room_data_directory)

                    if os.path.isdir(main_clue_media_file_directory) is False:
                        shutil.rmtree(main_clue_media_file_directory, ignore_errors=True)
                        os.mkdir(main_clue_media_file_directory)

                    if os.path.isdir(room_data_music_subfolder) is False:
                        os.mkdir(room_data_music_subfolder)

                    if os.path.isdir(room_data_picture_subfolder) is False:
                        os.mkdir(room_data_picture_subfolder)

                    if os.path.isdir(room_data_video_subfolder) is False:
                        os.mkdir(room_data_video_subfolder)

                    if os.path.isdir(room_data_intro_media_subfolder) is False:
                        os.mkdir(room_data_intro_media_subfolder)

                    if os.path.isdir(room_data_success_end_media_subfolder) is False:
                        os.mkdir(room_data_success_end_media_subfolder)

                    if os.path.isdir(room_data_fail_end_media_subfolder) is False:
                        os.mkdir(room_data_fail_end_media_subfolder)

                    # music directory
                    try:
                        if music_file_url is not None:
                            file_name = music_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_music_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_music_subfolder, ignore_errors=True)
                                os.mkdir(room_data_music_subfolder)

                                file_bytes = requests.get(music_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_music_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
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
                            file_name = picture_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_picture_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_picture_subfolder, ignore_errors=True)
                                os.mkdir(room_data_picture_subfolder)

                                file_bytes = requests.get(picture_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_picture_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
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
                            file_name = video_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_video_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_video_subfolder, ignore_errors=True)
                                os.mkdir(room_data_video_subfolder)

                                file_bytes = requests.get(video_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_video_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
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
                            file_name = intro_video_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_intro_media_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_intro_media_subfolder, ignore_errors=True)
                                os.mkdir(room_data_intro_media_subfolder)

                                file_bytes = requests.get(intro_video_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_intro_media_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
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
                            file_name = end_success_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_success_end_media_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_success_end_media_subfolder, ignore_errors=True)
                                os.mkdir(room_data_success_end_media_subfolder)

                                file_bytes = requests.get(end_success_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_success_end_media_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
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
                            file_name = end_fail_file_url.split("/")[5].partition("?X")[0]
                            file_location = os.path.join(room_data_fail_end_media_subfolder, file_name)

                            if os.path.isfile(file_location) is False:
                                shutil.rmtree(room_data_fail_end_media_subfolder, ignore_errors=True)
                                os.mkdir(room_data_fail_end_media_subfolder)

                                file_bytes = requests.get(end_fail_file_url, headers=headers)
                                file_bytes.raise_for_status()
                                with open(os.path.join(room_data_fail_end_media_subfolder, file_name), "wb") as file:
                                    file.write(file_bytes.content)

                                # emit file downloaded signal
                                self.media_file_downloaded.emit()
                            else:
                                # emit file downloaded signal
                                self.media_file_downloaded.emit()

                    except IndexError:
                        pass

                    except requests.exceptions.HTTPError as request_error:
                        if "401 Client Error" in str(request_error):
                            self.check_api_token_status()
                        else:
                            print(">> Console output - Not a 401 error")

                    # downloading clue medias
                    index = 0

                    while index <= len(response_of_room_info_api.json()["ClueMediaFiles"]) - 1:
                        url = response_of_room_info_api.json()["ClueMediaFiles"][index]["FilePath"]

                        if url is not None:
                            try:
                                file_name = url.split("/")[5].partition("?X")[0]
                            except IndexError:
                                index += int(1)
                                continue
                            else:
                                file_location = os.path.join(main_clue_media_file_directory, file_name)

                                if os.path.isfile(file_location) is False:
                                    clue_media_content = requests.get(url, headers=headers)
                                    clue_media_content.raise_for_status()
                                    with open(os.path.join(main_clue_media_file_directory, file_name), "wb") as file:
                                        file.write(clue_media_content.content)

                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()
                                else:
                                    # emit file downloaded signal
                                    self.media_file_downloaded.emit()

                                index += int(1)
                                continue
                        else:
                            index += int(1)

                    try:
                        # making post response for DeviceRequestid 6
                        response_of_download_files_request = requests.get(download_files_request_api, headers=headers)
                        response_of_download_files_request.raise_for_status()
                        device_request_id = response_of_download_files_request.json()["DeviceRequestid"]
                        device_key = response_of_download_files_request.json()["DeviceKey"]
                        requests.post(POST_DEVICE_API.format(device_unique_code=device_key, deviceRequestId=device_request_id), headers=headers).raise_for_status()

                    except simplejson.errors.JSONDecodeError:
                        # if the code inside the try block faces simplejson decode error while opening json files, pass
                        pass

                    except requests.exceptions.ConnectionError:
                        # if the code inside the try block faces connection error while making api calls, pass
                        pass

                    except json.decoder.JSONDecodeError:
                        # if the code inside the try block faces json decode error while opening json files, pass
                        pass

                    except KeyError:
                        # if the code inside the try block faces KeyError, then pass
                        pass

                    except requests.exceptions.HTTPError as request_error:
                        if "401 Client Error" in str(request_error):
                            self.check_api_token_status()
                        else:
                            print(">> Console output - Not a 401 error")

                    # emit downloading configurations signal
                    self.downloading_configurations.emit()
                    time.sleep(3)

                    data = {"Room Minimum Players": response_of_room_info_api.json()["RoomMinPlayers"],
                            "Room Maximum Players": response_of_room_info_api.json()["RoomMaxPlayers"],
                            "Clues Allowed": response_of_room_info_api.json()["CluesAllowed"],
                            "Clue Size On Screen": response_of_room_info_api.json()["ClueSizeOnScreen"],
                            "Maximum Number Of Clues": response_of_room_info_api.json()["MaxNoOfClues"],
                            "Clue Position Vertical": response_of_room_info_api.json()["CluePositionVertical"],
                            "IsTimeLimit": response_of_room_info_api.json()["IsTimeLimit"],
                            "Time Limit": response_of_room_info_api.json()["TimeLimit"],
                            "Time Override": response_of_room_info_api.json()["TimeOverride"],
                            "IsPhoto": response_of_room_info_api.json()["IsPhoto"],
                            "IsFailVideo": response_of_room_info_api.json()["IsFailVideo"],
                            "IsSuccessVideo": response_of_room_info_api.json()["IsSuccessVideo"]}

                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data", "device configurations.json"), "w") as file:
                        json.dump(data, file)

                    self.proceed.emit(True)
                    self.stop()

                else:
                    pass

        except simplejson.errors.JSONDecodeError:
            # if the code inside the try block faces simplejson decode error while opening json files, pass
            pass

        except requests.exceptions.ConnectionError:
            # if the code inside the try block faces connection error while making api calls, pass
            pass

        except json.decoder.JSONDecodeError:
            # if the code inside the try block faces json decode error while opening json files, pass
            pass

        except requests.exceptions.HTTPError as request_error:
            if "401 Client Error" in str(request_error):
                self.check_api_token_status()
            else:
                print(">> Console output - Not a 401 error")

    def check_api_token_status(self):
        if self.registering_device is False:
            print("401 Client Error - Device Removed or Not Registered")
            self.registering_device = True
            self.complete_reset.emit()
            self.stop()
        else:
            pass

    def stop(self):
        """ this method stops the thread by setting the is_killed attribute to False and then calling the run() methods
            which when validated with a while loop turns False and thus breaks """

        self.is_killed = True
        self.run()


class LoadingScreen(QWidget):

    def __init__(self):
        super().__init__()

        # default variables
        self.screen_width = QApplication.desktop().width()
        self.screen_height = QApplication.desktop().height()

        # instance methods
        self.window_config()
        self.frontend()

    def window_config(self):
        """ this method contains the codes for the configurations of the window """

        self.move(0, 0)
        self.setMinimumSize(self.screen_width, self.screen_height)

        fullScreen_ShortCut = QShortcut(QKeySequence("F11"), self)
        fullScreen_ShortCut.activated.connect(self.go_fullScreen)

        self.setStyleSheet("""
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');""")
        self.setStyleSheet("background-color: #191F26;")

        self.setCursor(Qt.BlankCursor)
        self.showFullScreen()

    def go_fullScreen(self):
        """ this method checks if the F11 key is pressed, if yes then check if the window is in full screen mode, if
            yes then put it back to normal else show full screen"""

        if self.isFullScreen() is True:
            # window is in full game screen mode
            self.showMaximized()
            self.setCursor(Qt.ArrowCursor)

        else:
            # window is in normal screen mode
            self.setCursor(Qt.BlankCursor)
            self.showFullScreen()

    def frontend(self):
        """ this method contains all the codes for the labels and the animations in the authentications window"""

        self.main_layout = QVBoxLayout()
        self.footer_layout = QHBoxLayout()

        gif = QMovie(os.path.join(ROOT_DIRECTORY, "assets/icons/loading_beaker.gif"))
        gif.start()

        loading_gif = QLabel(self)
        loading_gif.setAlignment(Qt.AlignHCenter)
        loading_gif.setMovie(gif)

        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignHCenter)
        self.loading_label.setText("confirming media files download ...")
        self.loading_label.setFont(QFont("IBM Plex Mono", 20))
        self.loading_label.setStyleSheet("color: white; margin-bottom : 50px;")
        self.loading_label.show()

        self.download_media_files_progressbar = QProgressBar(self)
        self.download_media_files_progressbar.setAlignment(Qt.AlignHCenter)
        self.download_media_files_progressbar.setTextVisible(False)
        self.download_media_files_progressbar.setFixedWidth(int(30 / 100 * self.screen_width))
        self.download_media_files_progressbar.setFixedHeight(int(4 / 100 * self.screen_height))

        stylesheet = """QProgressBar{background-color: transparent; border: 3px solid #4e71cf; border-radius: 5px;}
                QProgressBar::chunk{background-color: #4e71cf;}"""

        self.download_media_files_progressbar.setStyleSheet(stylesheet)
        self.download_media_files_progressbar.hide()

        self.footer_layout.addStretch(1)
        self.footer_layout.addWidget(self.download_media_files_progressbar, alignment=Qt.AlignHCenter)
        self.footer_layout.addStretch(1)

        self.main_layout.addStretch()
        self.main_layout.addWidget(loading_gif)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.loading_label)
        self.main_layout.addLayout(self.footer_layout)

        self.setLayout(self.main_layout)
        self.connect_backend_thread()

    def connect_backend_thread(self):
        """ this method starts the backend authentication thread"""

        self.loading_thread = LoadingBackend()
        self.loading_thread.start()
        self.loading_thread.authentication_details.connect(self.authentication_details)
        self.loading_thread.downloading_media.connect(self.downloading_media)
        self.loading_thread.media_file_downloaded.connect(self.update_media_files_downloader_progressbar)
        self.loading_thread.downloading_configurations.connect(self.downloading_configurations)
        self.loading_thread.proceed.connect(self.switch_window)
        self.loading_thread.complete_reset.connect(self.reset_game)

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

        self.loading_label.setText("confirming configurations download ...")
        self.loading_label.show()

    def reset_game(self):
        import splash_screen
        self.splash_screen_window = splash_screen.SplashWindow()
        self.splash_screen_window.show()

        self.loading_thread.disconnect()
        self.loading_thread.quit()
        self.close()
        self.deleteLater()

    def switch_window(self, response):
        """ this method is triggered as soon as the proceed signal is emitted by the backend thread"""

        if response is True:
            # if True is emitted by the proceed signal then move to the next window or screen

            import normal_screen
            self.window = normal_screen.NormalWindow()
            self.window.show()
            self.loading_thread.disconnect()
            self.loading_thread.quit()
            self.close()
            self.deleteLater()

        else:
            pass

