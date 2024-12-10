import asyncio
import threading

import mpv
# import mpv
import websockets
import json
from mpv import MPV

import game_idle

auth_token = "YOUR_SECRET_BEARER_TOKEN"
server_url = "ws://192.168.1.20:8765"
MACADDR = "client1"  # Change this to the unique identifier for the client


class WebsocketClient(threading.Thread):
    def __init__(self):
        super(WebsocketClient, self).__init__()
        print(">>> websocket_client - WEBSOCKET CLIENT STARTED............")
        video_player_ojb = VideoPlayer()
        asyncio.run(listen_to_server(video_player_ojb, MACADDR))


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
        game_idle.COMMAND = "pause"

    def unpause(self):
        self.player.pause = False

    def stop(self):
        self.player.stop()

    def time_pos_observer(self, name, value):
        if value is not None:
            self.desired_time_pos = value

    async def sync_video(self):
        while True:
            current_time = self.player.time_pos
            if current_time and abs(current_time - self.desired_time_pos) > 0.1:
                self.player.seek(self.desired_time_pos, "absolute")
            await asyncio.sleep(1)


async def listen_to_server(video_player, identifier):
    async def reconnect():
        while True:
            try:
                async with websockets.connect(server_url,
                                              extra_headers={"Authorization": f"Bearer {auth_token}"}) as websocket:
                    print("Connected to the server.")
                    await websocket.send(MACADDR)  # Send client ID to server
                    print(f">>> websocket_client - Connection to {server_url}")

                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        command = data.get("command")
                        media_file = data.get("media_file")

                        print(f">>> websocket_client - command was: {command}")
                        print(f">>> websocket_client - media_file was: {media_file}")

                        try:
                            if command == "play" and media_file:
                                # video_player.play(media_file)
                                print(f"{command}: {media_file}")
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

# if __name__ == "__main__":
#     video_player_ojb = VideoPlayer()
#     asyncio.run(listen_to_server(video_player_ojb, MACADDR))
