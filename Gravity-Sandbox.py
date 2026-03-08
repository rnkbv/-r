from logging import info
import pygame
import math
import random
import sys
import json
import os

from pygame import key

# Initialize Pygame
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except:
    pass

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
G = 6.67430e-11
SCALE_G = 100

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
BLUE = (100, 149, 237)
CYAN = (0, 255, 255)
PURPLE = (147, 112, 219)
GREEN = (0, 255, 0)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
DARK_BLUE = (10, 10, 40)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
DARK_RED = (139, 0, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
SELECT_COLOR = (255, 255, 100)
GRID_COLOR = (40, 40, 80)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def blend_colors(c1, c2, weight=0.5):
    return tuple(int(c1[i] * (1 - weight) + c2[i] * weight) for i in range(3))

# ----------------------------------------------------------------------
# Particle class
# ----------------------------------------------------------------------
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.radius = random.randint(2, 4)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.98
        self.vy *= 0.98
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, screen, camera_x, camera_y, zoom):
        if self.lifetime <= 0:
            return
        screen_x = int((self.x - camera_x) * zoom + SCREEN_WIDTH / 2)
        screen_y = int((self.y - camera_y) * zoom + SCREEN_HEIGHT / 2)
        dark_factor = self.lifetime / self.max_lifetime
        draw_color = tuple(int(c * dark_factor) for c in self.color)
        pygame.draw.circle(screen, draw_color, (screen_x, screen_y), int(self.radius * zoom))

# ----------------------------------------------------------------------
# Star class
# ----------------------------------------------------------------------
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.2, 0.2)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.01, 0.08)
        self.twinkle_phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.twinkle_phase += self.twinkle_speed
        self.x += self.vx
        self.y += self.vy
        # wrap around screen edges
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT
        elif self.y > SCREEN_HEIGHT:
            self.y = 0

    def draw(self, screen):
        # 👇 THIS IS THE KEY: update the star EVERY time it is drawn
        self.update()

        twinkle = (math.sin(self.twinkle_phase) + 1) / 2
        brightness = int(self.brightness * (0.6 + 0.4 * twinkle))
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

