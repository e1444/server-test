import asyncio


class GameServer:
    def __init__(self):
        self.clients = set()
        self.player_x = 400
        self.player_y = 300

    def add_client(self, client_writer):
        self.clients.add(client_writer)

    def remove_client(self, client_writer):
        self.clients.remove(client_writer)

    async def handle_client(self, client_reader, client_writer):
        self.add_client(client_writer)
        try:
            while True:
                data = await client_reader.read(100)
                if not data:
                    break

                message = data.decode().strip()
                print(f"Received from client: {message}")

                # Process the message received from the client and update game_state
                # Expect '{d_x},{d_y}'
                d_x, d_y = [int(x) for x in message.split(sep=',')]
                self.player_x += d_x
                self.player_y += d_y

                # Broadcast the updated game_state to all connected clients
                for client in self.clients:
                    try:
                        client.write(f"{self.player_x},{self.player_y}".encode())
                        await client.drain()
                    except:
                        # Remove the client if there's an error sending data
                        self.remove_client(client)
        except asyncio.CancelledError:
            pass
        finally:
            self.remove_client(client_writer)
            client_writer.close()
            await client_writer.wait_closed()

    async def main(self, host, port):
        server = await asyncio.start_server(self.handle_client, host, port)

        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    game_server = GameServer()
    asyncio.run(game_server.main("localhost", 5555))
