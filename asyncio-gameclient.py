import asyncio
import pygame
import uvloop

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

# Network
host = 'localhost'
port = 8888


async def game_loop():
    pygame.init()

    # Initialize the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Move the Block!")

    # Player starting position
    server_x, server_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    # Clock
    clock = pygame.time.Clock()

    reader, writer = await asyncio.open_connection(host, port)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        # Move the player based on keyboard input
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
            writer.write(f'{d_x},{d_y}'.encode())
            await writer.drain()

            data = await reader.read(100)
            print(f"Received response from server: {data.decode()}")
            server_x, server_y = [int(x) for x in data.decode().split(sep=',')]

        # Clear the screen
        screen.fill(WHITE)

        # Draw the player (a simple red block)
        pygame.draw.rect(screen, RED, (server_x, server_y, PLAYER_WIDTH, PLAYER_HEIGHT))

        # Update the display
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(game_loop())
