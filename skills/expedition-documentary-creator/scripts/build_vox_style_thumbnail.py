import os
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

sys.path.insert(0, '.')
import map_telemetry_hud as mth

OUT_PATH = './youtube_thumbnail.jpg'
MOBILE_TEST_PATH = './work/thumb_mobile_150px.jpg'
W, H = 1920, 1080

print("[1/5] Creating Johnny Harris / Vox tactile archival satellite map...")

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def latlon_to_global_px(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n * 256.0
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256.0
    return x, y

ZOOM = 8
x_min, y_min = deg2num(18.2, 74.0, ZOOM)
x_max, y_max = deg2num(10.8, 79.8, ZOOM)

tile_cols = x_max - x_min + 1
tile_rows = y_max - y_min + 1

map_mosaic = Image.new('RGB', (tile_cols * 256, tile_rows * 256))
for r, ty in enumerate(range(y_min, y_max + 1)):
    for c, tx in enumerate(range(x_min, x_max + 1)):
        try:
            t = mth.fetch_hybrid_esri_tile(ZOOM, tx, ty)
        except Exception:
            t = Image.new('RGB', (256, 256), (14, 20, 28))
        map_mosaic.paste(t, (c * 256, r * 256))

# Real GPS Waypoints
REAL_ROUTE_GPS = [
    {"name": "STARTING CITY", "lat": 17.3850, "lon": 78.4867},
    {"name": "Kurnool", "lat": 15.8281, "lon": 78.0373},
    {"name": "Anantapur", "lat": 14.6819, "lon": 77.6006},
    {"name": "Metro Hub", "lat": 12.9716, "lon": 77.5946},
    {"name": "Granite Hills", "lat": 12.7209, "lon": 77.2799},
    {"name": "Mandya", "lat": 12.5230, "lon": 76.8970},
    {"name": "Valley City", "lat": 12.2958, "lon": 76.6394},
    {"name": "Gundlupet", "lat": 11.8080, "lon": 76.6890},
    {"name": "Forest Reserve", "lat": 11.6664, "lon": 76.6331},
    {"name": "Biosphere", "lat": 11.5723, "lon": 76.6475},
    {"name": "Gudalur", "lat": 11.5074, "lon": 76.4950},
    {"name": "HIGHLANDS", "lat": 11.6302, "lon": 76.2259},
]

global_origin_x = x_min * 256.0
global_origin_y = y_min * 256.0

def geo_to_mosaic_px(lat, lon):
    gx, gy = latlon_to_global_px(lat, lon, ZOOM)
    return gx - global_origin_x, gy - global_origin_y

g_coords = [geo_to_mosaic_px(p['lat'], p['lon']) for p in REAL_ROUTE_GPS]
min_gx, max_gx = min(c[0] for c in g_coords), max(c[0] for c in g_coords)
min_gy, max_gy = min(c[1] for c in g_coords), max(c[1] for c in g_coords)

crop_x0 = max(0, int(min_gx - 180))
crop_y0 = max(0, int(min_gy - 60))
crop_x1 = min(map_mosaic.width, int(max_gx + 340))
crop_y1 = min(map_mosaic.height, int(max_gy + 90))

route_crop = map_mosaic.crop((crop_x0, crop_y0, crop_x1, crop_y1))
scale_factor = H / route_crop.height
map_full = route_crop.resize((int(round(route_crop.width * scale_factor)), H), Image.Resampling.LANCZOS)

def geo_to_canvas(lat, lon):
    mx, my = geo_to_mosaic_px(lat, lon)
    return int(round((mx - crop_x0) * scale_factor)), int(round((my - crop_y0) * scale_factor))

# Tactile styling: desaturate slightly for archival documentary tone
map_arr = np.array(map_full.crop((0, 0, min(map_full.width, W), H)), dtype=np.float32)
map_arr[:, :, 0] *= 0.70  # slate navy
map_arr[:, :, 1] *= 0.85  # moss green
map_arr[:, :, 2] *= 1.12  # deep atmospheric ocean

# Procedural canvas grain texture
np.random.seed(42)
noise = np.random.normal(0, 12, (H, map_arr.shape[1])).astype(np.float32)
for c in range(3):
    map_arr[:, :, c] = np.clip(map_arr[:, :, c] + noise, 0, 255)

sat_base = Image.fromarray(map_arr.astype(np.uint8))

print("[2/5] Creating seamless photographic fusion (The Single Hero Focal Point)...")
hero_photo = Image.open('./work/thumb_reservoir.jpg').convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
hero_photo = ImageEnhance.Contrast(hero_photo).enhance(1.4)
hero_photo = ImageEnhance.Color(hero_photo).enhance(1.45)

canvas = Image.new('RGB', (W, H), (10, 16, 24))
canvas.paste(sat_base, (0, 0))

c_arr = np.array(canvas, dtype=np.float32)
p_arr = np.array(hero_photo, dtype=np.float32)

Y_grid, X_grid = np.ogrid[:H, :W]
# Smooth 850px cosine transition zone from X=550 to X=1400
t_curve = np.clip((X_grid - 550) / 850.0, 0.0, 1.0)
blend_mask = 0.5 * (1.0 - np.cos(t_curve * np.pi))

# Double-exposure blend
for c in range(3):
    c_arr[:, :, c] = c_arr[:, :, c] * (1.0 - blend_mask) + p_arr[:, :, c] * blend_mask

# Volumetric warm sunlight blooming from the mountain horizon
sun_dist = np.sqrt((X_grid - (W - 100))**2 + (Y_grid - 100)**2)
sun_glow = np.clip(1.0 - (sun_dist / 1200.0), 0.0, 1.0) ** 2.2
c_arr[:, :, 0] += sun_glow * 55  # warm amber sun ray
c_arr[:, :, 1] += sun_glow * 38
c_arr[:, :, 2] += sun_glow * 12

# Left side subtle dark gradient so text punches through with 100% clarity
text_back_scrim = np.clip(1.0 - (X_grid / 800.0), 0.0, 1.0) ** 1.5
for c in range(3):
    c_arr[:, :, c] *= (1.0 - text_back_scrim * 0.45)

# Heavy cinematic edge vignette
dist_c = np.sqrt(((X_grid - W/2) / (W/2))**2 + ((Y_grid - H/2) / (H/2))**2)
vig = np.clip(1.0 - 0.45 * (dist_c ** 1.8), 0.45, 1.0)
for c in range(3):
    c_arr[:, :, c] *= vig

final_canvas = Image.fromarray(np.clip(c_arr, 0, 255).astype(np.uint8))

print("[3/5] Drawing bold, illuminated Vox-style journey line...")
draw = ImageDraw.Draw(final_canvas, 'RGBA')
projected_pts = [geo_to_canvas(p['lat'], p['lon']) for p in REAL_ROUTE_GPS]

# Multi-stage intense neon amber route trace
for r_w, r_alpha in [
    (28, (255, 130, 20, 40)),
    (18, (255, 175, 30, 95)),
    (10, (255, 215, 60, 210)),
    (4,  (255, 255, 240, 255))
]:
    draw.line(projected_pts, fill=r_alpha, width=r_w)

# Fonts
font_huge = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 124)
font_highlight = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 110)
font_pin = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 26)
font_sub = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 28)

