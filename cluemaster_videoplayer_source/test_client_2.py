import asyncio
import websockets
import json
import vlc
import time

auth_token = "YOUR_SECRET_BEARER_TOKEN"
server_url = "ws://localhost:8765"

class VideoPlayer:
    def __init__(self):
        self.player = vlc.MediaPlayer()
        self.desired_time_pos = 0

    def play(self, media_file):
        self.player.set_media(vlc.Media(media_file))
        self.player.play()
        time.sleep(1)  # Allow player to start
        asyncio.create_task(self.sync_video())

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def get_time(self):
        return self.player.get_time() / 1000.0  # Convert milliseconds to seconds

    def set_time(self, time_pos):
        self.player.set_time(int(time_pos * 1000))  # Convert seconds to milliseconds

    async def sync_video(self):
        while self.player.is_playing():
            current_time = self.get_time()
            if abs(current_time - self.desired_time_pos) > 0.1:
                self.set_time(self.desired_time_pos)
            await asyncio.sleep(1)

async def listen_to_server(video_player):
    async def reconnect():
        while True:
            try:
                async with websockets.connect(server_url, extra_headers={"Authorization": f"Bearer {auth_token}"}) as websocket:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        command = data.get("command")
                        media_file = data.get("media_file")
                        if command == "play" and media_file:
                            video_player.play(media_file)
                        elif command == "pause":
                            video_player.pause()
                        elif command == "stop":
                            video_player.stop()
            except Exception as e:
                print(f"Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    await reconnect()

if __name__ == "__main__":
    video_player = VideoPlayer()
    asyncio.run(listen_to_server(video_player))