# ----------------------------------------------------------------------
# CelestialBody class (enhanced)
# ----------------------------------------------------------------------
class CelestialBody:
    def __init__(self, x, y, mass, radius, color, vx=0, vy=0, body_type="planet", name=""):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.radius = radius
        self.color = color
        self.body_type = body_type
        self.name = name
        self.trail = []
        self.max_trail_length = 200
        self.to_remove = False
        self.glow_phase = random.uniform(0, math.pi * 2)
        self.selected = False

    def apply_force(self, fx, fy, dt):
        ax = fx / self.mass
        ay = fy / self.mass
        self.vx += ax * dt
        self.vy += ay * dt

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        self.glow_phase += 0.05

    def draw(self, screen, camera_x, camera_y, zoom, show_trails=True):
        # Trail
        if show_trails and len(self.trail) > 2:
            trail_points = []
            for i, (tx, ty) in enumerate(self.trail):
                screen_x = int((tx - camera_x) * zoom + SCREEN_WIDTH / 2)
                screen_y = int((ty - camera_y) * zoom + SCREEN_HEIGHT / 2)
                if -50 <= screen_x <= SCREEN_WIDTH + 50 and -50 <= screen_y <= SCREEN_HEIGHT + 50:
                    trail_points.append((screen_x, screen_y))
            if len(trail_points) > 1:
                for i in range(len(trail_points) - 1):
                    alpha = (i / len(trail_points)) * 0.5
                    col = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
                    if len(col) == 3:
                        pygame.draw.line(screen, col, trail_points[i], trail_points[i + 1], 2)

        # Screen position
        screen_x = int((self.x - camera_x) * zoom + SCREEN_WIDTH / 2)
        screen_y = int((self.y - camera_y) * zoom + SCREEN_HEIGHT / 2)
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100 or screen_y < -100 or screen_y > SCREEN_HEIGHT + 100:
            return

        draw_radius = max(3, int(self.radius * zoom))

        # Special effects
        if self.body_type == "star":
            glow_intensity = (math.sin(self.glow_phase) + 1) / 2
            for i in range(4, 0, -1):
                glow_radius = draw_radius + i * 4
                glow_alpha = (1 - i / 5) * glow_intensity * 0.7
                glow_color = tuple(min(255, int(c + (255 - c) * glow_alpha)) for c in self.color)
                pygame.draw.circle(screen, glow_color, (screen_x, screen_y), glow_radius)
        elif self.body_type == "black_hole":
            accretion_radius = draw_radius + int(8 * (1 + 0.3 * math.sin(self.glow_phase)))
            pygame.draw.circle(screen, (80, 0, 80), (screen_x, screen_y), accretion_radius)
            pygame.draw.circle(screen, (120, 0, 120), (screen_x, screen_y), accretion_radius - 2)
            pygame.draw.circle(screen, BLACK, (screen_x, screen_y), draw_radius)
            pygame.draw.circle(screen, (180, 0, 180), (screen_x, screen_y), draw_radius, 3)
        elif self.body_type == "white_hole":
    # Event horizon and accretion disk – white edition
            accretion_radius = draw_radius + int(8 * (1 + 0.3 * math.sin(self.glow_phase)))
            pygame.draw.circle(screen, (200, 200, 200), (screen_x, screen_y), accretion_radius)
            pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), accretion_radius - 2)
            pygame.draw.circle(screen, (220, 220, 220), (screen_x, screen_y), draw_radius)
            pygame.draw.circle(screen, WHITE, (screen_x, screen_y), draw_radius, 3)
            return  # prevents generic circle drawing
        elif self.body_type == "neutron_star":
            pulse = (math.sin(self.glow_phase * 3) + 1) / 2
            for i in range(3, 0, -1):
                glow_radius = draw_radius + i * 2
                glow_color = tuple(min(255, int(c * (0.5 + 0.5 * pulse))) for c in self.color)
                pygame.draw.circle(screen, glow_color, (screen_x, screen_y), glow_radius)
        elif self.body_type == "gas_giant":
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), draw_radius)
            band_color = tuple(max(0, c - 40) for c in self.color)
            for i in range(-2, 3):
                band_y = screen_y + i * (draw_radius // 3)
                pygame.draw.line(screen, band_color,
                               (screen_x - draw_radius, band_y),
                               (screen_x + draw_radius, band_y), 2)
            spot_color = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.circle(screen, spot_color,
                             (screen_x + draw_radius // 2, screen_y),
                             max(2, draw_radius // 4))
        else:
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), draw_radius)
            if draw_radius > 4:
                highlight_color = tuple(min(255, c + 100) for c in self.color)
                highlight_radius = max(2, draw_radius // 3)
                pygame.draw.circle(screen, highlight_color,
                                 (screen_x - draw_radius // 3, screen_y - draw_radius // 3),
                                 highlight_radius)

        # Selection highlight
        if self.selected:
            pygame.draw.circle(screen, SELECT_COLOR, (screen_x, screen_y), draw_radius + 4, 3)

        # Name label
        if draw_radius > 10 and self.name:
            font = pygame.font.Font(None, 18)
            name_text = font.render(self.name, True, WHITE)
            name_rect = name_text.get_rect(center=(screen_x, screen_y + draw_radius + 12))
            bg_rect = name_rect.inflate(8, 4)
            s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, bg_rect)
            screen.blit(name_text, name_rect)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.hypot(dx, dy)

    def is_colliding(self, other):
        return self.distance_to(other) < (self.radius + other.radius)

    def to_dict(self):
        return {
            "x": self.x, "y": self.y,
            "vx": self.vx, "vy": self.vy,
            "mass": self.mass, "radius": self.radius,
            "color": self.color, "body_type": self.body_type,
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["x"], data["y"],
            data["mass"], data["radius"],
            tuple(data["color"]),
            data["vx"], data["vy"],
            data["body_type"], data["name"]
        )

# ----------------------------------------------------------------------
# Button class
# ----------------------------------------------------------------------
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed

# ----------------------------------------------------------------------
# Main Simulation Class (complete)
# ----------------------------------------------------------------------
class GravitySimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gravity Sandbox - Ultimate Edition Enhanced")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)

        # Game state
        self.state = "menu"

        # Performance
        self.fps_history = []
        self.show_fps = False

        # Simulation state
        self.bodies = []
        self.particles = []
        self.paused = False
        self.show_trails = True
        self.time_scale = 1.0
        self.show_help = True
        self.show_info = True
        self.show_grid = False
        self.follow_mode = False
        self.prediction_mode = False
        self.prediction_points = []

        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.dragging_camera = False
        self.drag_start = (0, 0)

        # Body creation
        self.selected_type = "planet"
        self.body_types = {
            "planet": {"mass": 50, "radius": 15, "color": BLUE, "display": "Planet"},
            "star": {"mass": 200, "radius": 28, "color": YELLOW, "display": "Star"},
            "moon": {"mass": 10, "radius": 8, "color": GRAY, "display": "Moon"},
            "gas_giant": {"mass": 120, "radius": 22, "color": ORANGE, "display": "Gas Giant"},
            "black_hole": {"mass": 600, "radius": 22, "color": PURPLE, "display": "Black Hole"},
            "red_giant": {"mass": 180, "radius": 35, "color": RED, "display": "Red Giant"},
            "neutron_star": {"mass": 250, "radius": 12, "color": CYAN, "display": "Neutron Star"},
            "dwarf_planet": {"mass": 20, "radius": 10, "color": BROWN, "display": "Dwarf Planet"},
            "ice_giant": {"mass": 100, "radius": 20, "color": LIGHT_BLUE, "display": "Ice Giant"},
            "asteroid": {"mass": 5, "radius": 6, "color": GRAY, "display": "Asteroid"},
            "white_hole": {"mass": 600, "radius": 18, "color": WHITE, "display": "White Hole"}
        }

        # Velocity vector
        self.velocity_start = None
        self.velocity_end = None

        # Background stars
        self.stars = [Star() for _ in range(300)]

        # Selected body
        self.selected_body = None

        # Sound
        self.sound_enabled = False  # will be enabled only if mixer works
        self.collision_sound = None
        self.click_sound = None
        self.init_sound()

        # Spatial hash
        self.grid_cell_size = 100
        self.spatial_grid = {}

        # --- Presets must be defined after all methods are declared ---
        # We'll define all preset methods first, then the presets dictionary
        # (methods are defined below in the class body)
        self.presets = {}  # will be filled after method definitions
        self.setup_menu_buttons()

    # ------------------------------------------------------------------
    # Sound initialization (fixed)
    # ------------------------------------------------------------------
    def init_sound(self):
        try:
            pygame.mixer.init()
            self.sound_enabled = True
            self.collision_sound = self.create_beep(60, 0.2, 440)
            self.click_sound = self.create_beep(30, 0.05, 800)
        except:
            self.sound_enabled = False

    def create_beep(self, duration_ms, volume, frequency=440):
        """Generate a simple sine wave beep."""
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration_ms / 1000)
            # build array of sine samples
            buf = pygame.sndarray.make_sound(
                (volume * 32767 * 
                 [math.sin(2 * math.pi * frequency * t / sample_rate) 
                  for t in range(n_samples)]).astype('<i2')
            )
            return buf
        except:
            return None

    def play_sound(self, sound):
        if self.sound_enabled and sound:
            sound.play()

    # ------------------------------------------------------------------
    # Preset Scenarios (ALL original + new ones)
    # ------------------------------------------------------------------
    def create_solar_system(self):
        self.bodies.clear()
        sun = CelestialBody(0, 0, 300, 35, YELLOW, 0, 0, "star", "Sun")
        self.bodies.append(sun)
        def orbital_velocity(distance, central_mass):
            return math.sqrt(SCALE_G * central_mass / distance)
        # Mercury
        mercury_dist = 120
        mercury = CelestialBody(mercury_dist, 0, 15, 8, GRAY,
                                0, orbital_velocity(mercury_dist, sun.mass), "planet", "Mercury")
        self.bodies.append(mercury)
        # Venus
        venus_dist = 180
        venus = CelestialBody(venus_dist, 0, 25, 12, ORANGE,
                              0, orbital_velocity(venus_dist, sun.mass), "planet", "Venus")
        self.bodies.append(venus)
        # Earth
        earth_dist = 260
        earth = CelestialBody(earth_dist, 0, 30, 13, BLUE,
                              0, orbital_velocity(earth_dist, sun.mass), "planet", "Earth")
        self.bodies.append(earth)
        # Mars
        mars_dist = 350
        mars = CelestialBody(mars_dist, 0, 20, 10, RED,
                             0, orbital_velocity(mars_dist, sun.mass), "planet", "Mars")
        self.bodies.append(mars)
        # Jupiter
        jupiter_dist = 500
        jupiter = CelestialBody(jupiter_dist, 0, 100, 22, ORANGE,
                                0, orbital_velocity(jupiter_dist, sun.mass), "gas_giant", "Jupiter")
        self.bodies.append(jupiter)
        # Saturn
        saturn_dist = 650
        saturn = CelestialBody(saturn_dist, 0, 80, 20, GOLD,
                               0, orbital_velocity(saturn_dist, sun.mass), "gas_giant", "Saturn")
        self.bodies.append(saturn)
        # Uranus
        uranus_dist = 780
        uranus = CelestialBody(uranus_dist, 0, 60, 18, LIGHT_BLUE,
                               0, orbital_velocity(uranus_dist, sun.mass), "ice_giant", "Uranus")
        self.bodies.append(uranus)
        # Neptune
        neptune_dist = 900
        neptune = CelestialBody(neptune_dist, 0, 65, 18, BLUE,
                                0, orbital_velocity(neptune_dist, sun.mass), "ice_giant", "Neptune")
        self.bodies.append(neptune)

    def create_binary_stars(self):
        self.bodies.clear()
        separation = 250
        star_mass = 200
        orbital_speed = math.sqrt(SCALE_G * star_mass / separation)
        star1 = CelestialBody(-separation/2, 0, star_mass, 28, YELLOW, 0, orbital_speed, "star", "Star A")
        star2 = CelestialBody(separation/2, 0, star_mass, 28, ORANGE, 0, -orbital_speed, "star", "Star B")
        self.bodies.extend([star1, star2])
        total_mass = star_mass * 2
        planet1_dist = 450
        planet1_speed = math.sqrt(SCALE_G * total_mass / planet1_dist)
        planet1 = CelestialBody(0, planet1_dist, 35, 14, BLUE, planet1_speed, 0, "planet", "Planet I")
        self.bodies.append(planet1)
        planet2_dist = 450
        planet2_speed = math.sqrt(SCALE_G * total_mass / planet2_dist)
        planet2 = CelestialBody(0, -planet2_dist, 35, 14, GREEN, -planet2_speed, 0, "planet", "Planet II")
        self.bodies.append(planet2)
        planet3_dist = 600
        planet3_speed = math.sqrt(SCALE_G * total_mass / planet3_dist)
        planet3 = CelestialBody(planet3_dist, 0, 30, 13, PURPLE, 0, planet3_speed, "planet", "Planet III")
        self.bodies.append(planet3)

    def create_galaxy(self):
        self.bodies.clear()
        center = CelestialBody(0, 0, 500, 20, PURPLE, 0, 0, "black_hole", "Core")
        self.bodies.append(center)
        num_arms = 3
        bodies_per_arm = 15
        for arm in range(num_arms):
            arm_offset = (arm / num_arms) * 2 * math.pi
            for i in range(bodies_per_arm):
                distance = 120 + i * 25
                angle = arm_offset + (i / bodies_per_arm) * 3 * math.pi
                x = distance * math.cos(angle)
                y = distance * math.sin(angle)
                speed = math.sqrt(SCALE_G * center.mass / distance) * 0.9
                speed *= random.uniform(0.85, 1.15)
                vx = -speed * math.sin(angle)
                vy = speed * math.cos(angle)
                if random.random() < 0.2:
                    body = CelestialBody(x, y, 150, 24, random.choice([YELLOW, ORANGE, RED]),
                                         vx, vy, "star", f"Star-{arm}-{i}")
                else:
                    body = CelestialBody(x, y, 25, 11, random.choice([BLUE, GREEN, CYAN, PURPLE, PINK]),
                                         vx, vy, "planet", f"P-{arm}-{i}")
                self.bodies.append(body)

    def create_chaos(self):
        self.bodies.clear()
        num_attractors = 3
        for i in range(num_attractors):
            angle = (i / num_attractors) * 2 * math.pi
            distance = 300
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            speed = 3
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            body_type = random.choice(["star", "black_hole", "red_giant"])
            info = self.body_types[body_type]
            body = CelestialBody(x, y, info["mass"], info["radius"],
                                 info["color"], vx, vy, body_type, f"Attractor-{i}")
            self.bodies.append(body)
        num_bodies = 35
        for i in range(num_bodies):
            x = random.randint(-500, 500)
            y = random.randint(-400, 400)
            vx = random.uniform(-8, 8)
            vy = random.uniform(-8, 8)
            body_type = random.choice([
                "planet", "planet", "planet",
                "moon", "moon",
                "asteroid", "asteroid", "asteroid",
                "dwarf_planet",
                "gas_giant",
                "ice_giant"
            ])
            info = self.body_types[body_type]
            if body_type == "planet":
                color = random.choice([BLUE, GREEN, RED, PURPLE, ORANGE, CYAN, PINK])
            else:
                color = info["color"]
            body = CelestialBody(x, y, info["mass"], info["radius"],
                                 color, vx, vy, body_type)
            self.bodies.append(body)

    def create_planet_moons(self):
        self.bodies.clear()
        planet = CelestialBody(0, 0, 180, 28, ORANGE, 0, 0, "gas_giant", "Giant")
        self.bodies.append(planet)
        moon_data = [
            (100, GRAY, "Moon-I"),
            (150, WHITE, "Moon-II"),
            (210, CYAN, "Moon-III"),
            (280, PINK, "Moon-IV"),
            (360, LIGHT_BLUE, "Moon-V"),
            (450, SILVER, "Moon-VI")
        ]
        for i, (dist, color, name) in enumerate(moon_data):
            angle = (i / len(moon_data)) * 2 * math.pi
            x = dist * math.cos(angle)
            y = dist * math.sin(angle)
            speed = math.sqrt(SCALE_G * planet.mass / dist)
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            moon_size = 8 + (i % 3) * 2
            moon = CelestialBody(x, y, 15, moon_size, color,
                                 vx, vy, "moon", name)
            self.bodies.append(moon)

    def create_star_cluster(self):
        self.bodies.clear()
        central_star = CelestialBody(0, 0, 400, 32, YELLOW, 0, 0, "star", "Core Star")
        self.bodies.append(central_star)
        num_objects = 20
        for i in range(num_objects):
            distance = random.randint(200, 700)
            angle = random.uniform(0, 2 * math.pi)
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            base_speed = math.sqrt(SCALE_G * central_star.mass / distance)
            speed = base_speed * random.uniform(0.7, 1.3)
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            rand = random.random()
            if rand < 0.3:
                star_type = random.choice(["star", "red_giant", "neutron_star"])
                info = self.body_types[star_type]
                body = CelestialBody(x, y, info["mass"], info["radius"],
                                     info["color"], vx, vy, star_type, f"Star-{i}")
            elif rand < 0.6:
                info = self.body_types["gas_giant"]
                body = CelestialBody(x, y, info["mass"], info["radius"],
                                     random.choice([ORANGE, BROWN, PINK]), vx, vy, "gas_giant", f"Giant-{i}")
            else:
                info = self.body_types["planet"]
                body = CelestialBody(x, y, info["mass"], info["radius"],
                                     random.choice([BLUE, GREEN, RED, PURPLE]), vx, vy, "planet", f"Planet-{i}")
            self.bodies.append(body)

    def create_triple_stars(self):
        self.bodies.clear()
        distance = 200
        star_mass = 180
        angles = [0, 2*math.pi/3, 4*math.pi/3]
        colors = [YELLOW, ORANGE, RED]
        names = ["Star Alpha", "Star Beta", "Star Gamma"]
        for i, (angle, color, name) in enumerate(zip(angles, colors, names)):
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            speed = math.sqrt(SCALE_G * star_mass / distance) * 0.8
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            star = CelestialBody(x, y, star_mass, 26, color, vx, vy, "star", name)
            self.bodies.append(star)
        total_mass = star_mass * 3
        planet1_dist = 450
        planet1_angle = math.pi / 4
        planet1_speed = math.sqrt(SCALE_G * total_mass / planet1_dist)
        planet1 = CelestialBody(
            planet1_dist * math.cos(planet1_angle),
            planet1_dist * math.sin(planet1_angle),
            30, 13, BLUE,
            -planet1_speed * math.sin(planet1_angle),
            planet1_speed * math.cos(planet1_angle),
            "planet", "Planet I"
        )
        self.bodies.append(planet1)
        planet2_dist = 600
        planet2_angle = math.pi
        planet2_speed = math.sqrt(SCALE_G * total_mass / planet2_dist)
        planet2 = CelestialBody(
            planet2_dist * math.cos(planet2_angle),
            planet2_dist * math.sin(planet2_angle),
            35, 14, GREEN,
            -planet2_speed * math.sin(planet2_angle),
            planet2_speed * math.cos(planet2_angle),
            "planet", "Planet II"
        )
        self.bodies.append(planet2)

    def create_asteroid_belt(self):
        self.bodies.clear()
        star = CelestialBody(0, 0, 280, 32, YELLOW, 0, 0, "star", "Sun")
        self.bodies.append(star)
        inner_dist = 150
        inner_speed = math.sqrt(SCALE_G * star.mass / inner_dist)
        inner_planet = CelestialBody(inner_dist, 0, 40, 15, BLUE,
                                     0, inner_speed, "planet", "Inner World")
        self.bodies.append(inner_planet)
        num_asteroids = 60
        for i in range(num_asteroids):
            distance = random.uniform(280, 450)
            angle = random.uniform(0, 2 * math.pi)
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            speed = math.sqrt(SCALE_G * star.mass / distance) * random.uniform(0.95, 1.05)
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            if random.random() < 0.85:
                body_type = "asteroid"
                size = random.randint(4, 7)
                mass = 5
            else:
                body_type = "dwarf_planet"
                size = random.randint(8, 11)
                mass = 20
            color = random.choice([GRAY, BROWN, (150,150,150), (100,100,100)])
            asteroid = CelestialBody(x, y, mass, size, color, vx, vy, body_type, f"A-{i}")
            self.bodies.append(asteroid)
        outer_dist = 650
        outer_speed = math.sqrt(SCALE_G * star.mass / outer_dist)
        outer_giant = CelestialBody(outer_dist, 0, 120, 24, ORANGE,
                                    0, outer_speed, "gas_giant", "Outer Giant")
        self.bodies.append(outer_giant)
        for i in range(3):
            angle = (i / 3) * 2 * math.pi
            moon_dist = 60 + i * 25
            moon_x = outer_dist + moon_dist * math.cos(angle)
            moon_y = moon_dist * math.sin(angle)
            relative_speed = math.sqrt(SCALE_G * outer_giant.mass / moon_dist)
            moon_vx = -relative_speed * math.sin(angle)
            moon_vy = outer_speed + relative_speed * math.cos(angle)
            moon = CelestialBody(moon_x, moon_y, 12, 7, GRAY,
                                 moon_vx, moon_vy, "moon", f"Moon-{i+1}")
            self.bodies.append(moon)

    # NEW presets
    def create_earth_moon(self):
        self.bodies.clear()
        earth = CelestialBody(0, 0, 100, 18, BLUE, 0, 0, "planet", "Earth")
        moon = CelestialBody(200, 0, 5, 6, GRAY, 0, math.sqrt(SCALE_G * earth.mass / 200), "moon", "Moon")
        self.bodies.extend([earth, moon])
        self.zoom = 1.2

    def create_comet(self):
        self.bodies.clear()
        sun = CelestialBody(0, 0, 300, 32, YELLOW, 0, 0, "star", "Sun")
        comet = CelestialBody(800, 0, 10, 8, CYAN, 0, -12, "asteroid", "Comet Halley")
        self.bodies.extend([sun, comet])
        self.zoom = 0.9

    def create_collision(self):
        self.bodies.clear()
        star1 = CelestialBody(-250, 0, 200, 28, ORANGE, 2, 1, "star", "Star A")
        star2 = CelestialBody(250, 0, 200, 28, RED, -2, -1, "star", "Star B")
        self.bodies.extend([star1, star2])
        self.zoom = 1.0

    def create_random(self):
        self.bodies.clear()
        for _ in range(30):
            x = random.randint(-500, 500)
            y = random.randint(-400, 400)
            vx = random.uniform(-5, 5)
            vy = random.uniform(-5, 5)
            body_type = random.choice(["planet", "asteroid", "star", "gas_giant"])
            info = self.body_types[body_type]
            color = info["color"] if body_type != "planet" else random.choice([BLUE, GREEN, RED, PURPLE])
            body = CelestialBody(x, y, info["mass"], info["radius"], color, vx, vy, body_type)
            self.bodies.append(body)

    def create_double_planet(self):
        self.bodies.clear()
        mass = 80
        dist = 300
        speed = math.sqrt(SCALE_G * mass / dist) * 0.7
        planet1 = CelestialBody(-dist/2, 0, mass, 20, BLUE, 0, -speed, "planet", "Themis")
        planet2 = CelestialBody(dist/2, 0, mass, 20, GREEN, 0, speed, "planet", "Dione")
        self.bodies.extend([planet1, planet2])
        self.zoom = 1.0

    def create_ring_world(self):
        self.bodies.clear()
        giant = CelestialBody(0, 0, 200, 30, ORANGE, 0, 0, "gas_giant", "Ring Giant")
        self.bodies.append(giant)
        for i in range(80):
            dist = random.uniform(150, 220)
            angle = random.uniform(0, 2 * math.pi)
            x = dist * math.cos(angle)
            y = dist * math.sin(angle)
            speed = math.sqrt(SCALE_G * giant.mass / dist) * random.uniform(0.95, 1.05)
            vx = -speed * math.sin(angle)
            vy = speed * math.cos(angle)
            asteroid = CelestialBody(x, y, 5, 4, GRAY, vx, vy, "asteroid")
            self.bodies.append(asteroid)

    # ------------------------------------------------------------------
    # Menu setup (must be called after presets are defined)
    # ------------------------------------------------------------------
    def setup_menu_buttons(self):
        # Now define presets dictionary with all methods
        self.presets = {
            "Solar System": self.create_solar_system,
            "Binary Stars": self.create_binary_stars,
            "Triple Stars": self.create_triple_stars,
            "Galaxy Spiral": self.create_galaxy,
            "Asteroid Belt": self.create_asteroid_belt,
            "Planet & Moons": self.create_planet_moons,
            "Star Cluster": self.create_star_cluster,
            "Chaos": self.create_chaos,
            "Earth & Moon": self.create_earth_moon,
            "Comet": self.create_comet,
            "Collision Course": self.create_collision,
            "Random": self.create_random,
            "Double Planet": self.create_double_planet,
            "Ring World": self.create_ring_world,
        }

        button_width = 300
        button_height = 60
        spacing = 20
        start_y = 300
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        self.menu_buttons = [
            Button(center_x, start_y, button_width, button_height,
                   "Free Sandbox", DARK_BLUE, BLUE),
            Button(center_x, start_y + (button_height + spacing), button_width, button_height,
                   "Preset Scenarios", DARK_BLUE, BLUE),
            Button(center_x, start_y + 2 * (button_height + spacing), button_width, button_height,
                   "Quit", DARK_RED, RED)
        ]

        # Preset menu buttons – 2 columns
        self.preset_buttons = []
        button_width = 350
        button_height = 70
        spacing_x = 30
        spacing_y = 20
        start_x = SCREEN_WIDTH // 2 - button_width - spacing_x // 2
        start_y = 180

        for i, preset_name in enumerate(self.presets.keys()):
            col = i % 2
            row = i // 2
            x = start_x + col * (button_width + spacing_x)
            y = start_y + row * (button_height + spacing_y)
            self.preset_buttons.append(
                Button(x, y, button_width, button_height, preset_name, DARK_BLUE, BLUE)
            )

        self.back_button = Button(50, SCREEN_HEIGHT - 80, 150, 50, "Back", DARK_RED, RED)

    # ------------------------------------------------------------------
    # Body creation & selection
    # ------------------------------------------------------------------
    def get_body_at_pos(self, screen_x, screen_y):
        world_x = (screen_x - SCREEN_WIDTH / 2) / self.zoom + self.camera_x
        world_y = (screen_y - SCREEN_HEIGHT / 2) / self.zoom + self.camera_y
        for body in reversed(self.bodies):
            dist = math.hypot(body.x - world_x, body.y - world_y)
            if dist <= body.radius:
                return body
        return None

    def select_body(self, body):
        if self.selected_body:
            self.selected_body.selected = False
        self.selected_body = body
        if body:
            body.selected = True
            if self.follow_mode:
                self.camera_x = body.x
                self.camera_y = body.y

    def delete_selected_body(self):
        if self.selected_body and self.selected_body in self.bodies:
            self.bodies.remove(self.selected_body)
            self.select_body(None)

    def create_body(self, x, y, vx=0, vy=0):
        world_x = (x - SCREEN_WIDTH / 2) / self.zoom + self.camera_x
        world_y = (y - SCREEN_HEIGHT / 2) / self.zoom + self.camera_y
        info = self.body_types[self.selected_type]
        body = CelestialBody(
            world_x, world_y,
            info["mass"],
            info["radius"],
            info["color"],
            vx, vy,
            self.selected_type
        )
        self.bodies.append(body)
        self.play_sound(self.click_sound)

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------
    def build_spatial_grid(self):
        self.spatial_grid.clear()
        for body in self.bodies:
            cell_x = int(body.x // self.grid_cell_size)
            cell_y = int(body.y // self.grid_cell_size)
            key = (cell_x, cell_y)
            if key not in self.spatial_grid:
                self.spatial_grid[key] = []
            self.spatial_grid[key].append(body)

    def calculate_gravitational_force(self, body1, body2):
        dx = body2.x - body1.x
        dy = body2.y - body1.y
        distance = math.hypot(dx, dy)
        if distance < 1:
            return 0, 0

        force = (SCALE_G * body1.mass * body2.mass) / (distance * distance)

        # Base force direction (body1 -> body2)
        fx = force * dx / distance
        fy = force * dy / distance

        # REPULSION if either body is a white hole
        if body1.body_type == "white_hole" or body2.body_type == "white_hole":
            fx = -fx
            fy = -fy

        return fx, fy

    def update_physics(self, dt):
        if self.paused or self.state != "simulation":
            return
        dt *= self.time_scale

        # Gravity forces
        for i, body1 in enumerate(self.bodies):
            fx = fy = 0
            for j, body2 in enumerate(self.bodies):
                if i != j:
                    fxi, fyi = self.calculate_gravitational_force(body1, body2)
                    fx += fxi
                    fy += fyi
            body1.apply_force(fx, fy, dt)

        # Update positions
        for body in self.bodies:
            body.update(dt)

        # Update particles
        for p in self.particles[:]:
            if not p.update(dt):
                self.particles.remove(p)

        # Collisions
        self.build_spatial_grid()
        self.handle_collisions()

        # Prediction
        if self.prediction_mode and self.selected_body:
            self.update_prediction()

        # Follow mode
        if self.follow_mode and self.selected_body:
            self.camera_x = self.selected_body.x
            self.camera_y = self.selected_body.y

    def handle_collisions(self):
        to_remove = set()
        to_add = []
        checked_pairs = set()
        for key, cell_bodies in self.spatial_grid.items():
            for body1 in cell_bodies:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        neighbour_key = (key[0] + dx, key[1] + dy)
                        if neighbour_key in self.spatial_grid:
                            for body2 in self.spatial_grid[neighbour_key]:
                                if body1 == body2:
                                    continue
                                pair_id = id(body1) ^ id(body2)
                                if pair_id in checked_pairs:
                                    continue
                                checked_pairs.add(pair_id)
                                if body1.is_colliding(body2) and body1 not in to_remove and body2 not in to_remove:
                                    self.generate_particles(body1.x, body1.y, body1.color, body2.color)
                                    self.play_sound(self.collision_sound)

                                    total_mass = body1.mass + body2.mass
                                    new_x = (body1.x * body1.mass + body2.x * body2.mass) / total_mass
                                    new_y = (body1.y * body1.mass + body2.y * body2.mass) / total_mass
                                    new_vx = (body1.vx * body1.mass + body2.vx * body2.mass) / total_mass
                                    new_vy = (body1.vy * body1.mass + body2.vy * body2.mass) / total_mass
                                    new_radius = math.sqrt(body1.radius**2 + body2.radius**2)
                                    new_color = blend_colors(body1.color, body2.color, 0.5)
                                    new_type = body1.body_type if body1.mass > body2.mass else body2.body_type
                                    new_name = body1.name if body1.mass > body2.mass else body2.name

                                    merged = CelestialBody(
                                        new_x, new_y, total_mass, new_radius, new_color,
                                        new_vx, new_vy, new_type, new_name
                                    )
                                    to_add.append(merged)
                                    to_remove.add(body1)
                                    to_remove.add(body2)

        for body in to_remove:
            if body in self.bodies:
                self.bodies.remove(body)
            if self.selected_body == body:
                self.select_body(None)

        self.bodies.extend(to_add)

    def generate_particles(self, x, y, color1, color2, count=20):
        for _ in range(count):
            vx = random.uniform(-15, 15)
            vy = random.uniform(-15, 15)
            col = blend_colors(color1, color2, random.random())
            self.particles.append(Particle(x, y, vx, vy, col, random.uniform(0.5, 1.5)))

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def update_prediction(self):
        if not self.selected_body:
            self.prediction_points = []
            return
        sim_body = self.selected_body
        px, py = sim_body.x, sim_body.y
        pvx, pvy = sim_body.vx, sim_body.vy
        steps = 50
        dt = 0.1
        points = []
        other_bodies = [b for b in self.bodies if b != sim_body]

        for _ in range(steps):
            fx = fy = 0
            for ob in other_bodies:
                dx = ob.x - px
                dy = ob.y - py
                dist = math.hypot(dx, dy)
                if dist < 1:
                    continue
                force = (SCALE_G * sim_body.mass * ob.mass) / (dist * dist)
                fx += force * dx / dist
                fy += force * dy / dist
            ax = fx / sim_body.mass
            ay = fy / sim_body.mass
            pvx += ax * dt
            pvy += ay * dt
            px += pvx * dt
            py += pvy * dt
            points.append((px, py))

        self.prediction_points = points

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------
    def save_simulation(self, filename="simulation_save.json"):
        data = [b.to_dict() for b in self.bodies]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(self.bodies)} bodies to {filename}")

    def load_simulation(self, filename="simulation_save.json"):
        if not os.path.exists(filename):
            return
        with open(filename, "r") as f:
            data = json.load(f)
        self.bodies = [CelestialBody.from_dict(d) for d in data]
        self.select_body(None)
        print(f"Loaded {len(self.bodies)} bodies from {filename}")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_grid(self):
        if not self.show_grid:
            return
        spacing = 100 / self.zoom
        if spacing < 20:
            spacing = 20
        elif spacing < 50:
            spacing = 50
        elif spacing < 100:
            spacing = 100
        elif spacing < 200:
            spacing = 200
        else:
            spacing = 500

        first_x = (self.camera_x - (SCREEN_WIDTH / 2) / self.zoom) // spacing * spacing
        for x in range(int(first_x), int(first_x + SCREEN_WIDTH / self.zoom + spacing), int(spacing)):
            screen_x = int((x - self.camera_x) * self.zoom + SCREEN_WIDTH / 2)
            pygame.draw.line(self.screen, GRID_COLOR, (screen_x, 0), (screen_x, SCREEN_HEIGHT), 1)

        first_y = (self.camera_y - (SCREEN_HEIGHT / 2) / self.zoom) // spacing * spacing
        for y in range(int(first_y), int(first_y + SCREEN_HEIGHT / self.zoom + spacing), int(spacing)):
            screen_y = int((y - self.camera_y) * self.zoom + SCREEN_HEIGHT / 2)
            pygame.draw.line(self.screen, GRID_COLOR, (0, screen_y), (SCREEN_WIDTH, screen_y), 1)

    def draw_prediction(self):
        if not self.prediction_mode or not self.selected_body or not self.prediction_points:
            return
        points = []
        for px, py in self.prediction_points:
            sx = int((px - self.camera_x) * self.zoom + SCREEN_WIDTH / 2)
            sy = int((py - self.camera_y) * self.zoom + SCREEN_HEIGHT / 2)
            if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
                points.append((sx, sy))
        if len(points) > 1:
            pygame.draw.lines(self.screen, CYAN, False, points, 2)

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.screen, self.camera_x, self.camera_y, self.zoom)

    def draw_selected_info(self):
        if self.selected_body and self.show_info:
            body = self.selected_body
            panel_x = SCREEN_WIDTH - 320
            panel_y = 10
            panel_w = 300
            panel_h = 160
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 200))
            self.screen.blit(panel, (panel_x, panel_y))

            y = panel_y + 15
            x = panel_x + 15
            title = self.small_font.render(f"Selected: {body.name or 'Unnamed'}", True, SELECT_COLOR)
            self.screen.blit(title, (x, y))
            y += 25
            mass_txt = self.tiny_font.render(f"Mass: {body.mass:.1f}", True, WHITE)
            self.screen.blit(mass_txt, (x, y))
            y += 20
            vel = math.hypot(body.vx, body.vy)
            vel_txt = self.tiny_font.render(f"Velocity: {vel:.2f}  dx={body.vx:.2f} dy={body.vy:.2f}", True, WHITE)
            self.screen.blit(vel_txt, (x, y))
            y += 20
            dist_center = math.hypot(body.x, body.y)
            dist_txt = self.tiny_font.render(f"Dist from origin: {dist_center:.1f}", True, WHITE)
            self.screen.blit(dist_txt, (x, y))
            y += 25
            type_txt = self.tiny_font.render(f"Type: {body.body_type}", True, body.color)
            self.screen.blit(type_txt, (x, y))

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Menu state
            if self.state == "menu":
                for button in self.menu_buttons:
                    button.update(mouse_pos)
                    if event.type == pygame.MOUSEBUTTONDOWN and button.is_clicked(mouse_pos, True):
                        if button.text == "Free Sandbox":
                            self.state = "simulation"
                            self.bodies.clear()
                            self.select_body(None)
                        elif button.text == "Preset Scenarios":
                            self.state = "preset_menu"
                        elif button.text == "Quit":
                            return False

            # Preset menu state
            elif self.state == "preset_menu":
                self.back_button.update(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and self.back_button.is_clicked(mouse_pos, True):
                    self.state = "menu"

                for button in self.preset_buttons:
                    button.update(mouse_pos)
                    if event.type == pygame.MOUSEBUTTONDOWN and button.is_clicked(mouse_pos, True):
                        preset_func = self.presets[button.text]
                        preset_func()
                        self.state = "simulation"
                        self.camera_x = 0
                        self.camera_y = 0
                        self.select_body(None)
                        self.zoom = 1.0

            # Simulation state
            elif self.state == "simulation":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_t:
                        self.show_trails = not self.show_trails
                    elif event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_i:
                        self.show_info = not self.show_info
                    elif event.key == pygame.K_f and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.show_fps = not self.show_fps
                    elif event.key == pygame.K_c:
                        self.bodies.clear()
                        self.select_body(None)
                        self.prediction_points = []
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        self.time_scale = min(20.0, self.time_scale + 0.5)
                    elif event.key == pygame.K_MINUS:
                        self.time_scale = max(0.1, self.time_scale - 0.5)
                    elif event.key == pygame.K_r:
                        self.camera_x = 0
                        self.camera_y = 0
                        self.zoom = 1.0
                    # Body type selection
                    elif event.key == pygame.K_1:
                        self.selected_type = "planet"
                    elif event.key == pygame.K_2:
                        self.selected_type = "star"
                    elif event.key == pygame.K_3:
                        self.selected_type = "moon"
                    elif event.key == pygame.K_4:
                        self.selected_type = "gas_giant"
                    elif event.key == pygame.K_5:
                        self.selected_type = "black_hole"
                    elif event.key == pygame.K_6:
                        self.selected_type = "red_giant"
                    elif event.key == pygame.K_7:
                        self.selected_type = "neutron_star"
                    elif event.key == pygame.K_8:
                        self.selected_type = "dwarf_planet"
                    elif event.key == pygame.K_9:
                        self.selected_type = "ice_giant"
                    elif event.key == pygame.K_0:
                        self.selected_type = "asteroid"
                    elif event.key == pygame.K_x:
                        self.selected_type = "white_hole"
                    # NEW controls
                    elif event.key == pygame.K_DELETE:
                        self.delete_selected_body()
                    elif event.key == pygame.K_f and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.follow_mode = not self.follow_mode
                    elif event.key == pygame.K_p:
                        self.prediction_mode = not self.prediction_mode
                        if not self.prediction_mode:
                            self.prediction_points = []
                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    elif event.key == pygame.K_s:
                        self.save_simulation()
                    elif event.key == pygame.K_l:
                        self.load_simulation()
                    elif event.key == pygame.K_m:
                        self.sound_enabled = not self.sound_enabled
                    elif event.key == pygame.K_q:
                        self.sound_enabled = not self.sound_enabled
                        if self.sound_enabled:
                            self.init_sound()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.select_body(None)

                # Mouse events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        clicked_body = self.get_body_at_pos(event.pos[0], event.pos[1])
                        if clicked_body:
                            self.select_body(clicked_body)
                            self.velocity_start = None
                        else:
                            self.velocity_start = event.pos
                            self.velocity_end = event.pos
                    elif event.button == 2:  # Middle click
                        self.dragging_camera = True
                        self.drag_start = event.pos
                    elif event.button == 3:  # Right click
                        self.create_body(event.pos[0], event.pos[1])
                    elif event.button == 4:  # Wheel up
                        old_zoom = self.zoom
                        self.zoom = min(5.0, self.zoom * 1.1)
                        world_x_before = (event.pos[0] - SCREEN_WIDTH/2) / old_zoom + self.camera_x
                        world_y_before = (event.pos[1] - SCREEN_HEIGHT/2) / old_zoom + self.camera_y
                        self.camera_x = world_x_before - (event.pos[0] - SCREEN_WIDTH/2) / self.zoom
                        self.camera_y = world_y_before - (event.pos[1] - SCREEN_HEIGHT/2) / self.zoom
                    elif event.button == 5:  # Wheel down
                        old_zoom = self.zoom
                        self.zoom = max(0.1, self.zoom / 1.1)
                        world_x_before = (event.pos[0] - SCREEN_WIDTH/2) / old_zoom + self.camera_x
                        world_y_before = (event.pos[1] - SCREEN_HEIGHT/2) / old_zoom + self.camera_y
                        self.camera_x = world_x_before - (event.pos[0] - SCREEN_WIDTH/2) / self.zoom
                        self.camera_y = world_y_before - (event.pos[1] - SCREEN_HEIGHT/2) / self.zoom

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.velocity_start:
                        self.velocity_end = event.pos
                        dx = (self.velocity_end[0] - self.velocity_start[0]) / 10
                        dy = (self.velocity_end[1] - self.velocity_start[1]) / 10
                        self.create_body(self.velocity_start[0], self.velocity_start[1], dx, dy)
                        self.velocity_start = None
                        self.velocity_end = None
                    elif event.button == 2:
                        self.dragging_camera = False

                if event.type == pygame.MOUSEMOTION:
                    if self.velocity_start and event.buttons[0]:
                        self.velocity_end = event.pos
                    if self.dragging_camera:
                        dx = event.pos[0] - self.drag_start[0]
                        dy = event.pos[1] - self.drag_start[1]
                        self.camera_x -= dx / self.zoom
                        self.camera_y -= dy / self.zoom
                        self.drag_start = event.pos

        return True

    # ------------------------------------------------------------------
    # UI drawing (menu, simulation)
    # ------------------------------------------------------------------
    def draw_menu(self):
        self.screen.fill(DARK_BLUE)
        for star in self.stars:
            star.update()
            star.draw(self.screen)

        title = self.title_font.render("GRAVITY SANDBOX", True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        for offset in range(5, 0, -1):
            glow_color = tuple(c // (offset + 1) for c in CYAN)
            for dx, dy in ((offset, offset), (-offset, offset), (offset, -offset), (-offset, -offset)):
                glow = self.title_font.render("GRAVITY SANDBOX", True, glow_color)
                glow_rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + dx, 120 + dy))
                self.screen.blit(glow, glow_rect)
        self.screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render("Ultimate Edition Enhanced", True, GOLD)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(subtitle, subtitle_rect)

        for button in self.menu_buttons:
            button.draw(self.screen, self.font)

        credits = self.small_font.render("Create, Explore, Destroy – Gravitational Physics", True, WHITE)
        credits_rect = credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(credits, credits_rect)

    def draw_preset_menu(self):
        self.screen.fill(DARK_BLUE)
        for star in self.stars:
            star.update()
            star.draw(self.screen)

        title = self.subtitle_font.render("Choose a Scenario", True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        desc = self.small_font.render("Select a preset to start exploring!", True, WHITE)
        desc_rect = desc.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(desc, desc_rect)

        for button in self.preset_buttons:
            button.draw(self.screen, self.font)

        self.back_button.draw(self.screen, self.font)

    def draw_simulation(self):
        self.screen.fill(DARK_BLUE)
        for star in self.stars:
            star.draw(self.screen)

        self.draw_grid()

        for body in self.bodies:
            body.draw(self.screen, self.camera_x, self.camera_y, self.zoom, self.show_trails)

        self.draw_particles()
        self.draw_prediction()

        # Velocity vector
        if self.velocity_start and self.velocity_end:
            pygame.draw.line(self.screen, GREEN, self.velocity_start, self.velocity_end, 3)
            pygame.draw.circle(self.screen, GREEN, self.velocity_end, 6)
            dx = self.velocity_end[0] - self.velocity_start[0]
            dy = self.velocity_end[1] - self.velocity_start[1]
            length = math.hypot(dx, dy)
            if length > 0:
                angle = math.atan2(dy, dx)
                arrow_size = 15
                arrow_angle = math.pi / 6
                ax1 = self.velocity_end[0] - arrow_size * math.cos(angle - arrow_angle)
                ay1 = self.velocity_end[1] - arrow_size * math.sin(angle - arrow_angle)
                ax2 = self.velocity_end[0] - arrow_size * math.cos(angle + arrow_angle)
                ay2 = self.velocity_end[1] - arrow_size * math.sin(angle + arrow_angle)
                pygame.draw.line(self.screen, GREEN, self.velocity_end, (ax1, ay1), 3)
                pygame.draw.line(self.screen, GREEN, self.velocity_end, (ax2, ay2), 3)
            speed = length / 10
            speed_text = self.tiny_font.render(f"Speed: {speed:.1f}", True, GREEN)
            self.screen.blit(speed_text, (self.velocity_end[0] + 15, self.velocity_end[1] - 10))

        self.draw_ui()
        self.draw_selected_info()

        # Status bar
        status_y = SCREEN_HEIGHT - 25
        status_bg = pygame.Surface((SCREEN_WIDTH, 25), pygame.SRCALPHA)
        status_bg.fill((0, 0, 0, 200))
        self.screen.blit(status_bg, (0, status_y))
        status_text = f"Bodies: {len(self.bodies)} | Zoom: {self.zoom:.2f} | Time: {self.time_scale:.1f}x | "
        status_text += "Follow" if self.follow_mode else "      "
        status_text += " | Pred" if self.prediction_mode else "      "
        status_text += " | Grid" if self.show_grid else "      "
        status_text += " | Sound ON" if self.sound_enabled else " | Sound OFF"
        status_surface = self.tiny_font.render(status_text, True, WHITE)
        self.screen.blit(status_surface, (10, status_y + 5))

    def draw_ui(self):
        # Info panel
        if self.show_info:
            panel_width = 320
            panel_height = 280
            panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 200))
            self.screen.blit(panel, (10, 10))

            y_offset = 20
            x_offset = 20

            title = self.font.render("GRAVITY SANDBOX", True, CYAN)
            self.screen.blit(title, (x_offset, y_offset))
            y_offset += 35

            info = self.small_font.render(f"Bodies: {len(self.bodies)}", True, WHITE)
            self.screen.blit(info, (x_offset, y_offset))
            y_offset += 25

            status = "PAUSED" if self.paused else "RUNNING"
            status_color = ORANGE if self.paused else GREEN
            status_text = self.small_font.render(f"Status: {status}", True, status_color)
            self.screen.blit(status_text, (x_offset, y_offset))
            y_offset += 25

            time_text = self.small_font.render(f"Time Scale: {self.time_scale:.1f}x", True, WHITE)
            self.screen.blit(time_text, (x_offset, y_offset))
            y_offset += 25

            zoom_text = self.small_font.render(f"Zoom: {self.zoom:.2f}x", True, WHITE)
            self.screen.blit(zoom_text, (x_offset, y_offset))
            y_offset += 25

            cam_text = self.tiny_font.render(f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})", True, GRAY)
            self.screen.blit(cam_text, (x_offset, y_offset))
            y_offset += 30

            type_display = self.body_types[self.selected_type]["display"]
            type_color = self.body_types[self.selected_type]["color"]
            selected_text = self.small_font.render(f"Selected:", True, WHITE)
            self.screen.blit(selected_text, (x_offset, y_offset))
            pygame.draw.circle(self.screen, type_color, (x_offset + 100, y_offset + 10), 8)
            type_name = self.small_font.render(type_display, True, type_color)
            self.screen.blit(type_name, (x_offset + 115, y_offset))
            y_offset += 35

            selector_text = self.tiny_font.render("Press 1-0 to select type", True, GRAY)
            self.screen.blit(selector_text, (x_offset, y_offset))

        # Body type selector
        selector_y = SCREEN_HEIGHT - 120
        selector_x = 20
        selector_bg = pygame.Surface((SCREEN_WIDTH - 40, 100), pygame.SRCALPHA)
        selector_bg.fill((0, 0, 0, 200))
        self.screen.blit(selector_bg, (20, selector_y))

        selector_title = self.tiny_font.render("BODY TYPES (1-0):", True, CYAN)
        self.screen.blit(selector_title, (selector_x + 10, selector_y + 5))

        option_y = selector_y + 30
        option_x = selector_x + 20
        spacing = 150
        for i, (key, info) in enumerate(self.body_types.items()):
            if i == 5:
                option_y += 35
                option_x = selector_x + 20
            if key == self.selected_type:
                highlight = pygame.Surface((140, 30), pygame.SRCALPHA)
                highlight.fill((255, 255, 255, 50))
                self.screen.blit(highlight, (option_x - 5, option_y - 5))
            pygame.draw.circle(self.screen, info["color"], (option_x + 8, option_y + 10), 6)
            # Determine which key to show
            if key == "white_hole":
                key_display = "X"
            elif i < 9:
                key_display = str(i + 1)
            else:
                key_display = "0"
            name_text = self.tiny_font.render(f"{key_display}: {info['display']}", True, WHITE)
            self.screen.blit(name_text, (option_x + 20, option_y + 2))
            option_x += spacing

        # Help panel
        if self.show_help:
            help_y = 20
            help_x = SCREEN_WIDTH - 480
            help_panel = pygame.Surface((460, 560), pygame.SRCALPHA)
            help_panel.fill((0, 0, 0, 200))
            self.screen.blit(help_panel, (help_x, help_y))

            help_texts = [
                ("=== CONTROLS ===", YELLOW),
                ("Left Click: Select body / Set velocity", WHITE),
                ("Right Click: Instant create", WHITE),
                ("Middle Click + Drag: Pan camera", WHITE),
                ("Mouse Wheel: Zoom at cursor", WHITE),
                ("", WHITE),
                ("1-0: Select body type", CYAN),
                ("DELETE: Remove selected body", CYAN),
                ("CTRL+F: Follow selected", CYAN),
                ("P: Toggle trajectory prediction", CYAN),
                ("G: Toggle grid", CYAN),
                ("S / L: Save / Load", CYAN),
                ("M / Q: Mute / Toggle sound", CYAN),
                ("SPACE: Pause/Resume", CYAN),
                ("T: Toggle trails", CYAN),
                ("I: Toggle info panel", CYAN),
                ("F: Toggle FPS counter", CYAN),
                ("C: Clear all bodies", CYAN),
                ("+/-: Time scale", CYAN),
                ("R: Reset camera", CYAN),
                ("H: Toggle this help", CYAN),
                ("ESC: Main menu", CYAN),
                ("", WHITE),
                ("=== TIPS ===", YELLOW),
                ("• Drag perpendicular to create orbits", WHITE),
                ("• Select a body to see its info", WHITE),
                ("• Follow mode locks camera to selection", WHITE),
                ("• Prediction shows ~5 sec path", WHITE),
                ("• Collisions create particles and sound", WHITE),
            ]

            text_y = help_y + 15
            for text, color in help_texts:
                if text == "":
                    text_y += 10
                    continue
                help_surface = self.tiny_font.render(text, True, color)
                self.screen.blit(help_surface, (help_x + 15, text_y))
                text_y += 24
        else:
            hint = self.small_font.render("Press H for help | Press I to toggle info", True, GRAY)
            hint_rect = hint.get_rect(topright=(SCREEN_WIDTH - 20, 20))
            self.screen.blit(hint, hint_rect)

        # FPS counter
        if self.show_fps:
            fps = self.clock.get_fps()
            fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, GREEN if fps > 50 else (YELLOW if fps > 30 else RED))
            fps_rect = fps_text.get_rect(topright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 140))
            fps_bg = pygame.Surface((120, 30), pygame.SRCALPHA)
            fps_bg.fill((0, 0, 0, 200))
            self.screen.blit(fps_bg, (SCREEN_WIDTH - 140, SCREEN_HEIGHT - 145))
            self.screen.blit(fps_text, fps_rect)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "preset_menu":
            self.draw_preset_menu()
        elif self.state == "simulation":
            self.draw_simulation()
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update_physics(dt)
            self.draw()

        pygame.quit()
        sys.exit()

# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sim = GravitySimulation()
    sim.run()
    
    #---------------------------------
    
    #---------------------------------
    
    # Thanks For Playing! - @rnkbv
