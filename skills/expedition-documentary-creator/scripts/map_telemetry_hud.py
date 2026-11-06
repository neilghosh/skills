import os
import math
import urllib.request
from io import BytesIO
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TILE_CACHE_DIR = '/Users/neilghosh/dev/video/work/sat_tiles'
os.makedirs(TILE_CACHE_DIR, exist_ok=True)

# Real towns, villages, forest checkposts, and highway markers across the route
NEARBY_PLACES = [
    # Mysuru - Ramanagara corridor
    {'name': 'Ramanagara', 'lat': 12.7209, 'lon': 77.2799, 'kind': 'town'},
    {'name': 'Channapatna', 'lat': 12.6518, 'lon': 77.2067, 'kind': 'town'},
    {'name': 'Bidadi', 'lat': 12.7981, 'lon': 77.3866, 'kind': 'village'},
    {'name': 'Maddur', 'lat': 12.5842, 'lon': 77.0444, 'kind': 'town'},
    {'name': 'Mandya', 'lat': 12.5218, 'lon': 76.8951, 'kind': 'city'},
    {'name': 'Mysuru (Mysore)', 'lat': 12.2958, 'lon': 76.6394, 'kind': 'city'},
    {'name': 'Nanjangud', 'lat': 12.1200, 'lon': 76.6801, 'kind': 'town'},
    # Bandipur & Mudumalai & Nilgiris tri-junction
    {'name': 'Gundlupet', 'lat': 11.8080, 'lon': 76.6914, 'kind': 'town'},
    {'name': 'Hangala', 'lat': 11.7165, 'lon': 76.6578, 'kind': 'village'},
    {'name': 'Bandipur Checkpost', 'lat': 11.6656, 'lon': 76.6285, 'kind': 'village'},
    {'name': 'Moolehole (KA/KL Border)', 'lat': 11.6780, 'lon': 76.4730, 'kind': 'village'},
    {'name': 'Kakkanalla (KA/TN Border)', 'lat': 11.6085, 'lon': 76.5975, 'kind': 'village'},
    {'name': 'Theppakadu', 'lat': 11.5819, 'lon': 76.5858, 'kind': 'village'},
    {'name': 'Masinagudi', 'lat': 11.5732, 'lon': 76.6429, 'kind': 'town'},
    {'name': 'Gudalur (TN)', 'lat': 11.5030, 'lon': 76.4917, 'kind': 'town'},
    {'name': 'Ooty (Udhagamandalam)', 'lat': 11.4102, 'lon': 76.6950, 'kind': 'city'},
    # Wayanad District (Kerala) towns & villages
    {'name': 'Muthanga Wildlife Post', 'lat': 11.6725, 'lon': 76.3733, 'kind': 'village'},
    {'name': 'Sultan Bathery', 'lat': 11.6644, 'lon': 76.2570, 'kind': 'town'},
    {'name': 'Meenangadi', 'lat': 11.6593, 'lon': 76.1714, 'kind': 'village'},
    {'name': 'Ambalavayal', 'lat': 11.6190, 'lon': 76.2122, 'kind': 'village'},
    {'name': 'Kalpetta (Wayanad HQ)', 'lat': 11.6103, 'lon': 76.0827, 'kind': 'city'},
    {'name': 'Kainatty', 'lat': 11.6305, 'lon': 76.0865, 'kind': 'village'},
    {'name': 'Muttil', 'lat': 11.6290, 'lon': 76.1130, 'kind': 'village'},
    {'name': 'Kaniyambetta', 'lat': 11.6895, 'lon': 76.0772, 'kind': 'village'},
    {'name': 'Kambalakkad', 'lat': 11.6780, 'lon': 76.0400, 'kind': 'village'},
    {'name': 'Chundale', 'lat': 11.5762, 'lon': 76.0544, 'kind': 'village'},
    {'name': 'Vythiri', 'lat': 11.5515, 'lon': 76.0402, 'kind': 'town'},
    {'name': 'Lakkidi (Ghat Crest)', 'lat': 11.5194, 'lon': 76.0191, 'kind': 'village'},
    {'name': 'Pozhuthana', 'lat': 11.5865, 'lon': 75.9922, 'kind': 'village'},
    {'name': 'Meppadi', 'lat': 11.5546, 'lon': 76.1353, 'kind': 'town'},
    {'name': 'Kalladi', 'lat': 11.5152, 'lon': 76.1225, 'kind': 'village'},
    {'name': 'Thollayiram Kandi', 'lat': 11.4948, 'lon': 76.1060, 'kind': 'village'},
    {'name': 'Chooralmala', 'lat': 11.4820, 'lon': 76.1460, 'kind': 'village'},
    {'name': 'Vaduvanchal', 'lat': 11.5390, 'lon': 76.2085, 'kind': 'village'},
]

