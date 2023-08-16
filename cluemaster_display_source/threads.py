import json
import time
import requests
import simplejson
from apis import *
from requests.structures import CaseInsensitiveDict
from PyQt5.QtCore import QThread, pyqtSignal
import os

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MASTER_DIRECTORY = os.path.join(os.environ.get("HOME"), "CluemasterDisplay")


class GameDetails(QThread):

    # signals
    statusUpdated = pyqtSignal(int)
    updateCluesUsed = pyqtSignal(int)
    apiStatus = pyqtSignal(int)
    deviceIDcorrupted = pyqtSignal()
    update_detected = pyqtSignal()
    custom_game_status = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""
        self.app_is_idle = True

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        device_unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

        game_details_url = GAME_DETAILS_API.format(device_unique_code)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsGameDetailsThreadRunning"] is True:
                    pass
                else:
                    return

                print(">>> Console output - Game Details")
                response = requests.get(game_details_url, headers=headers)
                response.raise_for_status()
                print(">>> Console output - Is App Idle - ", self.app_is_idle)

                if self.app_is_idle is True and response.status_code == 401:
                    print(">>> Console output - Device Corrupted...")
                    self.deviceIDcorrupted.emit()

                elif response.status_code != 200:
                    print(">>> Console output - API Response not 200")
                    pass
                else:
                    response = response.json()
                    game_status = response["gameStatus"]
                    clue_used = response["noOfCluesUsed"]

                    if clue_used is None:
                        pass
                    else:
                        self.updateCluesUsed.emit(clue_used)

                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/GameDetails.json"), "w") as game_details_json_file:
                        json.dump(response, game_details_json_file)

                    self.statusUpdated.emit(game_status)

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls then pass
                self.apiStatus.emit(0)

            except json.decoder.JSONDecodeError:
                # if the codes inside the try block faces json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the codes inside the try block faces simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From GameDetails API)")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        # setting ResettingGame to True
                        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                            thread_file_response = json.load(thread_file)
                            thread_file_response["ResettingGame"] = True

                        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file_x:
                            json.dump(thread_file_response, thread_file_x)

                        self.custom_game_status.emit()
                else:
                    print(">> Console output - Not a 401 error")

            except PermissionError:
                # application update detected
                self.update_detected.emit()

            else:
                # if no error then
                self.apiStatus.emit(1)

            finally:
                # and finally
                time.sleep(3)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsGameDetailsThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.update_detected.emit()


class ShutdownRestartRequest(QThread):

    # signals
    shutdown = pyqtSignal()
    restart = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {unique_code}:{api_key}"

        shutdown_restart_api = GET_SHUTDOWN_RESTART_REQUEST.format(unique_code=unique_code)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsShutdownRestartRequestThreadRunning"] is True:
                    pass

                else:
                    return

                print(">>> Console output - Shutdown restart response")
                json_response = requests.get(shutdown_restart_api, headers=headers)
                json_response.raise_for_status()

                deviceRequestId = json_response.json()["DeviceRequestid"]
                requestId = json_response.json()["RequestID"]

                if requestId == 8:
                    url = POST_DEVICE_API.format(device_unique_code=unique_code, deviceRequestId=deviceRequestId)
                    response = requests.post(url, headers=headers)
                    if response.status_code == 200:
                        self.restart.emit()
                    else:
                        pass

                elif requestId == 9:
                    url = POST_DEVICE_API.format(device_unique_code=unique_code, deviceRequestId=deviceRequestId)
                    response = requests.post(url, headers=headers)
                    if response.status_code == 200:
                        self.shutdown.emit()
                    else:
                        pass

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls, then pass
                pass

            except json.decoder.JSONDecodeError:
                # if the code inside the try is facing json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the code inside the try is facing simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From ShutdownRestart API )")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        print(">>> Console output - API Token Expired (Shutdown Restart)")
                else:
                    print(">> Console output - Not a 401 error")

            except FileNotFoundError:
                # if the code faces the FilNotFoundError then pass
                pass

            finally:
                # and finally
                time.sleep(15)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsShutdownRestartRequestThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.restart.emit()


