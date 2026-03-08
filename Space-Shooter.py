import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 50)
STAR_COLOR = (200, 200, 255)

class Particle:
    """Visual particle effect"""
    def __init__(self, x, y, color, velocity=None, lifetime=30):
        self.x = x
        self.y = y
        self.color = color
        if velocity:
            self.vx, self.vy = velocity
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 4)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vy += 0.1  # Gravity effect
    
    def draw(self, screen):
        alpha = self.lifetime / self.max_lifetime
        size = max(1, int(self.size * alpha))
        color = tuple(int(c * alpha) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)
    
    def is_alive(self):
        return self.lifetime > 0

class Star:
    """Background star for parallax effect"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.5, 3)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(150, 255)
    
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, screen):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class Player(pygame.sprite.Sprite):
    """Player spaceship"""
    def __init__(self):
        super().__init__()
        self.width = 40
        self.height = 50
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.draw_ship()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.shoot_delay = 10
        self.invulnerable = 0
        self.shield = False
        self.shield_timer = 0
    
    def draw_ship(self):
        # Draw a cool spaceship
        points = [
            (self.width // 2, 0),  # Top
            (0, self.height),      # Bottom left
            (self.width // 2, self.height - 10),  # Bottom center
            (self.width, self.height)  # Bottom right
        ]
        pygame.draw.polygon(self.image, CYAN, points)
        pygame.draw.polygon(self.image, WHITE, points, 2)
        # Cockpit
        pygame.draw.circle(self.image, BLUE, (self.width // 2, 15), 5)
        # Wings
        pygame.draw.polygon(self.image, CYAN, [
            (0, self.height - 10),
            (10, self.height - 20),
            (15, self.height)
        ])
        pygame.draw.polygon(self.image, CYAN, [
            (self.width, self.height - 10),
            (self.width - 10, self.height - 20),
            (self.width - 15, self.height)
        ])
    
    def update(self, keys_pressed):
        # Movement
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.rect.x -= self.speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.rect.x += self.speed
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.rect.y -= self.speed
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.rect.y += self.speed
        
        # Keep on screen
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)
        
        # Cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer == 0:
                self.shield = False
    
    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.shoot_delay
            return True
        return False
    
    def take_damage(self, damage):
        if self.invulnerable == 0 and not self.shield:
            self.health -= damage
            self.invulnerable = 60
            return True
        return False
    
    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
    
    def activate_shield(self, duration=300):
        self.shield = True
        self.shield_timer = duration
    
    def draw(self, screen):
        # Flash when invulnerable
        if self.invulnerable > 0 and self.invulnerable % 10 < 5:
            return
        
        screen.blit(self.image, self.rect)
        
        # Draw shield
        if self.shield:
            pygame.draw.circle(screen, (0, 255, 255, 100), self.rect.center, 35, 2)
            pygame.draw.circle(screen, (0, 150, 255, 50), self.rect.center, 33, 2)

class Bullet(pygame.sprite.Sprite):
    """Player bullet"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 4
        self.height = 15
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10
        self.damage = 10
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    """Enemy spaceship"""
    def __init__(self, enemy_type=1):
        super().__init__()
        self.type = enemy_type
        
        if enemy_type == 1:  # Basic enemy
            self.width = 30
            self.height = 30
            self.health = 20
            self.speed = 2
            self.color = RED
            self.points = 10
        elif enemy_type == 2:  # Fast enemy
            self.width = 25
            self.height = 25
            self.health = 10
            self.speed = 4
            self.color = ORANGE
            self.points = 20
        else:  # Tank enemy
            self.width = 40
            self.height = 40
            self.health = 50
            self.speed = 1
            self.color = PURPLE
            self.points = 50
        
        self.max_health = self.health
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.draw_enemy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.rect.y = random.randint(-100, -40)
        self.shoot_cooldown = random.randint(60, 120)
    
    def draw_enemy(self):
        # Enemy ship design (inverted triangle)
        points = [
            (self.width // 2, self.height),  # Bottom point
            (0, 0),  # Top left
            (self.width, 0)  # Top right
        ]
        pygame.draw.polygon(self.image, self.color, points)
        pygame.draw.polygon(self.image, WHITE, points, 2)
    
    def update(self):
        self.rect.y += self.speed
        
        # Shoot
        self.shoot_cooldown -= 1
        
        # Remove if off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
    
    def should_shoot(self):
        if self.shoot_cooldown <= 0 and self.rect.y > 0:
            self.shoot_cooldown = random.randint(60, 180)
            return True
        return False
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            return True
        return False

class EnemyBullet(pygame.sprite.Sprite):
    """Enemy bullet"""
    def __init__(self, x, y):
        super().__init__()
        self.width = 4
        self.height = 12
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = 5
        self.damage = 10
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    """Power-up items"""
    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.type = powerup_type
        self.width = 20
        self.height = 20
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if powerup_type == "health":
            self.color = GREEN
            self.symbol = "+"
        elif powerup_type == "shield":
            self.color = CYAN
            self.symbol = "S"
        else:  # rapid_fire
            self.color = YELLOW
            self.symbol = "R"
        
        pygame.draw.circle(self.image, self.color, (self.width // 2, self.height // 2), self.width // 2)
        pygame.draw.circle(self.image, WHITE, (self.width // 2, self.height // 2), self.width // 2, 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Explosion:
    """Explosion animation"""
    def __init__(self, x, y, size=20):
        self.x = x
        self.y = y
        self.particles = []
        self.size = size
        
        # Create explosion particles
        for _ in range(size):
            color = random.choice([RED, ORANGE, YELLOW])
            particle = Particle(x, y, color, lifetime=random.randint(20, 40))
            self.particles.append(particle)
    
    def update(self):
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)
    
    def is_alive(self):
        return len(self.particles) > 0

class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Shooter - Epic Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 72)
        
        # Game state
        self.state = "menu"  # menu, playing, paused, game_over
        self.score = 0
        self.high_score = 0
        self.wave = 1
        self.enemies_killed = 0
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        # Effects
        self.explosions = []
        self.stars = [Star() for _ in range(100)]
        
        # Player
        self.player = None
        
        # Wave spawning
        self.enemy_spawn_timer = 0
        self.enemies_to_spawn = 5
    
    def new_game(self):
        """Start a new game"""
        # Clear all sprites
        self.all_sprites.empty()
        self.bullets.empty()
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.powerups.empty()
        
        # Reset game variables
        self.score = 0
        self.wave = 1
        self.enemies_killed = 0
        self.explosions = []
        self.enemy_spawn_timer = 0
        self.enemies_to_spawn = 5
        
        # Create player
        self.player = Player()
        self.all_sprites.add(self.player)
        
        self.state = "playing"
    
    def spawn_enemy(self):
        """Spawn a new enemy"""
        # Determine enemy type based on wave
        rand = random.random()
        if self.wave < 3:
            enemy_type = 1
        elif self.wave < 6:
            if rand < 0.7:
                enemy_type = 1
            else:
                enemy_type = 2
        else:
            if rand < 0.5:
                enemy_type = 1
            elif rand < 0.85:
                enemy_type = 2
            else:
                enemy_type = 3
        
        enemy = Enemy(enemy_type)
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)
    
    def spawn_powerup(self, x, y):
        """Spawn a power-up with random chance"""
        if random.random() < 0.3:  # 30% chance
            powerup_type = random.choice(["health", "shield", "rapid_fire"])
            powerup = PowerUp(x, y, powerup_type)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.new_game()
                    elif event.key == pygame.K_ESCAPE:
                        return False
                
                elif self.state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "paused"
                    elif event.key == pygame.K_p:
                        self.state = "paused"
                
                elif self.state == "paused":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        self.state = "menu"
                
                elif self.state == "game_over":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.new_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
        
        return True
    
    def update(self):
        """Update game state"""
        if self.state != "playing":
            return
        
        # Update stars
        for star in self.stars:
            star.update()
        
        # Player shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            if self.player.shoot():
                bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
                self.bullets.add(bullet)
                self.all_sprites.add(bullet)
        
        # Update player
        self.player.update(keys)
        
        # Update sprites
        self.bullets.update()
        self.enemies.update()
        self.enemy_bullets.update()
        self.powerups.update()
        
        # Enemy shooting
        for enemy in self.enemies:
            if enemy.should_shoot():
                bullet = EnemyBullet(enemy.rect.centerx, enemy.rect.bottom)
                self.enemy_bullets.add(bullet)
                self.all_sprites.add(bullet)
        
        # Bullet hits enemies
        for bullet in self.bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, self.enemies, False)
            if hit_enemies:
                bullet.kill()
                for enemy in hit_enemies:
                    if enemy.take_damage(bullet.damage):
                        self.score += enemy.points
                        self.enemies_killed += 1
                        self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, 30))
                        self.spawn_powerup(enemy.rect.centerx, enemy.rect.centery)
                        enemy.kill()
        
        # Enemy bullets hit player
        hit_bullets = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for bullet in hit_bullets:
            if self.player.take_damage(bullet.damage):
                self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery, 15))
        
        # Enemies hit player
        hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for enemy in hit_enemies:
            if self.player.take_damage(30):
                self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery, 20))
            self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, 25))
        
        # Power-ups
        hit_powerups = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in hit_powerups:
            if powerup.type == "health":
                self.player.heal(30)
            elif powerup.type == "shield":
                self.player.activate_shield(300)
            elif powerup.type == "rapid_fire":
                self.player.shoot_delay = max(3, self.player.shoot_delay - 2)
        
        # Update explosions
        for explosion in self.explosions[:]:
            explosion.update()
            if not explosion.is_alive():
                self.explosions.remove(explosion)
        
        # Spawn enemies
        if len(self.enemies) < self.enemies_to_spawn:
            self.enemy_spawn_timer += 1
            if self.enemy_spawn_timer > 60:
                self.spawn_enemy()
                self.enemy_spawn_timer = 0
        
        # Check for next wave
        if self.enemies_killed >= self.wave * 5 and len(self.enemies) == 0:
            self.wave += 1
            self.enemies_to_spawn = min(15, 5 + self.wave * 2)
        
        # Check game over
        if self.player.health <= 0:
            self.state = "game_over"
            if self.score > self.high_score:
                self.high_score = self.score
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(DARK_BLUE)
        
        # Draw stars
        for star in self.stars:
            star.update()
            star.draw(self.screen)
        
        # Title with glow effect
        title = self.large_font.render("SPACE SHOOTER", True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        
        # Glow effect
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            glow = self.large_font.render("SPACE SHOOTER", True, BLUE)
            glow_rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], 150 + offset[1]))
            self.screen.blit(glow, glow_rect)
        
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font.render("Epic Edition", True, YELLOW)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        instructions = [
            "CONTROLS:",
            "Arrow Keys / WASD - Move",
            "SPACE - Shoot",
            "P - Pause",
            "ESC - Menu",
            "",
            "Press SPACE to Start",
            "Press ESC to Quit"
        ]
        
        y = 280
        for line in instructions:
            if line == "CONTROLS:":
                text = self.font.render(line, True, CYAN)
            elif line == "":
                y += 10
                continue
            elif "Press" in line:
                text = self.small_font.render(line, True, YELLOW)
            else:
                text = self.small_font.render(line, True, WHITE)
            
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30
        
        # High score
        if self.high_score > 0:
            high_score_text = self.font.render(f"High Score: {self.high_score}", True, GREEN)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            self.screen.blit(high_score_text, high_score_rect)
    
    def draw_game(self):
        """Draw game screen"""
        self.screen.fill(DARK_BLUE)
        
        # Draw stars
        for star in self.stars:
            star.draw(self.screen)
        
        # Draw sprites
        self.bullets.draw(self.screen)
        self.enemies.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
        self.powerups.draw(self.screen)
        
        # Draw player with custom draw method
        self.player.draw(self.screen)
        
        # Draw explosions
        for explosion in self.explosions:
            explosion.draw(self.screen)
        
        # Draw HUD
        # Health bar
        bar_width = 200
        bar_height = 20
        health_ratio = self.player.health / self.player.max_health
        
        pygame.draw.rect(self.screen, RED, (10, 10, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (10, 10, bar_width * health_ratio, bar_height))
        pygame.draw.rect(self.screen, WHITE, (10, 10, bar_width, bar_height), 2)
        
        health_text = self.small_font.render(f"HP: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (15, 12))
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH - 200, 10))
        
        # Wave
        wave_text = self.font.render(f"Wave: {self.wave}", True, CYAN)
        self.screen.blit(wave_text, (SCREEN_WIDTH - 200, 50))
        
        # Shield indicator
        if self.player.shield:
            shield_text = self.small_font.render("SHIELD ACTIVE", True, CYAN)
            self.screen.blit(shield_text, (10, 40))
    
    def draw_pause(self):
        """Draw pause screen"""
        # Dim the background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.large_font.render("PAUSED", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(pause_text, pause_rect)
        
        # Instructions
        resume_text = self.small_font.render("Press P or ESC to Resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(resume_text, resume_rect)
        
        quit_text = self.small_font.render("Press Q to Quit to Menu", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(quit_text, quit_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(DARK_BLUE)
        
        # Draw stars
        for star in self.stars:
            star.draw(self.screen)
        
        # Game Over text
        game_over_text = self.large_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Stats
        stats = [
            f"Final Score: {self.score}",
            f"High Score: {self.high_score}",
            f"Waves Survived: {self.wave}",
            f"Enemies Destroyed: {self.enemies_killed}",
        ]
        
        y = 250
        for stat in stats:
            if "High Score" in stat:
                color = GREEN if self.score >= self.high_score else WHITE
            else:
                color = WHITE
            
            text = self.font.render(stat, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50
        
        # Instructions
        restart_text = self.small_font.render("Press SPACE to Play Again", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = self.small_font.render("Press ESC for Main Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(menu_text, menu_rect)
    
    def draw(self):
        """Draw current state"""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "paused":
            self.draw_game()
            self.draw_pause()
        elif self.state == "game_over":
            self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()


    # Thanks For Playing! - @rnkbv