# Approximate State & District Boundary Polylines for clear visual cartography
STATE_BORDERS = [
    # Karnataka (Chamarajanagar) / Tamil Nadu (Nilgiris) border along Moyar River
    [
        (11.645, 76.430), (11.625, 76.510), (11.608, 76.597),
        (11.602, 76.680), (11.595, 76.780), (11.580, 76.880)
    ],
    # Kerala (Wayanad) / Karnataka (Chamarajanagar & Mysuru) border
    [
        (11.880, 76.120), (11.790, 76.260), (11.710, 76.390),
        (11.645, 76.430)
    ],
    # Kerala (Wayanad & Malappuram) / Tamil Nadu (Nilgiris) border
    [
        (11.645, 76.430), (11.580, 76.380), (11.510, 76.310),
        (11.460, 76.210), (11.430, 76.120), (11.410, 76.040)
    ],
    # Wayanad District / Kozhikode District border (along Thamarassery Ghat escarpment)
    [
        (11.650, 75.920), (11.570, 75.965), (11.515, 76.015),
        (11.470, 76.045), (11.430, 76.120)
    ],
]

# State / District Area Watermark Labels
REGION_WATERMARKS = [
    {'text': 'KARNATAKA\n(MYSURU DIST.)', 'lat': 12.38, 'lon': 76.82},
    {'text': 'KARNATAKA\n(CHAMARAJANAGAR DIST.)', 'lat': 11.74, 'lon': 76.62},
    {'text': 'TAMIL NADU\n(THE NILGIRIS DIST.)', 'lat': 11.53, 'lon': 76.62},
    {'text': 'KERALA\n(WAYANAD DISTRICT)', 'lat': 11.62, 'lon': 76.16},
    {'text': 'KERALA\n(KOZHIKODE DIST.)', 'lat': 11.49, 'lon': 75.95},
]

SHOT_TELEMETRY = [
    {
        'id': 0,
        'title': 'NH-275 MYSURU CORRIDOR',
        'subtitle': 'RAMANAGARA DIST., KARNATAKA  •  NH-275',
        'state_dist': 'KARNATAKA • RAMANAGARA DIST.',
        'lat': 12.8012, 'lon': 77.3824,
        'alt_m': 735, 'spd_kmh': 68, 'dist_km': 45,
        'zoom': 11,
        'edge_arrows': [
            ('top-right', 'NE', 'BENGALURU (42 KM)'),
            ('bottom-left', 'SW', 'MYSURU (95 KM) / KERALA'),
        ],
    },
    {
        'id': 1,
        'title': 'BANDIPUR TIGER RESERVE',
        'subtitle': 'CHAMARAJANAGAR DIST., KARNATAKA  •  NH-181',
        'state_dist': 'KARNATAKA • CHAMARAJANAGAR DIST.',
        'lat': 11.6524, 'lon': 76.6281,
        'alt_m': 910, 'spd_kmh': 28, 'dist_km': 215,
        'zoom': 11,
        'edge_arrows': [
            ('top', 'N', 'GUNDLUPET & MYSURU (KA)'),
            ('bottom', 'S', 'TN BORDER (5 KM) & OOTY'),
            ('left', 'W', 'WAYANAD (KERALA)'),
        ],
    },
    {
        'id': 2,
        'title': 'MUDUMALAI BIOSPHERE',
        'subtitle': 'THE NILGIRIS DIST., TAMIL NADU  •  3-STATE BORDER',
        'state_dist': 'TAMIL NADU • THE NILGIRIS DIST.',
        'lat': 11.5712, 'lon': 76.5942,
        'alt_m': 880, 'spd_kmh': 18, 'dist_km': 232,
        'zoom': 11,
        'edge_arrows': [
            ('top', 'N', 'BANDIPUR (KARNATAKA)'),
            ('right', 'E', 'MASINAGUDI & OOTY (TN)'),
            ('left', 'W', 'SULTAN BATHERY (KERALA)'),
        ],
    },
    {
        'id': 3,
        'title': 'WAYANAD INTERIOR ESTATES',
        'subtitle': 'WAYANAD DIST., KERALA  •  NEAR CHUNDALE & VYTHIRI',
        'state_dist': 'KERALA • WAYANAD DISTRICT',
        'lat': 11.5815, 'lon': 76.0241,
        'alt_m': 780, 'spd_kmh': 22, 'dist_km': 305,
        'zoom': 12,
        'edge_arrows': [
            ('top-right', 'NE', 'KALPETTA TOWN (8 KM)'),
            ('bottom', 'S', 'VYTHIRI (3 KM) & MEPPADI'),
            ('left', 'W', 'KOZHIKODE DIST. BORDER'),
        ],
    },
    {
        'id': 4,
        'title': 'VYTHIRI RAINFOREST HILLS',
        'subtitle': 'WAYANAD DIST., KERALA  •  ABOVE THAMARASSERY GHAT',
        'state_dist': 'KERALA • WAYANAD DISTRICT',
        'lat': 11.5515, 'lon': 76.0402,
        'alt_m': 776, 'spd_kmh': 32, 'dist_km': 318,
        'zoom': 12,
        'edge_arrows': [
            ('top', 'N', 'KALPETTA HQ (11 KM)'),
            ('bottom-left', 'SW', 'LAKKIDI & KOZHIKODE (NH-766)'),
            ('right', 'E', 'MEPPADI TEA ESTATES (10 KM)'),
        ],
    },
    {
        'id': 5,
        'title': 'MEPPADI TEA GARDENS',
        'subtitle': 'WAYANAD DIST., KERALA  •  MEPPADI – OOTY ROAD',
        'state_dist': 'KERALA • WAYANAD DISTRICT',
        'lat': 11.5350, 'lon': 76.1250,
        'alt_m': 940, 'spd_kmh': 0, 'dist_km': 334,
        'zoom': 12,
        'edge_arrows': [
            ('top-left', 'NW', 'KALPETTA (12 KM)'),
            ('bottom', 'S', 'KALLADI & 900 KANDI (5 KM)'),
            ('right', 'E', 'VADUVANCHAL & GUDALUR (TN)'),
        ],
    },
    {
        'id': 6,
        'title': '900 KANDI (THOLLAYIRAM)',
        'subtitle': 'WAYANAD DIST., KERALA  •  ABOVE KALLADI & MEPPADI',
        'state_dist': 'KERALA • WAYANAD DISTRICT',
        'lat': 11.4948, 'lon': 76.1060,
        'alt_m': 1455, 'spd_kmh': 14, 'dist_km': 344,
        'zoom': 12,
        'edge_arrows': [
            ('top', 'N', 'KALLADI & MEPPADI (6 KM)'),
            ('bottom', 'S', 'MALAPPURAM DIST. / NILAMBUR'),
            ('right', 'E', 'CHOORALMALA (4 KM)'),
        ],
    },
    {
        'id': 7,
        'title': 'WESTERN GHATS ESCARPMENT',
        'subtitle': 'WAYANAD – MALAPPURAM BORDER  •  1,458m RIDGE',
        'state_dist': 'KERALA • WAYANAD / MALAPPURAM BORDER',
        'lat': 11.4948, 'lon': 76.1060,
        'alt_m': 1458, 'spd_kmh': 0, 'dist_km': 345,
        'zoom': 12,
        'edge_arrows': [
            ('top', 'N', 'MEPPADI & KALPETTA'),
            ('bottom-left', 'SW', 'KOZHIKODE & ARABIAN SEA'),
            ('right', 'E', 'TAMIL NADU (NILGIRIS)'),
        ],
    },
    {
        'id': 8,
        'title': 'KALPETTA HIGHLANDS',
        'subtitle': 'WAYANAD DIST., KERALA  •  KAMBALAKKAD – KALPETTA',
        'state_dist': 'KERALA • WAYANAD DISTRICT',
        'lat': 11.6650, 'lon': 76.0650,
        'alt_m': 865, 'spd_kmh': 24, 'dist_km': 368,
        'zoom': 12,
        'edge_arrows': [
            ('bottom', 'S', 'KALPETTA TOWN (6 KM)'),
            ('top', 'N', 'MANANTHAVADY & KANNUR'),
            ('right', 'E', 'SULTAN BATHERY & MYSURU'),
        ],
    },
]

