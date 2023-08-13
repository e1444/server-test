import asyncio
import time


class EchoServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print(f"Received: {message}")
        self.transport.write(data)  # Echo back the data to the client

    def connection_lost(self, exc):
        print("Client disconnected")


async def game_loop():
    running = True

    i = 0

    while running:
        if i == 60:
            i = 0
            print(time.time())

        i += 1

        await asyncio.sleep(1/60)


async def server_loop(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoServerProtocol, host, port)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


async def main():
    server_task = asyncio.create_task(server_loop('localhost', 8888))
    game_task = asyncio.create_task(game_loop())
    await asyncio.gather(server_task, game_task)

asyncio.run(main())
