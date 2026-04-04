import pygame
from gui.theme import WOOD_DARK, WOOD_MID, TEXT_LIGHT, GOLD, load_font


class EventLog:
    """Scrollable event log strip along the bottom of the screen."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._font       = None
        self._font_title = None
        self.scroll_offset = 0

    def _get_fonts(self):
        if self._font is None:
            self._font       = load_font(12)
            self._font_title = load_font(12)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, self.scroll_offset - event.y)

    def draw(self, surface: pygame.Surface, event_log: list):
        self._get_fonts()

        pygame.draw.rect(surface, WOOD_DARK, self.rect)
        pygame.draw.rect(surface, WOOD_MID,  self.rect, width=2)

        title = self._font_title.render("EVENT LOG", True, GOLD)
        surface.blit(title, (self.rect.x + 6, self.rect.y + 4))

        line_h    = 16
        log_x     = self.rect.x + 82
        log_w     = self.rect.width - 92
        max_lines = self.rect.height // line_h

        if not event_log:
            no_ev = self._font.render("No events yet.", True, TEXT_LIGHT)
            surface.blit(no_ev, (log_x, self.rect.y + 6))
            return

        total = len(event_log)
        # Clamp scroll
        self.scroll_offset = min(self.scroll_offset, max(0, total - max_lines))

        start = max(0, total - max_lines - self.scroll_offset)
        end   = max(0, total - self.scroll_offset)
        visible = event_log[start:end]

        clip = pygame.Rect(log_x, self.rect.y, log_w, self.rect.height)
        surface.set_clip(clip)

        for i, evt in enumerate(visible):
            y = self.rect.y + 4 + i * line_h
            if 'rolled' in evt.lower():
                color = (210, 200, 90)
            elif 'bet' in evt.lower():
                color = (140, 220, 140)
            elif 'leg' in evt.lower() or 'end' in evt.lower():
                color = GOLD
            elif 'win' in evt.lower():
                color = (255, 210, 50)
            else:
                color = TEXT_LIGHT

            txt = evt[:90] if len(evt) > 90 else evt
            surface.blit(self._font.render(txt, True, color), (log_x, y))

        surface.set_clip(None)

        if total > max_lines:
            hint = self._font.render("▲▼", True, (120, 100, 70))
            surface.blit(hint, (self.rect.right - 22, self.rect.y + 4))
