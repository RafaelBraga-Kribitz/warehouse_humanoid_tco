"""Rebuild docs/assets/demo.gif from docs/assets/demo.cast (F-244).

Deterministic terminal replay: pyte emulates an 80x24 VT100, Pillow draws each
distinct screen. Idle gaps are capped so the GIF stays short.

    pip install pyte                             # one-off renderer dependency
    python scripts/render_demo_gif.py            # writes docs/assets/demo.gif + demo.lock.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pyte
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CAST = ROOT / "docs" / "assets" / "demo.cast"
GIF = ROOT / "docs" / "assets" / "demo.gif"
LOCK = ROOT / "docs" / "assets" / "demo.lock.json"
COLS, ROWS = 80, 24
WIDTH, HEIGHT = 840, 490
CELL_W, CELL_H = WIDTH / COLS, HEIGHT / ROWS
IDLE_CAP_MS = 3000
MIN_FRAME_MS = 60
TICK_MS = 200
HOLD_END_MS = 3000
BG = "#272822"
FG = "#f8f8f2"
PALETTE = {
    "black": "#272822",
    "red": "#f92672",
    "green": "#a6e22e",
    "brown": "#e6db74",
    "blue": "#66d9ef",
    "magenta": "#ae81ff",
    "cyan": "#66d9ef",
    "white": "#f8f8f2",
}
FONT_PATH = Path(__import__("matplotlib").get_data_path()) / "fonts" / "ttf" / "DejaVuSansMono.ttf"
BOLD_PATH = FONT_PATH.with_name("DejaVuSansMono-Bold.ttf")


def _colour(name: str, default: str) -> str:
    if name == "default":
        return default
    if name.startswith("bright"):
        return PALETTE.get(name[6:], default)
    if len(name) == 6:
        return f"#{name}"
    return PALETTE.get(name, default)


def _events(path: Path) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        delta, kind, data = json.loads(line)
        if kind == "o":
            out.append((float(delta), data))
    return out


def _draw(screen: pyte.Screen, fonts: tuple[ImageFont.FreeTypeFont, ...]) -> Image.Image:
    regular, bold = fonts
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    for row in range(ROWS):
        line = screen.buffer[row]
        for col in range(COLS):
            cell = line[col]
            x, y = col * CELL_W, row * CELL_H
            if not cell.data.strip():
                continue
            colour = _colour(cell.fg, FG)
            draw.text((x, y + 1), cell.data, fill=colour, font=bold if cell.bold else regular)
    if not screen.cursor.hidden:
        cx, cy = screen.cursor.x * CELL_W, screen.cursor.y * CELL_H
        draw.rectangle((cx, cy + 2, cx + CELL_W - 2, cy + CELL_H - 2), fill=FG)
    return image


def render(cast: Path = CAST, gif: Path = GIF) -> int:
    fonts = (
        ImageFont.truetype(str(FONT_PATH), 17),
        ImageFont.truetype(str(BOLD_PATH), 17),
    )
    screen = pyte.Screen(COLS, ROWS)
    stream = pyte.Stream(screen)
    frames: list[Image.Image] = []
    stamps: list[int] = []  # virtual time (ms) each frame becomes visible
    keys: list[tuple[object, ...]] = []
    clock = 0
    last_snap = -TICK_MS
    dirty = False

    def snapshot() -> None:
        nonlocal last_snap, dirty
        last_snap = clock
        dirty = False
        key = (
            tuple(
                tuple((c.data, c.fg, c.bold) for c in screen.buffer[r].values())
                for r in range(ROWS)
            ),
            screen.cursor.x,
            screen.cursor.y,
            screen.cursor.hidden,
        )
        if keys and key == keys[-1]:
            return
        keys.append(key)
        frames.append(_draw(screen, fonts))
        stamps.append(clock)

    for delta, data in _events(cast):
        gap = min(int(delta * 1000), IDLE_CAP_MS)
        if gap > TICK_MS and dirty:
            snapshot()  # show the screen as it stood before a long pause
        clock += gap
        # Replay typed commands in small pieces so they animate.
        pieces = (
            [data[i : i + 2] for i in range(0, len(data), 2)]
            if "\x1b" not in data and "\n" not in data and len(data) > 4
            else [data]
        )
        for piece in pieces:
            stream.feed(piece)
            dirty = True
            if len(pieces) > 1:
                clock += 40
            if clock - last_snap >= TICK_MS:
                snapshot()
    snapshot()
    durations = [max(stamps[i + 1] - stamps[i], MIN_FRAME_MS) for i in range(len(stamps) - 1)] + [
        HOLD_END_MS
    ]
    quantised = [f.quantize(colors=32, method=Image.Quantize.MEDIANCUT) for f in frames]
    quantised[0].save(
        gif,
        save_all=True,
        append_images=quantised[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    return len(frames)


if __name__ == "__main__":
    frame_count = render()
    LOCK.write_text(
        json.dumps(
            {
                "cast_sha256": hashlib.sha256(CAST.read_bytes()).hexdigest(),
                "gif_sha256": hashlib.sha256(GIF.read_bytes()).hexdigest(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {GIF} ({frame_count} frames) and {LOCK.name}")
    sys.exit(0)