# Pins
hyd_pt = geo_to_canvas(17.3850, 78.4867)
ker_pt = geo_to_canvas(11.6302, 76.2259)

# 1. STARTING CITY PIN
draw.ellipse([hyd_pt[0]-16, hyd_pt[1]-16, hyd_pt[0]+16, hyd_pt[1]+16], outline=(255, 210, 50, 200), width=4)
draw.ellipse([hyd_pt[0]-8,  hyd_pt[1]-8,  hyd_pt[0]+8,  hyd_pt[1]+8],  fill=(255, 235, 90, 255), outline=(10, 15, 22, 255), width=2)
# White tactile card
tag_w, tag_h = 210, 48
tx0, ty0 = hyd_pt[0] + 20, hyd_pt[1] - 24
draw.rounded_rectangle([tx0+4, ty0+4, tx0+tag_w+4, ty0+tag_h+4], radius=8, fill=(0, 0, 0, 160)) # shadow
draw.rounded_rectangle([tx0, ty0, tx0+tag_w, ty0+tag_h], radius=8, fill=(255, 255, 255, 245), outline=(20, 30, 45, 255), width=2)
draw.text((tx0 + 16, ty0 + 8), "STARTING CITY", font=font_pin, fill=(15, 22, 32))

# 2. HIGHLANDS DESTINATION PIN
draw.ellipse([ker_pt[0]-18, ker_pt[1]-18, ker_pt[0]+18, ker_pt[1]+18], outline=(255, 220, 60, 230), width=4)
draw.ellipse([ker_pt[0]-9,  ker_pt[1]-9,  ker_pt[0]+9,  ker_pt[1]+9],  fill=(255, 65, 30, 255), outline=(255, 255, 255, 255), width=2)
# Destination orange/red card
ktx0, kty0 = ker_pt[0] - 190, ker_pt[1] - 24
draw.rounded_rectangle([ktx0+4, kty0+4, ktx0+165+4, kty0+tag_h+4], radius=8, fill=(0, 0, 0, 160)) # shadow
draw.rounded_rectangle([ktx0, kty0, ktx0+165, kty0+tag_h], radius=8, fill=(245, 55, 25, 245), outline=(255, 255, 255, 255), width=2)
draw.text((ktx0 + 18, kty0 + 8), "HIGHLANDS", font=font_pin, fill=(255, 255, 255))

