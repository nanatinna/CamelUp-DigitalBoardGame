import pygame

# ---------------------------------------------------------------------------
# Color constants (RGB tuples)
# ---------------------------------------------------------------------------

SAND_LIGHT     = (212, 180, 131)
SAND_DARK      = (200, 169, 110)
WOOD_DARK      = (61,  31,  10)
WOOD_MID       = (92,  61,  30)
WOOD_LIGHT     = (139, 94,  60)
PARCHMENT      = (232, 213, 163)
PARCHMENT_DARK = (196, 169, 109)
TEXT_LIGHT     = (245, 230, 200)
TEXT_DARK      = (61,  31,  10)
GOLD           = (212, 160, 23)
CAMEL_GREEN    = (58,  140, 63)
CAMEL_PURPLE   = (130, 60,  190)
CAMEL_YELLOW   = (212, 192, 32)
CAMEL_BLUE     = (46,  109, 180)
CAMEL_RED      = (200, 60,  40)
# Crazy camels (Camel Up 2.0) — move backward
CAMEL_BLACK    = (28,  28,  28)
CAMEL_WHITE    = (240, 237, 224)
# Grey die colour (the single die that moves a random crazy camel)
CAMEL_GREY_DIE = (160, 160, 160)
WHITE          = (255, 255, 255)
BLACK          = (0,   0,   0)
RED            = (200, 60,  40)
DARK_OVERLAY   = (0,   0,   0,  180)

# ---------------------------------------------------------------------------
# Camel color map
# ---------------------------------------------------------------------------

CAMEL_COLOR_MAP: dict[str, tuple] = {
    # racing camels
    "green":  CAMEL_GREEN,
    "purple": CAMEL_PURPLE,
    "yellow": CAMEL_YELLOW,
    "blue":   CAMEL_BLUE,
    "red":    CAMEL_RED,
    # crazy camels (Camel Up 2.0) — move backward
    "black":  CAMEL_BLACK,
    "white":  CAMEL_WHITE,
    # grey die (not a camel colour — used for the dice pyramid display)
    "grey":   CAMEL_GREY_DIE,
}

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

WINDOW_W = 1280
WINDOW_H = 800
TOP_BAR_H = 40
BOTTOM_BAR_H = 100
LEFT_PANEL_W = 240
RIGHT_PANEL_W = 260
CENTER_W = WINDOW_W - LEFT_PANEL_W - RIGHT_PANEL_W  # 780
MAIN_H = WINDOW_H - TOP_BAR_H - BOTTOM_BAR_H        # 660

LEFT_PANEL_RECT   = (0, TOP_BAR_H, LEFT_PANEL_W, MAIN_H)
CENTER_RECT       = (LEFT_PANEL_W, TOP_BAR_H, CENTER_W, MAIN_H)
RIGHT_PANEL_RECT  = (LEFT_PANEL_W + CENTER_W, TOP_BAR_H, RIGHT_PANEL_W, MAIN_H)
BOTTOM_BAR_RECT   = (0, TOP_BAR_H + MAIN_H, WINDOW_W, BOTTOM_BAR_H)
TOP_BAR_RECT      = (0, 0, WINDOW_W, TOP_BAR_H)

TILE_SIZE = 70
CAMEL_W = 40
CAMEL_H = 28
CAMEL_STACK_OFFSET = 18
BOARD_MARGIN = 20

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def get_camel_color(color_name: str) -> tuple:
    """Return the RGB tuple for a camel color name.

    Falls back to CAMEL_WHITE if the name is not recognised.
    """
    return CAMEL_COLOR_MAP.get(color_name.lower(), CAMEL_WHITE)


# ---------------------------------------------------------------------------
# Surface generators
# ---------------------------------------------------------------------------


_FONT_PATH = 'assets/fonts/Cinzel-Bold.otf'


def _ensure_font_init() -> None:
    """Lazily initialise pygame.font if it has not been initialised yet."""
    if not pygame.font.get_init():
        pygame.font.init()