CHAPTERS = [
    {
        'before_shot': 0,
        'chapter_num': 'CHAPTER I',
        'title': 'THE ROYAL MYSORE & TIGER CORRIDOR',
        'subtitle': 'Karnataka (Ramanagara & Mysuru)   >>   Bandipur Tiger Reserve   >>   Tamil Nadu (Mudumalai)',
        'wp_indices': [0, 1, 2],
        'center_lat': 12.15, 'center_lon': 76.85, 'zoom': 9,
        'stats': 'STATES: KARNATAKA -> TAMIL NADU    |    DISTANCE: 232 KM    |    ELEVATION: 735m TO 910m',
        'narration': 'Chapter One. From the plains of Mysore into the Bandipur and Mudumalai tiger corridor.',
        'dir_banners': [
            ('top-right', 'NE >> BENGALURU (NH-275)'),
            ('left', '<< KERALA (WAYANAD & KANNUR)'),
            ('bottom-right', 'SE >> OOTY & COIMBATORE (TAMIL NADU)'),
        ],
    },
    {
        'before_shot': 3,
        'chapter_num': 'CHAPTER II',
        'title': 'CROSSING INTO WAYANAD DISTRICT, KERALA',
        'subtitle': '3-State Border (KA / TN / KL)   >>   Sultan Bathery   >>   Kalpetta, Vythiri & Meppadi',
        'wp_indices': [2, 4, 5],
        'center_lat': 11.58, 'center_lon': 76.28, 'zoom': 11,
        'stats': 'BORDER: NILGIRIS (TN) -> WAYANAD (KL)    |    DISTANCE: 102 KM    |    ELEVATION: 776m TO 940m',
        'narration': 'Chapter Two. Crossing the Kerala border into the rainforest hills and colonial tea estates of Wayanad.',
        'dir_banners': [
            ('top', 'N >> KARNATAKA (MYSURU & BANDIPUR)'),
            ('bottom-right', 'E >> TAMIL NADU (MASINAGUDI & OOTY)'),
            ('bottom-left', 'SW >> KOZHIKODE & MALABAR COAST (NH-766)'),
        ],
    },
    {
        'before_shot': 6,
        'chapter_num': 'CHAPTER III',
        'title': 'ASCENT TO 900 KANDI & KALPETTA',
        'subtitle': 'Meppadi & Kalladi Village   >>   1,458m Thollayiram Kandi Ridge   >>   Kalpetta HQ',
        'wp_indices': [5, 6, 8],
        'center_lat': 11.58, 'center_lon': 76.08, 'zoom': 12,
        'stats': 'DISTRICT: WAYANAD, KERALA    |    SUMMIT ALTITUDE: 1,458m    |    TOTAL ROUTE: 368 KM',
        'narration': 'Chapter Three. Ascending fourteen hundred and fifty meters to the summit ridges of Nine Hundred Kandi.',
        'dir_banners': [
            ('top', 'N >> MANANTHAVADY & KARNATAKA'),
            ('bottom', 'S >> MALAPPURAM DIST. (NILAMBUR VALLEY)'),
            ('left', 'W >> VYTHIRI, LAKKIDI & KOZHIKODE'),
            ('right', 'E >> SULTAN BATHERY & TAMIL NADU'),
        ],
    },
]


