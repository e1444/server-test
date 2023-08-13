import asyncio
import uvloop

import multiprocessing


BUFFER_SIZE = 4


def send_message(conn, msg: bytes) -> None:
    conn.send(msg)


def recv_message(conn) -> bytes:
    msg = conn.recv()
    while conn.poll():
        msg = conn.recv()
    return msg


async def send_net_message(writer, msg: bytes) -> None:
    writer.write(str(len(msg)).encode().ljust(BUFFER_SIZE) + msg)
    await writer.drain()


async def recv_net_message(reader) -> bytes:
    buf = await reader.read(BUFFER_SIZE)
    msg_data = await reader.read(int(buf) + BUFFER_SIZE)

    while len(msg_data) != int(buf):
        buf = msg_data[int(buf):]
        msg_data = await reader.read(int(buf) + BUFFER_SIZE)

    return msg_data


class ClientContext:
    clients: dict

    def __init__(self, conn):
        self.conn = conn
        self.clients = {}

    def add_client(self, _id, client_writer):
        self.clients[_id] = client_writer

    def remove_client(self, _id):
        self.clients.pop(_id)

    async def handle_client(self, client_reader, client_writer):
        _id = len(self.clients)
        self.add_client(_id, client_writer)

        await send_net_message(client_writer, str({'id': _id}).encode())

        async def receive_data():
            while True:
                data = await recv_net_message(client_reader)

                send_message(self.conn, data)

                message = data.decode()
                print(f"Received from client: {message}")

        async def send_data():
            while True:
                await asyncio.sleep(0)
                if self.conn.poll():
                    msg = recv_message(self.conn)

                    # Broadcast the updated game_state to all connected clients
                    for __id, client in self.clients.items():
                        await send_net_message(client, msg)

        receive_task = asyncio.create_task(receive_data())
        send_task = asyncio.create_task(send_data())

        try:
            await asyncio.gather(receive_task, send_task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error with client {_id}: {e}")
        finally:
            self.remove_client(_id)
            client_writer.close()
            await client_writer.wait_closed()
            print(f"Connection from {_id} closed")


def pygame_game_loop(conn):
    import pygame

    # Clock
    clock = pygame.time.Clock()
    pos = [100, 100]

    while True:
        if conn.poll():
            msg = eval(recv_message(conn).decode())
            pos[0] += msg[0]
            pos[1] += msg[1]

        send_message(conn, str(pos).encode())

        clock.tick(60)


async def run_server(ctx):
    host = 'localhost'
    port = 5555

    # Start the server
    server = await asyncio.start_server(ctx.handle_client, host, port)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    # Serve clients indefinitely
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    uvloop.install()

    game_conn, h_input_conn = multiprocessing.Pipe()

    # Start the game loop and input handling processes
    game_process = multiprocessing.Process(target=pygame_game_loop, args=(game_conn,))
    game_process.start()

    ctx = ClientContext(h_input_conn)
    asyncio.run(run_server(ctx))

    # Wait for the game process to finish
    game_process.terminate()
    game_process.join()
