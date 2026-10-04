import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_luxury_perfume_icon(size: int, is_maskable: bool = False) -> Image.Image:
    # 4x supersampling for ultra smooth antialiased curves
    scale = 4
    canvas_size = size * scale
    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Padding factor (maskable icons need ~20% safe zone padding)
    pad_ratio = 0.22 if is_maskable else 0.08
    effective_w = canvas_size * (1.0 - 2 * pad_ratio)
    effective_h = canvas_size * (1.0 - 2 * pad_ratio)
    offset_x = canvas_size * pad_ratio
    offset_y = canvas_size * pad_ratio

    # 1. Base dark background with rounded corners
    bg_radius = int(canvas_size * (0.0 if is_maskable else 0.22))
    bg_bbox = [0, 0, canvas_size, canvas_size]
    
    # Gradient background
    for i in range(canvas_size):
        ratio = i / canvas_size
        # Dark charcoal black to deep obsidian
        r = int(18 - 12 * ratio)
        g = int(18 - 12 * ratio)
        b = int(22 - 15 * ratio)
        draw.line([(0, i), (canvas_size, i)], fill=(r, g, b, 255))

    # Mask to rounded rectangle if not maskable
    if not is_maskable:
        mask = Image.new("L", (canvas_size, canvas_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(bg_bbox, radius=bg_radius, fill=255)
        im.putalpha(mask)

    # 2. Golden ambient aura in center
    aura = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    aura_draw = ImageDraw.Draw(aura)
    cx, cy = canvas_size // 2, int(canvas_size * 0.52)
    aura_r = int(effective_w * 0.42)
    aura_draw.ellipse(
        [cx - aura_r, cy - aura_r, cx + aura_r, cy + aura_r],
        fill=(212, 175, 55, 45)
    )
    aura = aura.filter(ImageFilter.GaussianBlur(radius=int(canvas_size * 0.12)))
    im = Image.alpha_composite(im, aura)
    draw = ImageDraw.Draw(im)

    # 3. Outer golden border rim (if not maskable)
    if not is_maskable:
        rim_width = max(2, int(canvas_size * 0.015))
        draw.rounded_rectangle(
            [rim_width // 2, rim_width // 2, canvas_size - rim_width // 2, canvas_size - rim_width // 2],
            radius=bg_radius,
            outline=(212, 175, 55, 90),
            width=rim_width
        )

    # 4. Perfume Bottle Coordinates
    bottle_w = effective_w * 0.52
    bottle_h = effective_h * 0.56
    bottle_l = cx - bottle_w / 2
    bottle_r = cx + bottle_w / 2
    bottle_b = offset_y + effective_h * 0.90
    bottle_t = bottle_b - bottle_h

    # Colors
    gold_highlight = (255, 235, 150, 255)
    gold_main = (212, 175, 55, 255)
    gold_dark = (160, 120, 30, 255)
    gold_shadow = (70, 50, 15, 230)
    glass_fill = (22, 22, 28, 230)
    gold_line = (235, 195, 75, 255)
    line_w = max(4, int(canvas_size * 0.022))

    # A. Flacon Body (Beveled cut corners)
    corner_cut = bottle_w * 0.16
    body_points = [
        (bottle_l + corner_cut, bottle_t),
        (bottle_r - corner_cut, bottle_t),
        (bottle_r, bottle_t + corner_cut),
        (bottle_r, bottle_b - corner_cut),
        (bottle_r - corner_cut, bottle_b),
        (bottle_l + corner_cut, bottle_b),
        (bottle_l, bottle_b - corner_cut),
        (bottle_l, bottle_t + corner_cut),
    ]
    # Draw glass body filled
    draw.polygon(body_points, fill=glass_fill)

    # Inner liquid gradient
    liquid_margin = bottle_w * 0.08
    liquid_points = [
        (bottle_l + corner_cut + liquid_margin, bottle_t + liquid_margin * 1.5),
        (bottle_r - corner_cut - liquid_margin, bottle_t + liquid_margin * 1.5),
        (bottle_r - liquid_margin, bottle_t + corner_cut + liquid_margin),
        (bottle_r - liquid_margin, bottle_b - corner_cut - liquid_margin),
        (bottle_r - corner_cut - liquid_margin, bottle_b - liquid_margin),
        (bottle_l + corner_cut + liquid_margin, bottle_b - liquid_margin),
        (bottle_l + liquid_margin, bottle_b - corner_cut - liquid_margin),
        (bottle_l + liquid_margin, bottle_t + corner_cut + liquid_margin),
    ]
    draw.polygon(liquid_points, fill=(35, 30, 20, 200))
    # Liquid bottom glow
    draw.ellipse(
        [cx - bottle_w * 0.35, bottle_b - bottle_h * 0.45, cx + bottle_w * 0.35, bottle_b - liquid_margin],
        fill=(212, 175, 55, 60)
    )

    # Flacon Outline (Gold)
    draw.polygon(body_points, outline=gold_line, width=line_w)

    # B. Atomizer Neck / Collar
    neck_w = bottle_w * 0.32
    neck_h = effective_h * 0.065
    neck_l = cx - neck_w / 2
    neck_r = cx + neck_w / 2
    neck_b = bottle_t
    neck_t = neck_b - neck_h
    draw.rectangle([neck_l, neck_t, neck_r, neck_b], fill=gold_main, outline=gold_highlight, width=max(2, line_w // 2))

    # C. Stopper / Cap
    cap_w = bottle_w * 0.46
    cap_h = effective_h * 0.13
    cap_l = cx - cap_w / 2
    cap_r = cx + cap_w / 2
    cap_b = neck_t
    cap_t = cap_b - cap_h
    cap_corner = cap_w * 0.12
    cap_points = [
        (cap_l + cap_corner, cap_t),
        (cap_r - cap_corner, cap_t),
        (cap_r, cap_t + cap_corner),
        (cap_r, cap_b),
        (cap_l, cap_b),
        (cap_l, cap_t + cap_corner),
    ]
    draw.polygon(cap_points, fill=gold_main, outline=gold_highlight, width=line_w)
    # Cap inner facet highlight line
    draw.line([(cx, cap_t + 4), (cx, cap_b - 4)], fill=gold_highlight, width=max(2, line_w // 2))

    # D. Central Luxury Emblem / Diamond Sparkle
    sparkle_cy = (bottle_t + bottle_b) / 2
    sparkle_size = bottle_w * 0.24
    
    # 4-point diamond star
    star_pts = [
        (cx, sparkle_cy - sparkle_size),
        (cx + sparkle_size * 0.28, sparkle_cy - sparkle_size * 0.28),
        (cx + sparkle_size, sparkle_cy),
        (cx + sparkle_size * 0.28, sparkle_cy + sparkle_size * 0.28),
        (cx, sparkle_cy + sparkle_size),
        (cx - sparkle_size * 0.28, sparkle_cy + sparkle_size * 0.28),
        (cx - sparkle_size, sparkle_cy),
        (cx - sparkle_size * 0.28, sparkle_cy - sparkle_size * 0.28),
    ]
    draw.polygon(star_pts, fill=gold_highlight, outline=(255, 255, 255, 255), width=max(1, line_w // 3))

    # Center sparkle dot
    s_r = max(3, int(sparkle_size * 0.15))
    draw.ellipse([cx - s_r, sparkle_cy - s_r, cx + s_r, sparkle_cy + s_r], fill=(255, 255, 255, 255))

    # Downsample using high-quality Lanczos resampling
    final_img = im.resize((size, size), Image.Resampling.LANCZOS)
    return final_img

def main():
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public"))
    os.makedirs(target_dir, exist_ok=True)

    icons = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable.png", 512, True),
        ("apple-touch-icon.png", 180, False),
    ]

    for filename, size, maskable in icons:
        out_path = os.path.join(target_dir, filename)
        img = create_luxury_perfume_icon(size, is_maskable=maskable)
        img.save(out_path, format="PNG", optimize=True)
        print(f"Generated {filename} ({size}x{size}) at {out_path}")

    # Also save to frontend/src/app/apple-icon.png for Next.js convention
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "app"))
    apple_app_icon = create_luxury_perfume_icon(180, False)
    apple_app_icon.save(os.path.join(app_dir, "apple-icon.png"), format="PNG", optimize=True)
    print("Generated Next.js app/apple-icon.png")

if __name__ == "__main__":
    main()
