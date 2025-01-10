import asyncio
import websockets


async def run_command(command):
    print(f"Running command: {command}")
    # Simulate command execution with a simple print statement
    # You can replace this with actual command execution logic
    result = f"Executed: {command}"
    return result


async def listen_for_commands(uri):
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        while True:
            try:
                command = await websocket.recv()
                print(f"Received command: {command}")
                result = await run_command(command)
                await websocket.send(result)
            except websockets.ConnectionClosed:
                print("Connection closed")
                break


if __name__ == "__main__":
    uri = "ws://192.168.1.20:8765"
    asyncio.get_event_loop().run_until_complete(listen_for_commands(uri))
