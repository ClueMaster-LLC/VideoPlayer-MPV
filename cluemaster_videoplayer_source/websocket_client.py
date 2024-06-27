import asyncio
import websockets
import json

#from mpv import MPV

auth_token = "YOUR_SECRET_BEARER_TOKEN"
server_url = "ws://localhost:8765"


class VideoPlayer:
    def __init__(self):
        self.player = MPV(input_default_bindings=True, input_vo_keyboard=True)
        self.player.observe_property("time-pos", self.time_pos_observer)
        self.desired_time_pos = 0

    def play(self, media_file):
        self.player.play(media_file)
        self.player.wait_until_playing()
        asyncio.create_task(self.sync_video())

    def pause(self):
        self.player.pause = True

    def unpause(self):
        self.player.pause = False

    def time_pos_observer(self, name, value):
        if value is not None:
            self.desired_time_pos = value

    async def sync_video(self):
        while True:
            current_time = self.player.time_pos
            if current_time and abs(current_time - self.desired_time_pos) > 0.1:
                self.player.seek(self.desired_time_pos, "absolute")
            await asyncio.sleep(1)


async def listen_to_server(video_player):
    async def reconnect():
        while True:
            try:
                async with websockets.connect(server_url,
                                              extra_headers={"Authorization": f"Bearer {auth_token}"}) as websocket:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        command = data.get("command")
                        media_file = data.get("media_file")
                        if command == "play" and media_file:
                            video_player.play(media_file)
                        elif command == "pause":
                            video_player.pause()
                        elif command == "unpause":
                            video_player.unpause()
            except Exception as e:
                print(f"Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    await reconnect()


if __name__ == "__main__":
    video_player = VideoPlayer()
    asyncio.run(listen_to_server(video_player))
