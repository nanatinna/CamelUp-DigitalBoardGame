"""
Leg Summary Popup
=================
Shown at the end of each leg after the camel walk animation completes.
Displays standings, leg bet payouts, per-player coin delta, and dice recap.

Usage (GameScreen)::

    # open with a data dict assembled in _do_roll()
    self._leg_summary.open(data)

    # in draw() – last overlay so it sits on top:
    if self._leg_summary.is_open():
        self._leg_summary.draw(surface)

    # in handle_event() – before any other handler:
    if self._leg_summary.is_open():
        if self._leg_summary.handle_event(event):
            return
"""

import pygame
from gui.theme import CAMEL_COLOR_MAP, load_font, WINDOW_W, WINDOW_H

# ── Palette ──────────────────────────────────────────────────────────────────
_BG         = (44,  26,  14)     # #2C1A0E  dark panel
_BORDER     = (200, 150, 12)     # #C8960C  gold border
_GOLD       = (200, 150, 12)     # #C8960C  gold text / button bg
_OFF_WHITE  = (245, 230, 200)    # #F5E6C8  body text
_GREEN      = (46,  204, 64)     # positive payout
_RED_COL    = (231, 76,  60)     # negative payout
_DARK_TEXT  = (44,  26,  14)     # button label (dark on gold)
_ROW_BG     = (62,  38,  18)     # alternating table row background
_DIV        = (120, 85,  35)     # section divider line
_WHITE      = (255, 255, 255)


