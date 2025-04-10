import pygame
import sys
import os
import random

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 40
GRID_SIZE = 9
MARGIN = 50
WIDTH = TILE_SIZE * GRID_SIZE + MARGIN * 2
HEIGHT = TILE_SIZE * GRID_SIZE + MARGIN * 2
BOMB_COUNT = 10
FPS = 60

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 128, 0)

# Setup screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minesweeper Puppy 🐶")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 32)

# Load images
def load_images_from_folder(folder):
    images = []
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            img = pygame.image.load(os.path.join(folder, filename)).convert_alpha()
            images.append(img)
    return images

idle_frames = load_images_from_folder('assets/idle')
walk_frames = load_images_from_folder('assets/walk')
dead_frames = load_images_from_folder('assets/dead')
bomb_image = pygame.transform.scale(pygame.image.load("assets/bomb.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))

# Puppy class
class Puppy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.state = 'idle'
        self.animations = {
            'idle': idle_frames,
            'walk': walk_frames,
            'dead': dead_frames
        }
        self.current_frame = 0
        self.image = self.animations[self.state][self.current_frame]
        self.original_image = self.image
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.animation_speed = 0.1
        self.time_since_last_frame = 0
        self.dead_timer = 0
        self.scale = 1.5
        self.flipped = False

    def update(self, dt, target_pos):
        if self.state != 'dead':
            distance = pygame.math.Vector2(target_pos) - self.rect.center
            if distance.length() > 5:
                self.state = 'walk'
                move = distance.normalize() * 2
                self.rect.center += move
            else:
                self.state = 'idle'

            # Determine direction (flip when moving left)
            direction = target_pos[0] - self.rect.centerx
            self.flipped = direction < 0

            if self.current_frame >= len(self.animations[self.state]):
                self.current_frame = 0

            frame = self.animations[self.state][self.current_frame]
            if self.flipped:
                frame = pygame.transform.flip(frame, True, False)

            self.image = pygame.transform.scale(frame, (int(32 * self.scale), int(32 * self.scale)))
            self.rect = self.image.get_rect(center=self.rect.center)

        else:
            self.dead_timer += dt
            if self.scale < 20:
                self.scale += dt * 10
            center = (WIDTH // 2, HEIGHT // 2)
            if self.current_frame >= len(self.animations['dead']):
                self.current_frame = len(self.animations['dead']) - 1

            frame = self.animations['dead'][self.current_frame]
            self.image = pygame.transform.scale(frame, (int(32 * self.scale), int(32 * self.scale)))
            self.rect = self.image.get_rect(center=center)

        self.time_since_last_frame += dt
        if self.time_since_last_frame >= self.animation_speed:
            self.time_since_last_frame = 0
            self.current_frame += 1
            if self.current_frame >= len(self.animations[self.state]):
                if self.state == 'dead':
                    self.current_frame = len(self.animations[self.state]) - 1
                else:
                    self.current_frame = 0

    def die(self):
        self.state = 'dead'
        self.current_frame = 0
        self.dead_timer = 0

# Tile class
class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(MARGIN + x*TILE_SIZE, MARGIN + y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.revealed = False
        self.bomb = False
        self.flagged = False
        self.adjacent_bombs = 0

    def draw(self):
        color = GRAY if self.revealed else WHITE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 1)
        if self.revealed and self.bomb:
            screen.blit(bomb_image, self.rect)
        elif self.revealed and self.adjacent_bombs > 0:
            text = font.render(str(self.adjacent_bombs), True, BLUE if self.adjacent_bombs == 1 else GREEN)
            text_rect = text.get_rect(center=self.rect.center)
            screen.blit(text, text_rect)

# Grid setup
def generate_grid():
    grid = [[Tile(x, y) for y in range(GRID_SIZE)] for x in range(GRID_SIZE)]
    bombs_placed = 0
    while bombs_placed < BOMB_COUNT:
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        if not grid[x][y].bomb:
            grid[x][y].bomb = True
            bombs_placed += 1

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if grid[x][y].bomb:
                continue
            count = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if grid[nx][ny].bomb:
                            count += 1
            grid[x][y].adjacent_bombs = count
    return grid

# Retry Modal
class RetryModal:
    def __init__(self):
        self.retry_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 30, 90, 30)
        self.cancel_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 - 30, 90, 30)
        self.visible = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def draw(self):
        if self.visible:
            modal_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            modal_bg.fill((0, 0, 0, 180))
            screen.blit(modal_bg, (0, 0))

            mouse_pos = pygame.mouse.get_pos()

            # Hover color logic
            retry_color = (200, 255, 200) if self.retry_rect.collidepoint(mouse_pos) else WHITE
            cancel_color = (255, 200, 200) if self.cancel_rect.collidepoint(mouse_pos) else WHITE

            # Draw buttons with hover color
            pygame.draw.rect(screen, retry_color, self.retry_rect)
            pygame.draw.rect(screen, cancel_color, self.cancel_rect)
            pygame.draw.rect(screen, BLACK, self.retry_rect, 2)
            pygame.draw.rect(screen, BLACK, self.cancel_rect, 2)

            # Draw text centered inside buttons
            retry_text = font.render("Retry", True, BLACK)
            cancel_text = font.render("Cancel", True, BLACK)

            retry_text_rect = retry_text.get_rect(center=self.retry_rect.center)
            cancel_text_rect = cancel_text.get_rect(center=self.cancel_rect.center)

            screen.blit(retry_text, retry_text_rect)
            screen.blit(cancel_text, cancel_text_rect)

# Main loop
def main():
    puppy = Puppy()
    all_sprites = pygame.sprite.Group(puppy)
    grid = generate_grid()
    modal = RetryModal()
    game_over = False
    running = True
    while running:
        dt = clock.tick(FPS) / 1_000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                pos = pygame.mouse.get_pos()
                for row in grid:
                    for tile in row:
                        if tile.rect.collidepoint(pos) and not tile.revealed:
                            tile.revealed = True
                            if tile.bomb:
                                puppy.die()
                                game_over = True
                                modal.show()
            elif event.type == pygame.MOUSEBUTTONDOWN and game_over:
                if modal.retry_rect.collidepoint(event.pos):
                    main()  # restart
                elif modal.cancel_rect.collidepoint(event.pos):
                    running = False

        mouse_pos = pygame.mouse.get_pos()
        if not game_over:
            all_sprites.update(dt, mouse_pos)
        else:
            all_sprites.update(dt, (WIDTH//2, HEIGHT//2))

        screen.fill(DARK_GRAY)

        for row in grid:
            for tile in row:
                tile.draw()

        all_sprites.draw(screen)
        modal.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
