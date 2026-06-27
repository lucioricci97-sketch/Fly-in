"""Pygame visualizer for the Fly-in simulation."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pygame

from .graph import Graph
from .simulator import Simulator
from .zone import Zone


# Some named colours (RGB). Unknown names fall back to white.
COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "red": (255, 100, 100),
    "green": (100, 220, 120),
    "blue": (100, 160, 255),
    "yellow": (250, 230, 90),
    "orange": (250, 170, 70),
    "cyan": (100, 230, 230),
    "magenta": (230, 100, 230),
    "purple": (180, 100, 230),
    "gray": (180, 180, 180),
    "lime": (180, 240, 100),
    "brown": (160, 110, 60),
    "gold": (240, 200, 60),
}

# Light Theme Colors
BG_COLOR = (245, 245, 250)      # Light off-white
GRID_COLOR = (230, 230, 235)    # Subtle graph paper lines
EDGE_COLOR = (150, 150, 160)
TEXT_COLOR = (30, 30, 30)       # Dark text
DRONE_BG = (50, 50, 60)         # Dark grey badge for drones
DRONE_TEXT = (255, 255, 255)
BLOCKED_COLOR = (180, 180, 180)


class Visualizer:
    """Display the graph and step through the simulation visually."""

    WIDTH = 1100
    HEIGHT = 720
    PADDING = 80
    AUTO_DELAY_MS = 500

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.simulator = Simulator(graph)
        self._auto = False
        self._last_auto_tick = 0
        self._latest_moves: List[Tuple[int, str]] = []
        self._compute_layout()


    def _compute_layout(self) -> None:
        """Map zone (x, y) coords to screen pixels (fits the window)."""
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(1, max_x - min_x)
        span_y = max(1, max_y - min_y)
        
        # INCREASED margins to completely clear the UI panels AND the circle radius
        left_margin = 60
        right_margin = 250   # Safe zone for the Legend
        top_margin = 120     # Pushed down to clear the top UI header
        bottom_margin = 120  # Pushed up to clear the bottom UI and zone names
        
        usable_w = max(100, self.WIDTH - left_margin - right_margin)
        usable_h = max(100, self.HEIGHT - top_margin - bottom_margin) 
        
        self._pos: Dict[str, Tuple[int, int]] = {}
        for zone in self.graph.zones.values():
            nx = (zone.x - min_x) / span_x if span_x > 0 else 0.5
            ny = (zone.y - min_y) / span_y if span_y > 0 else 0.5
            px = int(left_margin + nx * usable_w)
            py = int(top_margin + ny * usable_h)
            self._pos[zone.name] = (px, py)


    def run(self) -> None:
        """Open the window and run until the user closes it."""
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Fly-in")
        font = pygame.font.SysFont("consolas", 14)
        big_font = pygame.font.SysFont("consolas", 20, bold=True)
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.WIDTH = event.w
                    self.HEIGHT = event.h
                    # Grab the auto-resized surface instead of recreating the window!
                    # This prevents the OS from canceling your mouse drag.
                    screen = pygame.display.get_surface()
                    self._compute_layout()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                        self._do_step()
                    elif event.key == pygame.K_a:
                        self._auto = not self._auto
                    elif event.key == pygame.K_r:
                        self.simulator = Simulator(self.graph)
                        self._latest_moves = []
            if self._auto and not self.simulator.all_delivered():
                now = pygame.time.get_ticks()
                if now - self._last_auto_tick > self.AUTO_DELAY_MS:
                    self._do_step()
                    self._last_auto_tick = now
            self._draw(screen, font, big_font)
            pygame.display.flip()
            clock.tick(30)
        pygame.quit()
    
    def _do_step(self) -> None:
        if self.simulator.all_delivered():
            return
        moves = self.simulator.step()
        self.simulator.turn_log.append(moves)
        self._latest_moves = [(d.id, label) for d, label in moves]

    def _draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        big_font: pygame.font.Font,
    ) -> None:
        screen.fill(BG_COLOR)
        
        # Draw background grid (graph paper style)
        for x in range(0, self.WIDTH, 40):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, self.HEIGHT))
        for y in range(0, self.HEIGHT, 40):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (self.WIDTH, y))
            
        self._draw_edges(screen)
        self._draw_zones(screen, font)
        self._draw_drones(screen, font)
        self._draw_hud(screen, big_font, font)

    def _draw_edges(self, screen: pygame.Surface) -> None:
        """This was the function that got accidentally deleted!"""
        for (a, b), conn in self.graph.connections.items():
            pa, pb = self._pos[a], self._pos[b]
            pygame.draw.line(screen, EDGE_COLOR, pa, pb, 3)
            if conn.max_capacity > 1:
                mx = (pa[0] + pb[0]) // 2
                my = (pa[1] + pb[1]) // 2
                pygame.draw.circle(screen, EDGE_COLOR, (mx, my), 6)

    def _zone_fill(self, zone: Zone) -> Tuple[int, int, int]:
        """Fill color represents the mechanical TYPE of the zone."""
        if zone.is_start:
            return (180, 240, 180)  # Pale Green
        if zone.is_end:
            return (250, 230, 150)  # Pale Yellow
        if zone.is_blocked:
            return (160, 160, 160)  # Dark Grey
        if zone.zone_type == "restricted":
            return (255, 190, 190)  # Pale Red (Danger/Slow)
        if zone.zone_type == "priority":
            return (190, 230, 255)  # Pale Blue (Fast)
        return (255, 255, 255)      # White (Normal)

    def _zone_border(self, zone: Zone) -> Tuple[int, int, int]:
        """Border color satisfies the subject's metadata color requirement."""
        if zone.color and zone.color in COLOR_MAP:
            return COLOR_MAP[zone.color]
        return (40, 40, 40)         # Default dark charcoal

    def _draw_zones(
        self, screen: pygame.Surface, font: pygame.font.Font
    ) -> None:
        for zone in self.graph.zones.values():
            cx, cy = self._pos[zone.name]
            radius = 28
            
            fill_color = self._zone_fill(zone)
            border_color = self._zone_border(zone)
            
            # 1. Base fill (Instantly tells you the zone's mechanics)
            pygame.draw.circle(screen, fill_color, (cx, cy), radius)
            
            # 2. Thick colored border (Satisfies the subject's metadata rule)
            pygame.draw.circle(screen, border_color, (cx, cy), radius, 4)
            
            # Render name nicely below
            label = font.render(zone.name, True, TEXT_COLOR)
            bg_rect = label.get_rect(center=(cx, cy + radius + 14))
            pygame.draw.rect(screen, BG_COLOR, bg_rect.inflate(8, 4), border_radius=4)
            screen.blit(label, bg_rect)

    def _draw_drones(
        self, screen: pygame.Surface, font: pygame.font.Font
    ) -> None:
        # Cluster drones by their visual position.
        clusters: Dict[Tuple[int, int], List[int]] = {}
        for drone in self.simulator.drones:
            if drone.delivered:
                pos = self._pos[self.graph.end]
            elif drone.in_flight_to is not None:
                origin = self._pos[drone.position]
                target = self._pos[drone.in_flight_to]
                pos = ((origin[0] + target[0]) // 2,
                       (origin[1] + target[1]) // 2)
            else:
                pos = self._pos[drone.position]
            clusters.setdefault(pos, []).append(drone.id)
            
        for pos, ids in clusters.items():
            # Spread multiple drones out into a neat grid so they NEVER overlap
            for i, drone_id in enumerate(ids):
                row = i // 3
                col = i % 3
                # Calculate an offset so they sit next to each other
                offset_x = (col * 24) - (min(len(ids), 3) - 1) * 12
                offset_y = (row * 24) - (len(ids) // 3) * 12
                
                d_pos = (pos[0] + offset_x, pos[1] + offset_y)
                
                # Draw small dark badge
                pygame.draw.circle(screen, DRONE_BG, d_pos, 11)
                pygame.draw.circle(screen, (20, 20, 20), d_pos, 11, 2) # border
                
                txt = font.render(f"{drone_id}", True, DRONE_TEXT)
                txt_rect = txt.get_rect(center=d_pos)
                screen.blit(txt, txt_rect)

    def _draw_hud(
        self,
        screen: pygame.Surface,
        big_font: pygame.font.Font,
        font: pygame.font.Font,
    ) -> None:
        # Top Left: Turn & Delivery status
        turn_text = big_font.render(
            f"Turn: {self.simulator.turn}", True, TEXT_COLOR
        )
        screen.blit(turn_text, (20, 18))
        delivered = sum(1 for d in self.simulator.drones if d.delivered)
        delivered_text = big_font.render(
            f"Delivered: {delivered}/{self.graph.nb_drones}",
            True, TEXT_COLOR
        )
        screen.blit(delivered_text, (220, 18))
        
        # Bottom Left: Controls & Last Move
        help_text = font.render(
            "SPACE/RIGHT step  |  A auto  |  R reset  |  ESC quit",
            True, TEXT_COLOR,
        )
        screen.blit(help_text, (20, 46))
        if self._latest_moves:
            moves_str = "Last turn: " + " ".join(
                f"D{i}-{lbl}" for i, lbl in self._latest_moves
            )
            txt = font.render(moves_str, True, TEXT_COLOR)
            screen.blit(txt, (20, self.HEIGHT - 24))

        # Top Right: The Legend (This solves the visual confusion!)
        legend_items = [
            ("Start", (180, 240, 180)),
            ("End", (250, 230, 150)),
            ("Normal", (255, 255, 255)),
            ("Priority (Fast)", (190, 230, 255)),
            ("Restricted (Slow)", (255, 190, 190)),
            ("Blocked", (160, 160, 160))
        ]
        
        # Create a subtle background box for the legend
        pygame.draw.rect(screen, (255, 255, 255), (self.WIDTH - 210, 15, 195, 145), border_radius=6)
        pygame.draw.rect(screen, (200, 200, 210), (self.WIDTH - 210, 15, 195, 145), 2, border_radius=6)

        start_x = self.WIDTH - 190
        start_y = 25
        for text, color in legend_items:
            # Draw the color dot
            pygame.draw.circle(screen, color, (start_x, start_y), 8)
            pygame.draw.circle(screen, (40, 40, 40), (start_x, start_y), 8, 1)
            # Draw the label text
            label = font.render(text, True, TEXT_COLOR)
            screen.blit(label, (start_x + 15, start_y - 7))
            start_y += 20

def visualize(graph: Graph) -> None:
    """Convenience: build a Visualizer and run it."""
    Visualizer(graph).run()


def visualize_existing(
    graph: Graph, simulator: Optional[Simulator] = None
) -> None:
    """Visualize using an existing Simulator (kept for symmetry)."""
    visualizer = Visualizer(graph)
    if simulator is not None:
        visualizer.simulator = simulator
    visualizer.run()