def load_font(size, bold=False):
    candidates = [
        '/System/Library/Fonts/Supplemental/Avenir Next.ttc',
        '/System/Library/Fonts/HelveticaNeue.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size, index=1 if bold else 0)
            except Exception:
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return xtile, ytile


def fetch_hybrid_esri_tile(z, x, y):
    """
    Fetches and alpha-composites:
      1. Esri World_Imagery (Satellite base)
      2. Esri Reference/World_Transportation (Highways, ghat roads, local roads)
      3. Esri Reference/World_Boundaries_and_Places (State/District borders, town & village names)
    """
    cache_path = os.path.join(TILE_CACHE_DIR, f'hybrid_{z}_{x}_{y}.png')
    if os.path.exists(cache_path):
        try:
            return Image.open(cache_path).convert('RGB')
        except Exception:
            pass

    base_url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    trans_url = f'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}'
    places_url = f'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'

    try:
        req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            base_im = Image.open(BytesIO(r.read())).convert('RGBA')
    except Exception:
        base_im = Image.new('RGBA', (256, 256), (28, 52, 36, 255))

    # Slightly darken raw satellite layer before compositing labels so road/town labels pop clearly
    arr = np.array(base_im, dtype=np.float32)
    arr[:, :, :3] *= 0.84
    base_im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')

    for overlay_url in (trans_url, places_url):
        try:
            req = urllib.request.Request(overlay_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as r:
                ov_im = Image.open(BytesIO(r.read())).convert('RGBA')
                base_im = Image.alpha_composite(base_im, ov_im)
        except Exception:
            pass

    rgb_im = base_im.convert('RGB')
    try:
        rgb_im.save(cache_path)
    except Exception:
        pass
    return rgb_im


def build_satellite_patch(center_lat, center_lon, zoom, width, height):
    cx, cy = deg2num(center_lat, center_lon, zoom)
    half_w_tiles = (width / 256.0) / 2.0 + 1.0
    half_h_tiles = (height / 256.0) / 2.0 + 1.0

    min_tx = int(math.floor(cx - half_w_tiles))
    max_tx = int(math.ceil(cx + half_w_tiles))
    min_ty = int(math.floor(cy - half_h_tiles))
    max_ty = int(math.ceil(cy + half_h_tiles))

    grid_w = (max_tx - min_tx + 1) * 256
    grid_h = (max_ty - min_ty + 1) * 256
    canvas = Image.new('RGB', (grid_w, grid_h))

    for tx in range(min_tx, max_tx + 1):
        for ty in range(min_ty, max_ty + 1):
            tile = fetch_hybrid_esri_tile(zoom, tx, ty)
            canvas.paste(tile, ((tx - min_tx) * 256, (ty - min_ty) * 256))

    px_center_x = (cx - min_tx) * 256.0
    px_center_y = (cy - min_ty) * 256.0

    left = int(round(px_center_x - width / 2.0))
    top = int(round(px_center_y - height / 2.0))
    cropped = canvas.crop((left, top, left + width, top + height))

    def latlon_to_px(lat, lon):
        tx, ty = deg2num(lat, lon, zoom)
        x = (tx - min_tx) * 256.0 - left
        y = (ty - min_ty) * 256.0 - top
        return x, y

    return cropped, latlon_to_px


def draw_dashed_polyline(draw, pts, color=(110, 225, 255, 200), width=2, dash_len=8, gap_len=6):
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 1:
            continue
        ux, uy = dx / dist, dy / dist
        pos = 0.0
        while pos < dist:
            end_pos = min(dist, pos + dash_len)
            sx, sy = x0 + ux * pos, y0 + uy * pos
            ex, ey = x0 + ux * end_pos, y0 + uy * end_pos
            draw.line([(sx, sy), (ex, ey)], fill=color, width=width)
            pos += dash_len + gap_len


def draw_cartographic_context(draw, latlon_to_px, width, height, is_mini=False):
    """
    Draws State/District dashed boundaries, State/District area labels, and
    nearby Town/Village callout pins that fall within the map viewport.
    """
    # 1. Draw dashed State & District border lines
    for border in STATE_BORDERS:
        b_pts = [latlon_to_px(lat, lon) for lat, lon in border]
        draw_dashed_polyline(
            draw, b_pts,
            color=(100, 230, 255, 195 if is_mini else 215),
            width=2 if is_mini else 3,
            dash_len=7 if is_mini else 12,
            gap_len=5 if is_mini else 8
        )

    # 2. Draw State / District Watermark labels if inside viewport
    f_reg = load_font(9 if is_mini else 14, bold=True)
    for reg in REGION_WATERMARKS:
        rx, ry = latlon_to_px(reg['lat'], reg['lon'])
        if 25 < rx < width - 85 and 25 < ry < height - 35:
            draw.text((rx - 30, ry - 10), reg['text'], fill=(140, 235, 255, 165 if is_mini else 185), font=f_reg)

    # 3. Draw nearby Towns & Villages with anti-collision check
    f_town = load_font(10 if is_mini else 14, bold=True)
    f_vil = load_font(9 if is_mini else 12, bold=False)
    occupied_boxes = []

    # Avoid center of mini-map so current GPS pin stays clear
    if is_mini:
        occupied_boxes.append((width // 2 - 26, height // 2 - 26, width // 2 + 26, height // 2 + 26))

    for pl in NEARBY_PLACES:
        px, py = latlon_to_px(pl['lat'], pl['lon'])
        margin_x = 18 if is_mini else 60
        margin_y = 26 if is_mini else 135
        if not (margin_x <= px <= width - margin_x and margin_y <= py <= height - margin_y):
            continue

        font = f_town if pl['kind'] in ('city', 'town') else f_vil
        name = pl['name']
        tw = int(len(name) * (6.2 if is_mini else 8.2) + 10)
        th = 15 if is_mini else 22

        bx0, by0 = int(px + 6), int(py - th // 2)
        if bx0 + tw > width - 6:
            bx0 = int(px - tw - 6)
        bx1, by1 = bx0 + tw, by0 + th

        # Check overlap with already drawn town labels
        overlap = False
        for ox0, oy0, ox1, oy1 in occupied_boxes:
            if not (bx1 < ox0 - 3 or bx0 > ox1 + 3 or by1 < oy0 - 2 or by0 > oy1 + 2):
                overlap = True
                break
        if overlap:
            continue

        occupied_boxes.append((bx0, by0, bx1, by1))
        dot_r = 3 if pl['kind'] in ('city', 'town') else 2
        dot_col = (255, 230, 110, 255) if pl['kind'] in ('city', 'town') else (210, 240, 255, 235)
        draw.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r], fill=dot_col, outline=(10, 15, 20, 255), width=1)

        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=3, fill=(8, 14, 20, 195), outline=(255, 255, 255, 65), width=1)
        txt_col = (255, 240, 150, 255) if pl['kind'] in ('city', 'town') else (225, 240, 255, 245)
        draw.text((bx0 + 4, by0 + 1), name, fill=txt_col, font=font)


def draw_vector_arrow(draw, cx, cy, direction, color=(255, 205, 65, 255), size=5):
    angles = {
        'N': -math.pi / 2,
        'S': math.pi / 2,
        'E': 0.0,
        'W': math.pi,
        'NE': -math.pi / 4,
        'NW': -3 * math.pi / 4,
        'SE': math.pi / 4,
        'SW': 3 * math.pi / 4,
    }
    ang = angles.get(direction, 0.0)
    tip = (cx + math.cos(ang) * size, cy + math.sin(ang) * size)
    left = (cx + math.cos(ang + 2.4) * size, cy + math.sin(ang + 2.4) * size)
    right = (cx + math.cos(ang - 2.4) * size, cy + math.sin(ang - 2.4) * size)
    draw.polygon([tip, left, right], fill=color)


def draw_mini_map_edge_arrows(draw, map_w, map_h, edge_arrows):
    """
    Draws directional edge callouts on the PiP mini-map showing which way adjacent
    states, districts, and major towns lie.
    """
    f_arr = load_font(9, bold=True)
    for pos, dir_code, label in edge_arrows:
        bw = int(len(label) * 5.7 + 22)
        bh = 16
        if pos == 'top':
            x0, y0 = (map_w - bw) // 2, 5
        elif pos == 'top-right':
            x0, y0 = map_w - bw - 5, 5
        elif pos == 'top-left':
            x0, y0 = 42, 5
        elif pos == 'bottom':
            x0, y0 = (map_w - bw) // 2, map_h - bh - 5
        elif pos == 'bottom-left':
            x0, y0 = 5, map_h - bh - 5
        elif pos == 'bottom-right':
            x0, y0 = map_w - bw - 5, map_h - bh - 5
        elif pos == 'left':
            x0, y0 = 5, map_h // 2 - 28
        else:  # right
            x0, y0 = map_w - bw - 5, map_h // 2 + 12

        x0 = max(4, min(map_w - bw - 4, x0))
        y0 = max(4, min(map_h - bh - 4, y0))

        draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=4, fill=(10, 18, 28, 225), outline=(255, 195, 55, 190), width=1)
        draw_vector_arrow(draw, x0 + 9, y0 + bh // 2, dir_code, color=(255, 205, 65, 255), size=5)
        draw.text((x0 + 17, y0 + 2), label, fill=(255, 235, 175, 255), font=f_arr)


def choose_best_hud_corner(mp4_path, start_sec, dur_sec, hud_w=540, hud_h=268, margin=26):
    import subprocess
    mid_t = start_sec + dur_sec * 0.35
    cmd = [
        'ffmpeg', '-v', 'error', '-ss', f'{mid_t:.2f}', '-i', mp4_path,
        '-frames:v', '1', '-vf', 'scale=640:360', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'
    ]
    try:
        raw = subprocess.check_output(cmd)
        frame = np.frombuffer(raw, dtype=np.uint8).reshape((360, 640, 3)).astype(np.float32)
    except Exception:
        return (1920 - hud_w - margin, margin, 'top-right')

    bw = int(hud_w * 640 / 1920)
    bh = int(hud_h * 360 / 1080)
    mx = int(margin * 640 / 1920)
    my = int(margin * 360 / 1080)

    corners = [
        ('top-right', 640 - bw - mx, my, 1920 - hud_w - margin, margin),
        ('top-left', mx, my, margin, margin),
        ('bottom-right', 640 - bw - mx, 360 - bh - my, 1920 - hud_w - margin, 1080 - hud_h - margin),
        ('bottom-left', mx, 360 - bh - my, margin, 1080 - hud_h - margin),
    ]

    best_score = 1e18
    best_pos = (1920 - hud_w - margin, margin, 'top-right')

    gray = 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    edge_energy = gx + gy

    for name, x0, y0, full_x, full_y in corners:
        patch_edge = edge_energy[y0:y0+bh, x0:x0+bw]
        patch_std = np.std(gray[y0:y0+bh, x0:x0+bw])
        bias = 0.92 if 'right' in name else 1.0
        score = (np.mean(patch_edge) * 2.0 + patch_std * 0.5) * bias
        if score < best_score:
            best_score = score
            best_pos = (full_x, full_y, name)

    return best_pos


def fetch_clean_sat_road_tile(z, x, y):
    """Fetches pure Esri World_Imagery satellite terrain with zero tiny raster road/town text."""
    cache_path = os.path.join(TILE_CACHE_DIR, f'pure_sat_{z}_{x}_{y}.png')
    if os.path.exists(cache_path):
        try:
            return Image.open(cache_path).convert('RGB')
        except Exception:
            pass

    base_url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

    try:
        req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            base_im = Image.open(BytesIO(r.read())).convert('RGBA')
    except Exception:
        base_im = Image.new('RGBA', (256, 256), (28, 52, 36, 255))

    arr = np.array(base_im, dtype=np.float32)
    arr[:, :, :3] *= 0.90
    rgb_im = Image.fromarray(np.clip(arr[:, :, :3], 0, 255).astype(np.uint8), 'RGB')
    try:
        rgb_im.save(cache_path)
    except Exception:
        pass
    return rgb_im


def build_clean_satellite_patch(center_lat, center_lon, zoom, width, height):
    cx, cy = deg2num(center_lat, center_lon, zoom)
    half_w_tiles = (width / 256.0) / 2.0 + 1.0
    half_h_tiles = (height / 256.0) / 2.0 + 1.0

    min_tx = int(math.floor(cx - half_w_tiles))
    max_tx = int(math.ceil(cx + half_w_tiles))
    min_ty = int(math.floor(cy - half_h_tiles))
    max_ty = int(math.ceil(cy + half_h_tiles))

    grid_w = (max_tx - min_tx + 1) * 256
    grid_h = (max_ty - min_ty + 1) * 256
    canvas = Image.new('RGB', (grid_w, grid_h))

    for tx in range(min_tx, max_tx + 1):
        for ty in range(min_ty, max_ty + 1):
            tile = fetch_clean_sat_road_tile(zoom, tx, ty)
            canvas.paste(tile, ((tx - min_tx) * 256, (ty - min_ty) * 256))

    px_center_x = (cx - min_tx) * 256.0
    px_center_y = (cy - min_ty) * 256.0

    left = int(round(px_center_x - width / 2.0))
    top = int(round(px_center_y - height / 2.0))
    cropped = canvas.crop((left, top, left + width, top + height))

    def latlon_to_px(lat, lon):
        tx, ty = deg2num(lat, lon, zoom)
        x = (tx - min_tx) * 256.0 - left
        y = (ty - min_ty) * 256.0 - top
        return x, y

    return cropped, latlon_to_px


def render_hud_overlay_png(shot_idx, out_png_path, is_4k=False):
    """
    Renders a clean, spacious, large-font Geographic Telemetry Card with zero micro-print clutter:
      - Uncluttered satellite mini-map (no tiny raster labels, town pills, or edge boxes)
      - Large, high-contrast typography (3.5x-4x larger than legacy HUD)
      - Perfectly balanced Location Title, State/Corridor Pill, and Elevation + Distance tiles.
    """
    scale = 2 if is_4k else 1
    W, H = 580 * scale, 204 * scale
    info = SHOT_TELEMETRY[shot_idx % len(SHOT_TELEMETRY)]

    card_rgb = Image.new('RGB', (W, H), (10, 16, 24))
    draw = ImageDraw.Draw(card_rgb, 'RGBA')

    # Left side: Clean Satellite Map (zero tiny raster labels or overlapping pills)
    pad = 14 * scale
    map_w, map_h = 200 * scale, H - 2 * pad
    sat_img, latlon_to_px = build_clean_satellite_patch(info['lat'], info['lon'], max(9, info.get('zoom', 11) - 1), map_w, map_h)
    map_draw = ImageDraw.Draw(sat_img, 'RGBA')

    # Draw bold route line only (clean & uncluttered)
    pts_px = [latlon_to_px(s['lat'], s['lon']) for s in SHOT_TELEMETRY]
    if len(pts_px) > 1:
        map_draw.line(pts_px, fill=(255, 200, 70, 150), width=4 * scale)
        if shot_idx > 0:
            map_draw.line(pts_px[:min(len(pts_px), shot_idx + 1)], fill=(255, 140, 20, 255), width=6 * scale)

    # Center location beacon
    cx, cy = map_w // 2, map_h // 2
    map_draw.ellipse([cx - 22 * scale, cy - 22 * scale, cx + 22 * scale, cy + 22 * scale], outline=(255, 190, 40, 195), width=3 * scale)
    map_draw.ellipse([cx - 11 * scale, cy - 11 * scale, cx + 11 * scale, cy + 11 * scale], fill=(255, 70, 30, 255), outline=(255, 255, 255, 255), width=3 * scale)

    map_mask = Image.new('L', (map_w, map_h), 0)
    ImageDraw.Draw(map_mask).rounded_rectangle([0, 0, map_w - 1, map_h - 1], radius=12 * scale, fill=255)
    card_rgb.paste(sat_img, (pad, pad), map_mask)
    draw.rounded_rectangle([pad, pad, pad + map_w, pad + map_h], radius=12 * scale, outline=(255, 255, 255, 120), width=2 * scale)

    # Right Side: Big, bold, readable typography
    rx = pad + map_w + 18 * scale
    f_title = load_font(22 * scale, bold=True)
    f_state = load_font(15 * scale, bold=True)
    f_label = load_font(13 * scale, bold=True)
    f_val   = load_font(27 * scale, bold=True)

    title_str = info['title']
    if len(title_str) > 23:
        title_str = title_str[:22].rstrip()

    draw.text((rx, 16 * scale), title_str, fill=(255, 210, 65, 255), font=f_title)

    # State & Corridor Pill
    state_str = info.get('state_dist', 'SOUTH INDIA EXPEDITION')
    state_str = state_str.replace(' DISTRICT', '').replace(' DIST.', '').strip()
    draw.rounded_rectangle([rx, 52 * scale, W - pad, 86 * scale], radius=6 * scale, fill=(20, 48, 66, 240), outline=(100, 220, 255, 180), width=1 * scale)
    draw.text((rx + 10 * scale, 59 * scale), state_str, fill=(170, 240, 255, 255), font=f_state)

    # 2 Large, High-Contrast Metric Boxes (Elevation & Distance)
    box_y0, box_y1 = 98 * scale, H - pad
    box_w = (W - pad - rx - 12 * scale) // 2

    # Box 1: Elevation
    draw.rounded_rectangle([rx, box_y0, rx + box_w, box_y1], radius=10 * scale, fill=(20, 30, 42, 245), outline=(90, 150, 195, 150), width=2 * scale)
    draw.text((rx + 14 * scale, box_y0 + 10 * scale), 'ELEVATION', fill=(150, 205, 240, 255), font=f_label)
    draw.text((rx + 14 * scale, box_y0 + 34 * scale), f"{info['alt_m']} m", fill=(255, 255, 255, 255), font=f_val)

    # Box 2: Expedition Distance
    bx2 = rx + box_w + 12 * scale
    draw.rounded_rectangle([bx2, box_y0, W - pad, box_y1], radius=10 * scale, fill=(20, 30, 42, 245), outline=(245, 185, 55, 160), width=2 * scale)
    draw.text((bx2 + 14 * scale, box_y0 + 10 * scale), 'ROUTE DIST', fill=(255, 215, 120, 255), font=f_label)
    draw.text((bx2 + 14 * scale, box_y0 + 34 * scale), f"{info['dist_km']} km", fill=(255, 215, 75, 255), font=f_val)

    # Outer border
    draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=18 * scale, outline=(245, 180, 50, 230), width=3 * scale)

    card_rgba = card_rgb.convert('RGBA')
    alpha_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(alpha_mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=18 * scale, fill=238)
    card_rgba.putalpha(alpha_mask)

    card_rgba.save(out_png_path)
    return out_png_path


def render_chapter_map_video(chap_dict, out_mp4_path, wav_path, duration=3.4, fps=25):
    import subprocess
    W, H = 1920, 1080
    total_frames = int(round(duration * fps))

    sat_base, latlon_to_px = build_satellite_patch(
        chap_dict['center_lat'], chap_dict['center_lon'], chap_dict['zoom'], W, H
    )
    arr = np.array(sat_base, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W * 0.5) / (W * 0.58)) ** 2 + ((yy - H * 0.5) / (H * 0.58)) ** 2)
    vig = np.clip(1.0 - 0.42 * (dist ** 1.6), 0.38, 1.0)[:, :, None]
    arr = np.clip(arr * vig * 0.92, 0, 255).astype(np.uint8)
    bg_img = Image.fromarray(arr).convert('RGB')

    bg_draw = ImageDraw.Draw(bg_img, 'RGBA')
    for x in range(160, W, 200):
        bg_draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 22), width=1)
    for y in range(140, H, 200):
        bg_draw.line([(0, y), (W, y)], fill=(255, 255, 255, 22), width=1)

    # Draw State/District borders, State watermarks, and nearby Towns/Villages on Chapter Map
    draw_cartographic_context(bg_draw, latlon_to_px, W, H, is_mini=False)

    # Top & Bottom banners
    bg_draw.rectangle([0, 0, W, 135], fill=(8, 13, 18, 230))
    bg_draw.line([(0, 135), (W, 135)], fill=(245, 175, 45, 205), width=2)

    bg_draw.rectangle([0, H - 115, W, H], fill=(8, 13, 18, 230))
    bg_draw.line([(0, H - 115), (W, H - 115)], fill=(245, 175, 45, 205), width=2)

    f_chap = load_font(17, bold=True)
    f_title = load_font(36, bold=True)
    f_sub = load_font(19, bold=False)
    f_wp = load_font(16, bold=True)
    f_stats = load_font(18, bold=True)
    f_dir = load_font(15, bold=True)

    bg_draw.text((70, 20), f"KERALA & WESTERN GHATS EXPEDITION   •   {chap_dict['chapter_num']}", fill=(245, 185, 55, 255), font=f_chap)
    bg_draw.text((70, 48), chap_dict['title'], fill=(255, 255, 255, 255), font=f_title)
    bg_draw.text((70, 95), chap_dict['subtitle'], fill=(180, 210, 230, 240), font=f_sub)
    bg_draw.text((70, H - 70), chap_dict['stats'], fill=(245, 205, 85, 255), font=f_stats)

    # Draw directional edge banners showing neighboring states/cities
    for pos, txt in chap_dict.get('dir_banners', []):
        bw = int(len(txt) * 9.2 + 28)
        bh = 32
        if pos == 'top':
            bx, by = (W - bw) // 2, 150
        elif pos == 'top-right':
            bx, by = W - bw - 45, 150
        elif pos == 'bottom':
            bx, by = (W - bw) // 2, H - 160
        elif pos == 'bottom-left':
            bx, by = 45, H - 160
        elif pos == 'bottom-right':
            bx, by = W - bw - 45, H - 160
        elif pos == 'left':
            bx, by = 45, H // 2 - 20
        else:
            bx, by = W - bw - 45, H // 2 - 20
        bg_draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill=(12, 24, 36, 225), outline=(100, 220, 255, 195), width=2)
        bg_draw.text((bx + 12, by + 6), txt, fill=(175, 240, 255, 255), font=f_dir)

    wp_indices = chap_dict['wp_indices']
    wp_coords = []
    for idx in wp_indices:
        s = SHOT_TELEMETRY[idx]
        px, py = latlon_to_px(s['lat'], s['lon'])
        px = max(140, min(W - 320, px))
        py = max(210, min(H - 190, py))
        wp_coords.append((px, py, s['title'], f"{s['alt_m']}m"))

    dense_path = []
    for i in range(len(wp_coords) - 1):
        x0, y0, _, _ = wp_coords[i]
        x1, y1, _, _ = wp_coords[i + 1]
        steps = 45
        for st in range(steps):
            t = st / float(steps)
            mx = (x0 + x1) * 0.5 + (y1 - y0) * 0.08
            my = (y0 + y1) * 0.5 - (x1 - x0) * 0.08
            bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t ** 2 * x1
            by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t ** 2 * y1
            dense_path.append((bx, by))
    dense_path.append((wp_coords[-1][0], wp_coords[-1][1]))

    cmd = [
        'ffmpeg', '-y', '-v', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
        '-i', wav_path,
        '-map', '0:v:0', '-map', '1:a:0',
        '-vf', f'fade=t=in:st=0:d=0.4,fade=t=out:st={duration-0.45:.2f}:d=0.45,fps=25,settb=1/25,format=yuv420p',
        '-t', f'{duration:.3f}',
        '-video_track_timescale', '25000',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest', out_mp4_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    label_offsets = [(-15, -46), (16, 18), (-15, -46), (16, 18)]

    for f_idx in range(total_frames):
        prog = min(1.0, f_idx / max(1.0, total_frames * 0.78))
        frame = bg_img.copy()
        d = ImageDraw.Draw(frame, 'RGBA')

        if len(dense_path) > 1:
            d.line(dense_path, fill=(255, 255, 255, 80), width=3)

        n_pts = max(2, int(round(prog * len(dense_path))))
        active_pts = dense_path[:n_pts]
        if len(active_pts) > 1:
            d.line(active_pts, fill=(255, 140, 20, 115), width=11)
            d.line(active_pts, fill=(255, 205, 55, 255), width=4)

        for w_i, (wx, wy, w_title, w_alt) in enumerate(wp_coords):
            x_off, y_off = label_offsets[w_i % len(label_offsets)]
            d.ellipse([wx - 9, wy - 9, wx + 9, wy + 9], fill=(20, 30, 40, 235), outline=(255, 205, 65, 255), width=3)
            label_txt = f"{w_title} ({w_alt})"
            box_w = int(len(label_txt) * 9.5 + 18)
            bx0 = max(40, min(W - box_w - 40, wx + x_off))
            by0 = wy + y_off
            d.rounded_rectangle([bx0, by0, bx0 + box_w, by0 + 28], radius=5, fill=(10, 16, 22, 230), outline=(255, 195, 55, 190), width=1)
            d.text((bx0 + 8, by0 + 4), label_txt, fill=(255, 255, 255, 255), font=f_wp)

        hx, hy = active_pts[-1]
        pulse = 14 + int(5 * math.sin(f_idx * 0.45))
        d.ellipse([hx - pulse, hy - pulse, hx + pulse, hy + pulse], fill=(255, 160, 30, 95), outline=(255, 220, 90, 225), width=2)
        d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=(255, 70, 25, 255), outline=(255, 255, 255, 255), width=2)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    return out_mp4_path
