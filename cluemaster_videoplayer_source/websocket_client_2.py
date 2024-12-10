import asyncio
import websockets
import json
import os
from mpv import MPV
from settings import *

auth_token = "YOUR_SECRET_BEARER_TOKEN"
server_url = "ws://192.168.1.20:8765"
client_id = "unique_client_id_001"
media_folder = os.path.join(MASTER_DIRECTORY, "assets/media/")
# media_folder = "/path/to/media/folder"

class VideoPlayer:
    def __init__(self):
        self.player = MPV(input_default_bindings=True, input_vo_keyboard=True)
        self.desired_time_pos = 0
        self.playlist = self.scan_media_folder()
        self.looping = True

    def scan_media_folder(self):
        return [os.path.join(media_folder, file) for file in os.listdir(media_folder) if file.endswith(('.mp4', '.mkv', '.jpg', '.png'))]

    def play(self, media_file):
        self.looping = False
        self.player.play(media_file)
        self.player.wait_until_playing()
        asyncio.create_task(self.sync_video())

    def pause(self):
        self.player.pause = True

    def set_time(self, time_pos):
        self.player.seek(time_pos, "absolute")

    async def sync_video(self):
        while not self.looping:
            current_time = self.player.time_pos
            if current_time and abs(current_time - self.desired_time_pos) > 0.1:
                self.set_time(self.desired_time_pos)
            await asyncio.sleep(1)

    async def loop_playlist(self):
        while True:
            if self.looping:
                for media_file in self.playlist:
                    self.player.play(media_file)
                    self.player.wait_until_playing()
                    await asyncio.sleep(self.player.duration or 0)
            await asyncio.sleep(1)

async def listen_to_server(video_player):
    async def reconnect():
        while True:
            try:
                async with websockets.connect(server_url, extra_headers={"Authorization": f"Bearer {auth_token}"}) as websocket:
                    print("Connected to the server.")
                    await websocket.send(client_id)  # Send client ID to server
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        command = data.get("command")
                        media_file = data.get("media_file")
                        if command == "play" and media_file:
                            video_player.play(media_file)
                        elif command == "pause":
                            video_player.pause()
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    await reconnect()

if __name__ == "__main__":
    video_player = VideoPlayer()
    asyncio.create_task(video_player.loop_playlist())  # Start looping the playlist
    asyncio.run(listen_to_server(video_player))
