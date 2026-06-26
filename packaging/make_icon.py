"""Generate the Receipt Board application icon (``icon.ico`` + ``icon.png``).

A simple, self-contained brand mark — a white receipt card with a green check on a
blue rounded square — rendered at 256x256 and saved as a multi-resolution ``.ico``
(16/32/48/64/128/256) plus a 256x256 ``.png`` source.

This is a one-off asset generator, not part of the build. It depends on Pillow, which is
NOT a project dependency; run it ad hoc without polluting the venv::

    uv run --with pillow python packaging/make_icon.py

Re-run it to regenerate the committed ``packaging/icon.ico`` / ``packaging/icon.png``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
HERE = Path(__file__).resolve().parent

BRAND = (37, 99, 235, 255)  # blue background
BRAND_DARK = (29, 78, 216, 255)  # subtle border
CARD = (255, 255, 255, 255)  # receipt paper
ROW = (203, 213, 225, 255)  # list rows (slate-300)
CHECK = (34, 197, 94, 255)  # green check


def _rounded(draw: ImageDraw.ImageDraw, box, radius, **kw) -> None:
    draw.rounded_rectangle(box, radius=radius, **kw)


def render(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Blue rounded-square background.
    margin = size * 0.055
    _rounded(
        d,
        (margin, margin, size - margin, size - margin),
        radius=size * 0.22,
        fill=BRAND,
        outline=BRAND_DARK,
        width=max(1, int(size * 0.012)),
    )

    # White receipt card with a perforated (zigzag) bottom edge.
    cx0, cx1 = size * 0.30, size * 0.70
    cy0 = size * 0.24
    body_bottom = size * 0.66
    _rounded(d, (cx0, cy0, cx1, body_bottom), radius=size * 0.03, fill=CARD)

    teeth = 6
    tooth_w = (cx1 - cx0) / teeth
    tooth_h = size * 0.045
    pts = [(cx0, body_bottom)]
    for i in range(teeth):
        x_mid = cx0 + tooth_w * (i + 0.5)
        x_end = cx0 + tooth_w * (i + 1)
        pts.append((x_mid, body_bottom + tooth_h))
        pts.append((x_end, body_bottom))
    pts.append((cx1, body_bottom))
    d.polygon(pts, fill=CARD)

    # List rows inside the card.
    row_x0 = cx0 + (cx1 - cx0) * 0.16
    row_x1 = cx1 - (cx1 - cx0) * 0.12
    row_h = max(2, int(size * 0.022))
    for i, y_frac in enumerate((0.34, 0.44, 0.54)):
        y = size * y_frac
        x1 = row_x1 if i != 2 else row_x0 + (row_x1 - row_x0) * 0.6
        _rounded(d, (row_x0, y, x1, y + row_h), radius=row_h / 2, fill=ROW)

    # Bold green checkmark overlapping the card's lower-right.
    lw = max(3, int(size * 0.05))
    d.line(
        [
            (size * 0.50, size * 0.60),
            (size * 0.585, size * 0.685),
            (size * 0.74, size * 0.45),
        ],
        fill=CHECK,
        width=lw,
        joint="curve",
    )

    return img


def main() -> None:
    base = render(SIZE)
    png_path = HERE / "icon.png"
    ico_path = HERE / "icon.ico"
    base.save(png_path)
    base.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"wrote {png_path}")
    print(f"wrote {ico_path}")


if __name__ == "__main__":
    main()
