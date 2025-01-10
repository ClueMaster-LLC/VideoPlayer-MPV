import asyncio
import platform
import threading
import time
import websockets
import json
import GPUtil
from PyQt5.QtGui import QFont, QMovie
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QApplication
from mpv import MPV

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
# from websockets.legacy.async_timeout import timeout

import threads
from settings import *
from websocket_client_2 import media_folder

# import game_idle

auth_token = "YOUR_SECRET_BEARER_TOKEN"
server_url = "ws://192.168.1.20:8765"
MACADDR = "client1"  # Change this to the unique identifier for the client


class WebsocketClient(threading.Thread):
    def __init__(self):
        super(WebsocketClient, self).__init__()
        print(">>> websocket_client - WEBSOCKET CLIENT STARTED............")
        # video_player_ojb = VideoPlayer()
        # asyncio.run(listen_to_server(video_player_ojb, MACADDR))


class VideoPlayer:
    def __init__(self):
        self.playing_overlay = False
        self.media_folder = os.path.join(MASTER_DIRECTORY, "assets/media/")
        self.looping = True
        self.screen_height = None
        self.screen_width = None
        self.main_layout = None
        self.media_assets_location = None
        self.video_media = None
        self.filtered_usb_files: list = []
        self.playlist_files: list = []

        print(f"GPU FOUND: ", GPUtil.getAvailable())

        if not GPUtil.getAvailable():
            self.player = MPV(input_default_bindings=True,
                              input_vo_keyboard=False,
                              hwdec="no",
                              vo="x11",
                              keep_open="always",
                              fs="yes")
        else:
            self.player = MPV(input_default_bindings=True,
                              input_vo_keyboard=False,
                              hwdec="auto",
                              vo="gpu",
                              keep_open="always",
                              fs="yes")
            # loop_playlist="inf",

        self.player.observe_property("time-pos", self.time_pos_observer)
        self.desired_time_pos = 0
        self.current_index = 0
        self.desired_time_pos = 0
        self.looping_playlist_task = None
        self.interrupted = False
        self.playlist_load()
        # self.play_loop()
        # self.loop_media()

    # def scan_media_folder(self):
    #     media_files = [os.path.join(self.media_folder, f) for f in os.listdir(self.media_folder) if f.endswith(('.mp4', '.mpg', '.jpg', '.png'))]
    #     return media_files

    def play(self, media_file, overlay=False):
        # self.player.play(media_folder + media_file)
        # self.unpause()

        self.playlist_files.clear()
        # self.player.playlist_append(media_folder + media_file)
        for file in self.playlist_files:
            self.player.playlist_append(file)
            print(f"File added to list: {file}")
        # self.player.playlist_play_index(0)
        # self.unpause()
        print(f"ready to play {self.playlist_files}")

    async def loop_media(self):
        while True:
            if not self.playing_overlay:
                self.play(self.playlist_files[self.current_index])
                self.current_index = (self.current_index + 1) % len(self.playlist_files)
            await asyncio.sleep(0.1)

    # def play(self, media_file, overlay=False):
    #     if overlay:
    #         self.player.loadfile(media_folder + media_file, mode="replace")
    #         self.playing_overlay = True
    #     else:
    #         self.player.play(media_folder + media_file)
    #         self.player.wait_until_playing()
    #         self.playing_overlay = False
    #         asyncio.create_task(self.sync_video())

    # def play_loop(self):
    #     self.player.playlist_play_index(self.current_index)

    # def loop_media(self):
    #     while True:
    #         if not self.playing_overlay:
    #             self.play(self.playlist_files[self.current_index])
    #             self.current_index = (self.current_index + 1) % len(self.playlist_files)
    #         asyncio.sleep(0.1)

    def pause(self):
        self.player.pause = True

    def unpause(self):
        self.player.pause = False

    def stop(self):
        self.player.stop()

    def time_pos_observer(self, name, value):
        if value is not None:
            self.desired_time_pos = value

    # async def sync_video(self):
    #     while not self.looping:
    #         current_time = self.player.time_pos
    #         if current_time and abs(current_time - self.desired_time_pos) > 0.1:
    #             self.set_time(self.desired_time_pos)
    #         await asyncio.sleep(1)

    async def sync_video(self):
        while True:
            if self.playing_overlay:
                return
            current_time = self.player.time_pos
            if current_time and abs(current_time - self.desired_time_pos) > 0.1:
                self.set_time(self.desired_time_pos)
            await asyncio.sleep(1)

    def set_time(self, time_pos):
        self.player.seek(time_pos, "absolute")

    def playlist_load(self):
        # adding file to mpv playlist
        print(">>> websocket_client - Loading files from the media folder to the play_list")
        try:
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
                print(f'>>> websocket_client - Error Accessing USB: {usb_error}')
                self.filtered_usb_files = []

            # if there are files then play them.
            media_folder_dir = os.listdir(self.media_folder)

            # test if USB media files exist
            if self.filtered_usb_files:
                print(f'>>> websocket_client - USB FILES LIST HAS : {self.filtered_usb_files}')
            elif not self.filtered_usb_files:
                print(">>> websocket_client - USB LIST IS EMPTY ", self.filtered_usb_files)

            # if there are files then play them.
            media_folder_dir = os.listdir(self.media_folder)

            if len(media_folder_dir) != 0 or self.filtered_usb_files:

                self.video_media = os.path.join(MASTER_DIRECTORY, "assets/media/")
                self.media_assets_location = ([self.video_media + file for file in os.listdir(self.video_media)])

                if self.filtered_usb_files:
                    self.media_assets_location = self.media_assets_location + self.filtered_usb_files

                print(">>> websocket_client - Media Files: ", self.media_assets_location)
                self.playlist_files = self.media_assets_location

                try:
                    # adding file to mpv playlist
                    # print(f'>>> websocket_client - Adding PlayList Files: {self.media_assets_location}')
                    for media_file in self.media_assets_location:
                        self.player.playlist_append(media_file)
                        self.playlist_files.append(media_file)

                    # print(f'>>> websocket_client - PlayList FILES Contains: {self.playlist_files}')

                except Exception as error:
                    print(f'websocket_client - Error Building Playlist: {error}')

            else:
                print(f"websocket_client - No videos found in folder. Nothing to play.")
                self.no_media()

        except Exception as error_playlist:
            print(f'websocket_client - Error Loading PlayList Files: {error_playlist}')


    def no_media(self):

        self.main_layout = QVBoxLayout()

        font = QFont("IBM Plex Mono", 19)

        application_name = QLabel(self)
        application_name.setFont(font)
        application_name.setText("ClueMaster Video Player")
        application_name.setStyleSheet("color: white; font-size: 40px; font-weight: 700;")
        application_name.setGeometry(self.screen_width // 3, 100, 1000, 100)
        application_name.show()

        screensize_txt = QLabel(self)
        screensize_txt.setText(f"Screen Size: {self.screen_width} X {self.screen_height}")
        screensize_txt.setFont(font)
        screensize_txt.setStyleSheet("color: white; font-size: 60px; font-weight:bold;")
        screensize_txt.setGeometry(self.screen_width // 3, 200, 1000, 100)
        screensize_txt.show()

        message = QLabel(self)
        message.setFont(font)
        message.setStyleSheet("color: white; font-size: 30px; font-weight:bold;")
        message.setText("Idle Screen: No Media Files Found")
        message.setGeometry(self.screen_width // 3, 300, 1000, 100)
        message.show()

        ipaddress = QLabel(self)
        ipaddress.setFont(font)
        ipaddress.setStyleSheet("color: white; font-size: 30px; font-weight:bold;")
        ipaddress.setText(f"IP Address: {threads.IP_ADDRESS}")
        ipaddress.setGeometry(self.screen_width // 3, 400, 1000, 100)
        ipaddress.show()

        device_key = QLabel(self)
        device_key.setFont(font)
        device_key.setStyleSheet("color: white; font-size: 30px; font-weight:bold;")
        device_key.setText(f"Device Key: {threads.UNIQUE_CODE}")
        device_key.setGeometry(self.screen_width // 3, 500, 1000, 100)
        device_key.show()

        gif = QMovie(os.path.join(ROOT_DIRECTORY, "assets/icons/security_loading.gif"))
        gif.start()

        loading_gif = QLabel(self)
        loading_gif.setMovie(gif)
        loading_gif.setGeometry(self.screen_width // 3, self.screen_height - 200, 1000, 200)
        loading_gif.show()

async def listen_to_server(video_player, identifier):
    async def reconnect():
        while True:
            try:
                async with websockets.connect(server_url, ping_interval=10, ping_timeout=10,
                                              extra_headers={"Authorization": f"Bearer {auth_token}"}) as websocket:
                    print("Connected to the server.")
                    await websocket.send(MACADDR)  # Send client ID to server
                    print(f">>> websocket_client - Connection to {server_url}")

                    while True:
                        # video_player.playlist_load()
                        # video_player.player.playlist_play_index(0)
                        # video_player.wait_until_playing()
                        print(">>> websocket_client - Waiting for new commands")
                        message = await websocket.recv()
                        data = json.loads(message)
                        command = data.get("command")
                        media_file = data.get("media_file")

                        if command:
                            print(f">>> websocket_client - command was: {command}")
                        if media_file:
                            print(f">>> websocket_client - media_file was: {media_file}")

                        try:
                            if command == "play" and media_file:
                                # media_file = '77-20240801065957-HTVLDL.m4v'
                                # video_player.play(media_file)
                                video_player.play(media_file, overlay=False)
                                # Wait for overlay to finish, then resume the loop
                                await asyncio.sleep(5)
                                video_player.playing_overlay = False

                            elif command == "pause":
                                video_player.pause()
                            elif command == "unpause":
                                video_player.unpause()
                            elif command == "stop":
                                video_player.stop()

                        except FileExistsError as e:
                            if media_file:
                                print(
                                    f">>> websocket_client - Bad Command: {command}, {media_file} does not exist. {e}")
                            else:
                                print(f">>> websocket_client - Bad Command: {command}")

            except websockets.exceptions.ConnectionClosed as e:
                print(f">>> websocket_client - Connection closed: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

            except Exception as e:
                print(f">>> websocket_client - Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

            except asyncio.exceptions.CancelledError:
                print(f">>> websocket_client - Keyboard Interrupt: Disconnecting")
                break

            except json.decoder.JSONDecodeError as e:
                print(f">>> websocket_client - JSON Decoder error: {e}. Reconnecting in 5 seconds...")

    await reconnect()


async def listen(uri, identifier):
    async with websockets.connect(f"{uri}/{identifier}") as websocket:
        async for message in websocket:
            print(f">>> websocket_client - Received: {message}")

if __name__ == "__main__":
    video_player = VideoPlayer()
    # asyncio.create_task(video_player.loop_media())
    print("running")
    asyncio.run(listen_to_server(video_player, MACADDR))



# class Qtest(QWidget):
#     class GameIdleMPVPlayer(QWidget):
#         def __init__(self):
#             super(VideoPlayer, self).__init__()
#
#             # default variables
#             self.screen_width = QApplication.desktop().width()
#             self.screen_height = QApplication.desktop().height()
#
#             # configs
#             self.setAttribute(Qt.WA_DontCreateNativeAncestors)
#             self.setAttribute(Qt.WA_NativeWindow)
