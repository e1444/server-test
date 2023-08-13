import asyncio
import uvloop

import multiprocessing

FPS = 60
SERVER_TICK_RATE = 60

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Player properties
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 50
PLAYER_SPEED = 5

BUFFER_SIZE = 4


async def send_net_message(writer, msg: bytes) -> None:
    writer.write(str(len(msg)).encode().ljust(BUFFER_SIZE) + msg)
    await writer.drain()


async def recv_net_message(reader) -> bytes:
    buf = await reader.read(BUFFER_SIZE)
    msg_data = await reader.read(int(buf) + BUFFER_SIZE)

    while len(msg_data.rstrip()) != int(buf):
        print(1)
        buf = msg_data[int(buf):]
        msg_data = await reader.read(int(buf) + BUFFER_SIZE)

    return msg_data


async def handle_input(conn):
    host = 'localhost'
    port = 5555

    reader, writer = await asyncio.open_connection(host, port)

    data = await recv_net_message(reader)
    print(f"Received response from server: {data.decode()}")

    async def receive_data():
        while True:
            data = await recv_net_message(reader)
            print(f"Received response from server: {data.decode()}")
            conn.send(eval(data))

    async def send_data():
        while True:
            await asyncio.sleep(0)
            if conn.poll():
                d_x, d_y = conn.recv()
                await send_net_message(writer, f'({d_x},{d_y})'.encode())

    receive_task = asyncio.create_task(receive_data())
    send_task = asyncio.create_task(send_data())

    try:
        await asyncio.gather(receive_task, send_task)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"{e}")
    finally:
        writer.close()
        await writer.wait_closed()


def pygame_game_loop(conn):
    import pygame

    pygame.init()

    # Initialize the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Move the Block!")

    # Clock
    clock = pygame.time.Clock()

    # Game vars
    x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        keys = pygame.key.get_pressed()

        d_x, d_y = 0, 0

        if keys[pygame.K_LEFT]:
            d_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            d_x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            d_y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            d_y += PLAYER_SPEED

        if (d_x, d_y) != (0, 0):
            # Send the updated keys to the asyncio loop
            conn.send((d_x, d_y))

        # Receive updated locations
        if conn.poll():
            msg = conn.recv()
            x = msg[0]
            y = msg[1]

        # Clear the screen
        screen.fill(WHITE)

        # Draw the player (a simple red block)
        pygame.draw.rect(screen, RED, (x, y, PLAYER_WIDTH, PLAYER_HEIGHT))

        # Update the display
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    uvloop.install()

    game_conn, h_input_conn = multiprocessing.Pipe()

    # Start the game loop and input handling processes
    game_process = multiprocessing.Process(target=pygame_game_loop, args=(game_conn,))
    game_process.start()

    # Create an asyncio event loop and run the handle_input coroutine
    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_until_complete(handle_input(h_input_conn))

    # Wait for the game process to finish
    game_process.terminate()
    game_process.join()