class LegSummaryPopup:
    """Overlay popup that summarises a completed leg."""

    POPUP_W = 560

    def __init__(self) -> None:
        self._open: bool = False
        self._data: dict | None = None
        self._btn_rect: pygame.Rect | None = None
        self._fonts: dict[int, pygame.font.Font] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def open(self, data: dict) -> None:
        """Open the popup with pre-computed leg data."""
        self._open = True
        self._data = data
        self._btn_rect = None

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False
        self._data = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Consume the event.  Returns True for all events while popup is open."""
        if not self._open:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self.close()
        # Block ALL input while popup is visible
        return True

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if not self._open or not self._data:
            return

        data = self._data
        W, H = WINDOW_W, WINDOW_H
        pw = self.POPUP_W

        # Semi-transparent dark overlay
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        surface.blit(ov, (0, 0))

        # Compute dynamic height and center card
        ph = self._compute_height(data)
        ph = min(ph, H - 60)
        px = W // 2 - pw // 2
        py = H // 2 - ph // 2

        card = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(surface, _BG, card, border_radius=14)
        pygame.draw.rect(surface, _BORDER, card, width=3, border_radius=14)

        # Clip content inside card (with small inset)
        clip = card.inflate(-6, -6)
        old_clip = surface.get_clip()
        surface.set_clip(clip)

        y = py + 16
        y = self._draw_title(surface, px, y, pw, data)
        y = self._draw_standings(surface, px, y, pw, data)
        y = self._divider(surface, px, y, pw)
        y = self._draw_bets(surface, px, y, pw, data)
        y = self._draw_player_summary(surface, px, y, pw, data)
        y = self._divider(surface, px, y, pw)
        y = self._draw_dice_recap(surface, px, y, pw, data)

        surface.set_clip(old_clip)

        # NEXT LEG button – pinned to card bottom, always fully visible
        btn_w, btn_h = 210, 40
        btn_rect = pygame.Rect(
            px + pw // 2 - btn_w // 2,
            py + ph - btn_h - 14,
            btn_w, btn_h,
        )
        self._btn_rect = btn_rect
        pygame.draw.rect(surface, _GOLD, btn_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 210, 60), btn_rect, width=2, border_radius=10)
        lbl = self._font(16).render("NEXT LEG  \u2192", True, _DARK_TEXT)
        surface.blit(lbl, lbl.get_rect(center=btn_rect.center))

    # ── Section renderers ─────────────────────────────────────────────────────

    def _draw_title(self, surface, px, y, pw, data) -> int:
        cx = px + pw // 2
        title = self._font(26).render(
            f"LEG {data['leg_number']} COMPLETE!", True, _GOLD)
        surface.blit(title, (cx - title.get_width() // 2, y))
        y += title.get_height() + 4

        first  = (data.get('first')  or '—').capitalize()
        second = (data.get('second') or '—').capitalize()
        sub = self._font(14).render(
            f"1st: {first}   \u2502   2nd: {second}", True, _OFF_WHITE)
        surface.blit(sub, (cx - sub.get_width() // 2, y))
        y += sub.get_height() + 10
        return y

    def _draw_standings(self, surface, px, y, pw, data) -> int:
        """Colored rank badges for all 5 racing camels."""
        standings = data.get('standings', [])[:5]
        if not standings:
            return y
        cx = px + pw // 2
        badge_w, badge_h = 72, 22
        gap = 6
        total_w = len(standings) * badge_w + (len(standings) - 1) * gap
        bx = cx - total_w // 2
        fn = self._font(11)
        for i, color in enumerate(standings):
            rect = pygame.Rect(bx + i * (badge_w + gap), y, badge_w, badge_h)
            col = CAMEL_COLOR_MAP.get(color, (128, 128, 128))
            pygame.draw.rect(surface, col, rect, border_radius=5)
            pygame.draw.rect(surface, (200, 200, 200), rect, width=1, border_radius=5)
            ink = (0, 0, 0) if color == 'white' else _WHITE
            lbl = fn.render(f"#{i+1} {color.capitalize()}", True, ink)
            surface.blit(lbl, lbl.get_rect(center=rect.center))
        return y + badge_h + 10

    def _draw_bets(self, surface, px, y, pw, data) -> int:
        cx   = px + pw // 2
        fn_h = self._font(13)
        fn_r = self._font(12)

        hdr = fn_h.render("LEG BET RESULTS", True, _GOLD)
        surface.blit(hdr, (cx - hdr.get_width() // 2, y))
        y += hdr.get_height() + 8

        bets = data.get('bets', [])
        if not bets:
            nb = fn_r.render("No bets were placed this leg.", True, _OFF_WHITE)
            surface.blit(nb, (cx - nb.get_width() // 2, y))
            return y + 28

        # Build ordered list of camels that have bets
        camels_seen: list[str] = []
        seen_set: set[str] = set()
        for b in bets:
            if b['camel'] not in seen_set:
                seen_set.add(b['camel'])
                camels_seen.append(b['camel'])

        # Column x-positions (relative to popup left)
        c_name   = px + 28
        c_card   = px + 230
        c_payout = px + 320
        c_result = px + 410

        for camel in camels_seen:
            # Camel color badge header
            badge = pygame.Rect(px + 20, y, pw - 40, 24)
            col = CAMEL_COLOR_MAP.get(camel, (128, 128, 128))
            pygame.draw.rect(surface, col, badge, border_radius=5)
            pygame.draw.rect(surface, (200, 200, 200), badge, width=1, border_radius=5)
            ink = (0, 0, 0) if camel == 'white' else _WHITE
            badge_lbl = fn_h.render(camel.upper(), True, ink)
            surface.blit(badge_lbl, badge_lbl.get_rect(center=badge.center))
            y += 28

            for b in (b for b in bets if b['camel'] == camel):
                # Alternating row background
                row = pygame.Rect(px + 20, y, pw - 40, 24)
                pygame.draw.rect(surface, _ROW_BG, row, border_radius=3)

                payout = b['payout']
                pay_col = _GREEN if payout > 0 else _RED_COL
                pay_str = f"+{payout}" if payout > 0 else str(payout)

                if payout > 0 and payout == b['card']:
                    res_str, res_col = "1st \u2713", _GREEN
                elif payout == 1:
                    res_str, res_col = "2nd", (100, 200, 220)
                else:
                    res_str, res_col = "wrong", _RED_COL

                surface.blit(fn_r.render(b['player'], True, _OFF_WHITE),
                             (c_name, y + 4))
                surface.blit(fn_r.render(f"card: {b['card']}", True, _OFF_WHITE),
                             (c_card, y + 4))
                surface.blit(fn_r.render(pay_str, True, pay_col),
                             (c_payout, y + 4))
                surface.blit(fn_r.render(res_str, True, res_col),
                             (c_result, y + 4))
                y += 26
            y += 6

        return y

    def _draw_player_summary(self, surface, px, y, pw, data) -> int:
        cx  = px + pw // 2
        fn  = self._font(13)
        changes = data.get('player_changes', [])
        if not changes:
            return y

        hdr = fn.render("COINS THIS LEG", True, _GOLD)
        surface.blit(hdr, (cx - hdr.get_width() // 2, y))
        y += hdr.get_height() + 4

        # Two entries per line
        parts = []
        for pc in changes:
            ch = pc['change']
            sign = "+" if ch >= 0 else ""
            parts.append((f"{pc['name']}: {sign}{ch}", ch))

        # Render pairs
        for i in range(0, len(parts), 2):
            pair = parts[i:i+2]
            segments: list[tuple[str, tuple]] = []
            for text, val in pair:
                col = _GREEN if val > 0 else (_RED_COL if val < 0 else _OFF_WHITE)
                segments.append((text, col))
                segments.append(("    ", _OFF_WHITE))

            x = cx
            # Measure total width first
            total_w = sum(fn.size(s)[0] for s, _ in segments)
            x = cx - total_w // 2
            for text, col in segments:
                surf = fn.render(text, True, col)
                surface.blit(surf, (x, y))
                x += surf.get_width()
            y += fn.get_height() + 3

        return y + 6

    def _draw_dice_recap(self, surface, px, y, pw, data) -> int:
        cx  = px + pw // 2
        fn_h = self._font(12)
        fn_v = self._font(13)

        hdr = fn_h.render("DICE ROLLED THIS LEG", True, _GOLD)
        surface.blit(hdr, (cx - hdr.get_width() // 2, y))
        y += hdr.get_height() + 6

        dice = data.get('dice', [])
        if not dice:
            return y + 30

        tile_w, tile_h = 46, 38
        gap = 6
        max_per_row = (pw - 40) // (tile_w + gap)
        rows = [dice[i:i + max_per_row] for i in range(0, len(dice), max_per_row)]

        for row in rows:
            row_w = len(row) * tile_w + (len(row) - 1) * gap
            bx = cx - row_w // 2
            for i, die in enumerate(row):
                col = CAMEL_COLOR_MAP.get(die['color'], (128, 128, 128))
                rect = pygame.Rect(bx + i * (tile_w + gap), y, tile_w, tile_h)
                pygame.draw.rect(surface, col, rect, border_radius=6)
                pygame.draw.rect(surface, (200, 200, 200), rect, width=1, border_radius=6)
                ink = (0, 0, 0) if die['color'] in ('white', 'yellow') else _WHITE
                val_s = fn_v.render(str(die['value']), True, ink)
                surface.blit(val_s, val_s.get_rect(center=rect.center))
            y += tile_h + 6

        return y + 4

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _divider(self, surface, px, y, pw) -> int:
        pygame.draw.line(surface, _DIV,
                         (px + 20, y + 8), (px + pw - 20, y + 8), 1)
        return y + 18

    def _compute_height(self, data: dict) -> int:
        """Estimate total popup height so the card can be sized before drawing."""
        h = 16   # top padding
        h += 36  # title
        h += 20  # subtitle
        h += 10  # gap
        h += 28  # standings badges
        h += 10  # gap
        h += 18  # divider
        h += 22  # "LEG BET RESULTS" header
        h += 8

        bets = data.get('bets', [])
        if not bets:
            h += 28
        else:
            camels_seen: set[str] = set()
            for b in bets:
                if b['camel'] not in camels_seen:
                    camels_seen.add(b['camel'])
                    h += 28  # badge
                h += 26   # row
            h += len(camels_seen) * 6  # gaps

        n = len(data.get('player_changes', []))
        h += 22 + 4  # header
        h += (n // 2 + n % 2) * 18 + 6

        h += 18   # divider
        h += 22 + 6  # dice header

        rows = max(1, (len(data.get('dice', [])) + 8) // 9)  # rough estimate
        h += rows * (38 + 6) + 4

        h += 60   # button + padding
        return h

    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = load_font(size)
        return self._fonts[size]
