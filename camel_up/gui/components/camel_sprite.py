import pygame
from gui.theme import CAMEL_COLOR_MAP, CAMEL_W, CAMEL_H, WHITE, load_font


class CamelSprite:
    """Represents a single camel as a colored rounded rect with movement animation."""

    def __init__(self, color: str):
        self.color = color
        self.rgb = CAMEL_COLOR_MAP.get(color, (128, 128, 128))
        self._surface = None
        # Animation state
        self.pos = (0.0, 0.0)
        self.target_pos = (0.0, 0.0)
        self.start_pos = (0.0, 0.0)
        self.anim_frame = 20
        self.anim_frames = 20

    def _get_surface(self) -> pygame.Surface:
        if self._surface is not None:
            return self._surface
        surf = pygame.Surface((CAMEL_W, CAMEL_H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        rect = pygame.Rect(0, 0, CAMEL_W, CAMEL_H)
        pygame.draw.rect(surf, self.rgb, rect, border_radius=6)
        pygame.draw.rect(surf, WHITE, rect, width=2, border_radius=6)
        try:
            font = load_font(14)
            letter = self.color[0].upper()
            text_surf = font.render(letter, True, WHITE)
            text_rect = text_surf.get_rect(center=(CAMEL_W // 2, CAMEL_H // 2))
            surf.blit(text_surf, text_rect)
        except Exception:
            pass
        self._surface = surf
        return self._surface

    def start_animation(self, start: tuple, target: tuple, frames: int = 20):
        self.start_pos = (float(start[0]), float(start[1]))
        self.target_pos = (float(target[0]), float(target[1]))
        self.pos = self.start_pos
        self.anim_frame = 0
        self.anim_frames = max(1, frames)

    def update(self):
        if self.anim_frame < self.anim_frames:
            self.anim_frame += 1
            t = self.anim_frame / self.anim_frames
            t = t * t * (3 - 2 * t)  # smoothstep
            sx, sy = self.start_pos
            tx, ty = self.target_pos
            self.pos = (sx + (tx - sx) * t, sy + (ty - sy) * t)
        else:
            self.pos = self.target_pos

    @property
    def is_animating(self) -> bool:
        return self.anim_frame < self.anim_frames

    def draw(self, surface: pygame.Surface, x: int = None, y: int = None):
        surf = self._get_surface()
        if x is not None and y is not None:
            surface.blit(surf, (x, y))
        else:
            surface.blit(surf, (int(self.pos[0]), int(self.pos[1])))