print("[4/5] Applying Vox 3-word rule: Massive, high-contrast typography...")
title_x, title_y = 75, 80

# Massive multi-directional drop shadow for "2,000 KM"
for ox in range(-7, 8, 2):
    for oy in range(-7, 8, 2):
        draw.text((title_x + ox, title_y + oy), "2,000 KM", font=font_huge, fill=(0, 0, 0, 255))

# Pure white fill
draw.text((title_x, title_y), "2,000 KM", font=font_huge, fill=(255, 255, 255))

# Vox Highlighter Bar behind "DRIVE"
box_y = title_y + 140
box_w = 440
box_h = 135
# Box shadow
draw.rounded_rectangle([title_x - 12 + 6, box_y + 6, title_x - 12 + box_w + 6, box_y + box_h + 6], radius=16, fill=(0, 0, 0, 180))
# Bright glowing amber Vox bar
draw.rounded_rectangle([title_x - 12, box_y, title_x - 12 + box_w, box_y + box_h], radius=16, fill=(255, 185, 20, 255), outline=(255, 255, 255, 200), width=3)
# Bold dark typography inside highlight box
draw.text((title_x + 32, box_y + 8), "DRIVE", font=font_highlight, fill=(12, 18, 28, 255))

# Bottom Left Minimalist Badge (4 STATES • 4K ULTRA HD)
badge_w = 480
badge_h = 56
by = H - 105
draw.rounded_rectangle([title_x - 10 + 3, by + 3, title_x - 10 + badge_w + 3, by + badge_h + 3], radius=12, fill=(0, 0, 0, 180))
draw.rounded_rectangle([title_x - 10, by, title_x - 10 + badge_w, by + badge_h], radius=12, fill=(10, 18, 28, 230), outline=(255, 255, 255, 75), width=2)
draw.text((title_x + 16, by + 12), "4 STATES  •  ROAD DOCUMENTARY", font=font_sub, fill=(235, 242, 250))

final_canvas.save(OUT_PATH, quality=96)
print(f"[SUCCESS] Vox-style high-CTR YouTube thumbnail saved to: {OUT_PATH} ({os.path.getsize(OUT_PATH)/1024:.1f} KB)")

# Generate 150px mobile preview for Squint Test
thumb_mobile = final_canvas.resize((150, 84), Image.Resampling.LANCZOS)
thumb_mobile.save(MOBILE_TEST_PATH, quality=92)
print(f"Mobile Squint Test preview saved to: {MOBILE_TEST_PATH}")
