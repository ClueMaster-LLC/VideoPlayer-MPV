import asyncio
import websockets
import json

async def handle_command(command):
    if command == "play":
        print("Playing video")
        # Add code to play video
    elif command == "pause":
        print("Pausing video")
        # Add code to pause video

async def listen_to_server():
    async with websockets.connect("ws://192.168.1.26:8765") as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            command = data.get("command")
            if command:
                await handle_command(command)

if __name__ == "__main__":
    asyncio.run(listen_to_server())
