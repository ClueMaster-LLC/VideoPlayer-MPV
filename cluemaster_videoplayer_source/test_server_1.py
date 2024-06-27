import asyncio
import websockets
import json

connected_clients = set()


async def handler(websocket, path):
    # Register the client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Here we can handle incoming messages if needed
            pass
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        # Unregister the client
        connected_clients.remove(websocket)


async def send_command_to_all_clients(command):
    if connected_clients:
        message = json.dumps({"command": command})
        await asyncio.wait([client.send(message) for client in connected_clients])


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        while True:
            command = input("Enter command to synchronize video (play/pause): ")
            await send_command_to_all_clients(command)


if __name__ == "__main__":
    asyncio.run(main())