def load_font(size: int) -> pygame.font.Font:
    """Load Cinzel-Bold at *size*; falls back to the system default."""
    _ensure_font_init()
    try:
        return pygame.font.Font(_FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont('arial', size)


def generate_fallback_surface(
    width: int,
    height: int,
    color: tuple,
    label: str = "",
    outline_color: tuple = None,
) -> pygame.Surface:
    """Create a plain coloured surface with an optional outline and label.

    Parameters
    ----------
    width, height:
        Dimensions of the returned surface in pixels.
    color:
        RGB fill colour.
    label:
        Text string to render centred on the surface.  Ignored when empty.
    outline_color:
        RGB colour for a 1-pixel border drawn around the surface edge.
        Pass ``None`` (default) to skip the outline.

    Returns
    -------
    pygame.Surface
    """
    try:
        surface = pygame.Surface((width, height))
        surface.fill(color)

        if outline_color is not None:
            pygame.draw.rect(surface, outline_color, surface.get_rect(), 1)

        if label:
            _ensure_font_init()
            font = load_font(max(14, min(height // 3, 24)))
            text_surf = font.render(label, True, WHITE if color == BLACK else BLACK)
            text_rect = text_surf.get_rect(center=(width // 2, height // 2))
            surface.blit(text_surf, text_rect)

        return surface

    except Exception:
        # Ultimate fallback: return a minimal surface without any rendering
        surface = pygame.Surface((max(width, 1), max(height, 1)))
        surface.fill(color if len(color) >= 3 else (128, 128, 128))
        return surface


def generate_camel_surface(
    color_name: str,
    width: int = 60,
    height: int = 60,
) -> pygame.Surface:
    """Create a simple camel token surface.

    Draws a rounded rectangle in the camel's colour on a transparent
    background, with the first letter of the colour name centred in white.

    Parameters
    ----------
    color_name:
        One of the recognised camel colour names (e.g. ``"blue"``).
    width, height:
        Dimensions of the surface in pixels.  Default 60 x 60.

    Returns
    -------
    pygame.Surface with per-pixel alpha.
    """
    try:
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # fully transparent background

        camel_color = get_camel_color(color_name)

        # Padding so the rounded rect does not reach the very edge
        padding = max(4, width // 10)
        rect = pygame.Rect(padding, padding, width - padding * 2, height - padding * 2)
        border_radius = max(6, width // 8)
        pygame.draw.rect(surface, camel_color, rect, border_radius=border_radius)

        # Draw a subtle darker outline
        outline = tuple(max(0, c - 40) for c in camel_color)
        pygame.draw.rect(surface, outline, rect, width=2, border_radius=border_radius)

        # Render the first letter of the colour name
        letter = color_name[0].upper() if color_name else "?"
        _ensure_font_init()
        font_size = max(14, int(height * 0.45))
        font = load_font(font_size)
        text_surf = font.render(letter, True, WHITE)
        text_rect = text_surf.get_rect(center=(width // 2, height // 2))
        surface.blit(text_surf, text_rect)

        return surface

    except Exception:
        # Return a plain opaque surface as a last resort
        surface = pygame.Surface((max(width, 1), max(height, 1)))
        surface.fill(get_camel_color(color_name))
        return surface


def generate_background_surface(width: int, height: int) -> pygame.Surface:
    """Create a sandy gradient background surface.

    Draws horizontal bands that transition smoothly from ``SAND_LIGHT`` at
    the top to ``SAND_DARK`` at the bottom.

    Parameters
    ----------
    width, height:
        Dimensions of the surface in pixels.

    Returns
    -------
    pygame.Surface
    """
    try:
        surface = pygame.Surface((width, height))

        r1, g1, b1 = SAND_LIGHT
        r2, g2, b2 = SAND_DARK

        for y in range(height):
            t = y / max(height - 1, 1)  # 0.0 at top, 1.0 at bottom
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (width - 1, y))

        return surface

    except Exception:
        # Fallback: solid mid-point colour
        surface = pygame.Surface((max(width, 1), max(height, 1)))
        mid = tuple((a + b) // 2 for a, b in zip(SAND_LIGHT, SAND_DARK))
        surface.fill(mid)
        return surface