class UpdateRoomInfo(QThread):

    # signals
    update_detected = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        device_unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

        get_room_info_api = ROOM_INFO_API.format(device_unique_code=device_unique_code)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsUpdateRoomInfoThreadRunning"] is True:
                    pass

                else:
                    return

                print(">>> Console output - Update Room Info Response ")
                response_of_room_info_api = requests.get(get_room_info_api, headers=headers)
                response_of_room_info_api.raise_for_status()

                dictionary = {"Room Minimum Players": response_of_room_info_api.json()["RoomMinPlayers"],
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

                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/device configurations.json"), "w") as device_config_json_file:
                    json.dump(dictionary, device_config_json_file)

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls then pass
                pass

            except json.decoder.JSONDecodeError:
                # if the codes inside the try block faces json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the codes inside the try block faces simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From UpdateRoomInfo API )")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        print(">>> Console output - API Token Expired (UpdateRoomInfo)")
                else:
                    print(">> Console output - Not a 401 error")

            except PermissionError:
                # application update detected
                self.update_detected.emit()

            else:
                # if no error then
                pass

            finally:
                # and finally
                time.sleep(10)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsUpdateRoomInfoThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.update_detected.emit()


class GetGameClue(QThread):

    # signals
    statusChanged = pyqtSignal()
    update_detected = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/GameDetails.json")) as game_details_json_file:
            initial_dictionary = json.load(game_details_json_file)

        game_details_response = initial_dictionary
        initial_gameId = game_details_response["gameId"]

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        device_unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

        game_clue_url = GET_GAME_CLUE_API.format(initial_gameId=initial_gameId)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsGameClueThreadRunning"] is True:
                    pass

                else:
                    return

                print(">>> Console output - Clue response")
                json_response = requests.get(game_clue_url, headers=headers)
                json_response.raise_for_status()
                gameClueId = json_response.json()["gameClueId"]
                gameId = json_response.json()["gameId"]

                requests.post(POST_GAME_CLUE.format(gameId=gameId, gameClueId=gameClueId), headers=headers).raise_for_status()

                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/GameClue.json"), "w") as game_clue_json_file:
                    json.dump(json_response.json(), game_clue_json_file)

                self.statusChanged.emit()

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls, then pass
                pass

            except json.decoder.JSONDecodeError:
                # if the code inside the try is facing json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the code inside the try is facing simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From GetGameClue API )")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        print(">>> Console output - API Token Expired (GetGameClue)")
                else:
                    print(">> Console output - Not a 401 error")

            except KeyError:
                # if the code inside the try block faces KeyError, then pass
                pass

            except PermissionError:
                # application update detected
                self.update_detected.emit()

            else:
                # if no error then
                pass

            finally:
                # and finally
                time.sleep(3)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsGameClueThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.update_detected.emit()


class GetTimerRequest(QThread):

    # signals
    updateTimer = pyqtSignal()
    update_detected = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        device_unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {device_unique_code}:{api_key}"

        get_timer_request_api = GET_TIMER_REQUEST.format(device_unique_code)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsTimerRequestThreadRunning"] is True:
                    pass

                else:
                    return

                print(">>> Console output - Timer response")
                response = requests.get(get_timer_request_api, headers=headers)
                response.raise_for_status()

                request_id = response.json()["DeviceRequestid"]
                device_key = response.json()["DeviceKey"]
                requests.post(POST_DEVICE_API.format(device_unique_code=device_key, deviceRequestId=request_id), headers=headers).raise_for_status()

                self.updateTimer.emit()

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls, then pass
                pass

            except json.decoder.JSONDecodeError:
                # if the code inside the try is facing json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the code inside the try is facing simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From GetTimerRequest API )")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        print(">>> Console output - API Token Expired (GetTimeRequest)")
                else:
                    print(">> Console output - Not a 401 error")

            else:
                # if no error then
                pass

            finally:
                # and finally
                time.sleep(6)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsTimerRequestThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.update_detected.emit()


class DownloadConfigs(QThread):

    # signals
    downloadFiles = pyqtSignal()
    update_detected = pyqtSignal()

    def run(self):
        """ this is an autorun method which is triggered as soon as the thread is started, this method holds all the
            codes for every work, the thread does"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/unique_code.json")) as unique_code_json_file:
            initial_dictionary = json.load(unique_code_json_file)

        unique_code_response = initial_dictionary
        unique_code = unique_code_response["Device Unique Code"]
        api_key = unique_code_response["apiKey"]

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Basic {unique_code}:{api_key}"

        download_files_request_api = DOWNLOAD_FILES_REQUEST.format(unique_code=unique_code)

        while True:
            try:
                with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                    thread_file_response = json.load(thread_file)

                if thread_file_response["IsDownloadConfigsThreadRunning"] is True:
                    pass
                else:
                    return

                print(">>> Console Output - Download config response")
                response = requests.get(download_files_request_api, headers=headers)
                response.raise_for_status()
                request_id = response.json()["DeviceRequestid"]
                device_key = response.json()["DeviceKey"]
                requests.post(POST_DEVICE_API.format(device_unique_code=device_key, deviceRequestId=request_id), headers=headers).raise_for_status()

                self.downloadFiles.emit()
                return

            except requests.exceptions.ConnectionError:
                # if the code inside the try block faces connection error while making api calls, then pass
                pass

            except json.decoder.JSONDecodeError:
                # if the code inside the try is facing json decode error then pass
                pass

            except simplejson.errors.JSONDecodeError:
                # if the code inside the try is facing simplejson decode error then pass
                pass

            except requests.exceptions.HTTPError as request_error:
                if "401 Client Error" in str(request_error):
                    print("401 Client Error - Device Removed or Not Registered ( From DownloadConfigs API )")
                    with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as thread_file:
                        thread_file_response = json.load(thread_file)

                    if thread_file_response["ResettingGame"] is True:
                        pass
                    else:
                        print(">>> Console output - API Token Expired (DownloadConfigs)")
                else:
                    print(">> Console output - Not a 401 error")

            except FileNotFoundError:
                # if the code faces the FilNotFoundError then pass
                pass

            finally:
                # and finally
                time.sleep(15)

    def stop(self):
        """this method when called updates the thread running status to False and in the next loop when the condition
           checks the status, the condition turns False and breaks the thread"""

        with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json")) as initial_thread_file:
            thread_file_response = json.load(initial_thread_file)

        thread_file_response["IsDownloadConfigsThreadRunning"] = False

        try:
            with open(os.path.join(MASTER_DIRECTORY, "assets/application data/ThreadInfo.json"), "w") as thread_file:
                json.dump(thread_file_response, thread_file)

        except PermissionError:
            self.update_detected.emit()

