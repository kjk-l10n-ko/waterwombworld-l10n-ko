#!/usr/bin/env python3
"""
Build Korean font injection pipeline for Water Womb World.

Reads original font glyph tables and texture pages, renders Hangul syllables
from Galmuri pixel fonts, packs them into extended texture pages, and outputs
new PNG + CSV for each font.

Output:
  /tmp/water/font_export/{font}_new.png
  /tmp/water/font_export/{font}_new_glyphs.csv
  Water Womb World/out/{font}_new.png
  Water Womb World/out/{font}_new_glyphs.csv
"""

from PIL import Image, ImageDraw, ImageFont
import csv
import os
import time
from collections import namedtuple

# ── Paths ─────────────────────────────────────────────────────────────
FONTWORK = "/tmp/water/font_export"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
FONT_DIR = os.path.join(PROJECT_DIR, "assets", "fonts", "galmuri")
OUT_DIR = os.path.join(PROJECT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)

Glyph = namedtuple("Glyph", ["cp", "srcX", "srcY", "srcW", "srcH", "shift", "offset"])

# ── Font configuration ────────────────────────────────────────────────
FONT_CFG = {
    # (cell_w, cell_h, baseline_y, galmuri, pt)
    # baseline_y: row (0-indexed from top) where Latin baseline sits.
    #   Hangul syllable bottom aligns to this.
    #   Typically cell_h - descender_room (2-4px for Latin descenders).
    #
    "fnt_dialogue":        (8,  17,  15,  "Galmuri7.ttf",  12),
    "fnt_computer":        (8,  17,  15,  "Galmuri7.ttf",  12),
    "fnt_smallcomputer":   (7,  14,  12,  "Galmuri7.ttf",  10),
    "fnt_gothic":          (8,  17,  15,  "Galmuri7.ttf",  12),
    "fnt_gothic_patron_1": (8,  17,  15,  "Galmuri7.ttf",  12),
    "fntMain":             (8,  17,  15,  "Galmuri7.ttf",  12),
    "fntValue":            (8,  17,  15,  "Galmuri7.ttf",  12),
    # Medium
    "fnt_gothic_patron_2": (10, 21,  18,  "Galmuri9.ttf",  14),
    "fnt_gm_15":           (12, 25,  22,  "Galmuri9.ttf",  14),
    "fnt_gothic_patron_3": (13, 25,  22,  "Galmuri9.ttf",  14),
    "fntTop":              (16, 24,  21,  "Galmuri11.ttf", 14),
    "fnt_biggothic":       (16, 33,  29,  "Galmuri11.ttf", 16),
    "fnt_gothic_patron_4": (15, 30,  26,  "Galmuri11.ttf", 16),
    # Large
    "fnt_debug":           (16, 32,  28,  "Galmuri11.ttf", 16),
    "fnt_gm_20":           (16, 31,  27,  "Galmuri11.ttf", 16),
    "fnt_gm_30":           (22, 46,  41,  "Galmuri14.ttf", 22),
    "fnt_button":          (26, 52,  46,  "Galmuri14.ttf", 24),
}

# Fallback fonts for missing glyphs
FALLBACK_FONTS = [
    "Galmuri14.ttf",
    "Galmuri11.ttf",
    "Galmuri11-Bold.ttf",
    "Galmuri9.ttf",
    "Galmuri7.ttf",
]

HANGUL_START = 0xAC00
HANGUL_END = 0xD7A4  # 11172 modern Hangul syllables

TEX_WIDTH = 2048
TEX_MAX_WIDTH = 4096  # allow wider pages for large-cell fonts
TEX_MAX_HEIGHT = 4096
ROW_GAP = 2


# ── Hangul charset scanner ──────────────────────────────────────────

def compute_hangul_charset(project_dir):
    """Scan project files for used Hangul syllables and merge with KS X 1001 basic set."""
    used = set()

    # Scan www_ko.yarn
    yarn_path = os.path.join(project_dir, "www_ko.yarn")
    if os.path.exists(yarn_path):
        with open(yarn_path, encoding="utf-8") as f:
            text = f.read()
        for ch in text:
            if 0xAC00 <= ord(ch) <= 0xD7A3:
                used.add(ord(ch))

    # Scan ui_strings.tsv and the inline Korean in apply_strings.csx
    for rel in ("ui_strings.tsv", os.path.join("tools", "apply_strings.csx")):
        p = os.path.join(project_dir, rel)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for ch in f.read():
                    if 0xAC00 <= ord(ch) <= 0xD7A3:
                        used.add(ord(ch))

    # Real KS X 1001 Hangul (2350 syllables) via the EUC-KR table, rows 0xB0..0xC8
    for lead in range(0xB0, 0xC9):
        for trail in range(0xA1, 0xFF):
            try:
                used.add(ord(bytes([lead, trail]).decode("euc-kr")))
            except UnicodeDecodeError:
                pass

    hangul_cps = sorted(used)
    total_full = 0xD7A4 - 0xAC00  # 11172
    print(f"Hangul charset: {len(hangul_cps)} syllables (from used text + KS X 1001, vs {total_full} full set)")
    return hangul_cps


# ── Helpers ───────────────────────────────────────────────────────────

def read_glyphs(csv_path):
    """Read glyph CSV into list of Glyph namedtuples."""
    glyphs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            glyphs.append(Glyph(
                int(row["char"]), int(row["srcX"]), int(row["srcY"]),
                int(row["srcW"]), int(row["srcH"]), int(row["shift"]), int(row["offset"]),
            ))
    return glyphs


def write_glyphs(csv_path, glyphs):
    """Write glyph list to CSV."""
    with open(csv_path, "w", newline="") as f:
        f.write("char;srcX;srcY;srcW;srcH;shift;offset\n")
        for g in glyphs:
            f.write(f"{g.cp};{g.srcX};{g.srcY};{g.srcW};{g.srcH};{g.shift};{g.offset}\n")


# Galmuri is a pixel font: only crisp at size = unitsPerEm/100 (or an integer multiple).
NATIVE = {"Galmuri7.ttf": 8, "Galmuri9.ttf": 10, "Galmuri11.ttf": 12, "Galmuri14.ttf": 15}


def pick_font(cell_h):
    """Choose (file, native size, integer scale) so Hangul height is ~75% of cell_h."""
    best = None
    for name, em in NATIVE.items():
        for k in (1, 2, 3):
            if em * k > cell_h * 0.75:
                continue
            score = em * k - (k - 1) * 3  # prefer unscaled
            if best is None or score > best[0]:
                best = (score, name, em, k)
    if best is None:  # cell narrower than the smallest font: use it anyway, advance handles spacing
        return "Galmuri7.ttf", 8, 1
    return best[1], best[2], best[3]


def batch_render_hangul(font, cell_w, cell_h, baseline_y, cps, scale=1):
    """Render each syllable at native pixel size, upscale by integer `scale` (NEAREST),
    baseline-aligned, horizontally centred. Returns {cp: rows[cell_h][cell_w]}.
    """
    result = {}
    nw, nh, nb = -(-cell_w // scale) + 2, -(-cell_h // scale), baseline_y // scale
    for cp in cps:
        ch = chr(cp)
        x = 0 if cp < 0x3000 else max(0, (nw - round(font.getlength(ch))) // 2)  # Latin left-aligned, Hangul centred
        img = Image.new("L", (nw, nh), 0)
        ImageDraw.Draw(img).text((x, nb), ch, font=font, fill=255, anchor="ls")
        if scale > 1:
            img = img.resize((nw * scale, nh * scale), Image.NEAREST)
        px = img.load()
        w, h = img.size
        result[cp] = [[px[ix, iy] if ix < w and iy < h else 0 for ix in range(cell_w)] for iy in range(cell_h)]
    print(f"    {len(cps)} rendered")
    return result


def pack_positions(n, cell_w, cell_h, gap=2, max_w=TEX_WIDTH, max_h=TEX_MAX_HEIGHT, y_offset=0):
    """Compute (x, y) positions for n fixed-size glyphs using row packing.
    
    Tries to fit within max_w x max_h by widening the texture page if needed.
    y_offset: vertical offset to skip (e.g. original texture height).
    Returns (positions, total_width, total_height).
    """
    widths_to_try = [w for w in [max_w, 4096, TEX_MAX_WIDTH] if w <= TEX_MAX_WIDTH]
    for width in widths_to_try:
        per_row = (width - gap) // (cell_w + 3)
        if per_row < 1:
            per_row = 1
        rows_total = (n + per_row - 1) // per_row
        total_height = rows_total * (cell_h + gap) + gap
        if total_height <= max_h - y_offset or width >= TEX_MAX_WIDTH:
            break
    
    positions = []
    for i in range(n):
        col = i % per_row
        row_n = i // per_row
        x = col * (cell_w + 3) + gap
        y = row_n * (cell_h + gap) + gap + y_offset
        positions.append((x, y))
    
    return positions, width, total_height


def build_new_texture(orig_tex_path, hangul_rendered,
                       hangul_positions, cell_w, cell_h, tex_w, tex_h):
    """Build the new extended texture page.
    
    Preserves original Latin glyphs, appends packed Hangul rows below.
    hangul_positions Y coordinates already include orig_h offset.
    tex_w, tex_h are just the Hangul-packed area dimensions.
    """
    orig_tex = Image.open(orig_tex_path).convert("RGBA") if orig_tex_path else None
    
    if orig_tex:
        orig_w, orig_h = orig_tex.size
        new_w = max(orig_w, tex_w)
        new_h = orig_h + tex_h + 4  # original content + packed hangul + gap
    else:
        new_w = tex_w
        new_h = tex_h
    
    if new_h > TEX_MAX_HEIGHT:
        print(f"  WARNING: texture height {new_h} > {TEX_MAX_HEIGHT}, capping at {TEX_MAX_HEIGHT}")
        new_h = TEX_MAX_HEIGHT
    
    new_tex = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    if orig_tex:
        new_tex.paste(orig_tex, (0, 0))
    
    for (gx, gy), alpha_rows in zip(hangul_positions, hangul_rendered):
        glyph_img = Image.new("L", (cell_w, cell_h), 0)
        for y in range(cell_h):
            for x in range(cell_w):
                if y < len(alpha_rows) and x < len(alpha_rows[y]):
                    glyph_img.putpixel((x, y), alpha_rows[y][x])
        
        rgba = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 0))
        rgba.putalpha(glyph_img)
        new_tex.paste(rgba, (gx, gy), rgba)
    
    return new_tex


def process_font(font_name, hangul_cps):
    """Process a single font: read original data, build Hangul glyphs, write output."""
    print(f"\n{'='*60}")
    print(f"Processing: {font_name}")
    print(f"{'='*60}")
    
    cfg = FONT_CFG[font_name]
    cell_w, cell_h, baseline_y, _, _ = cfg
    galmuri_file, pt, scale = pick_font(cell_h)
    cell_w = max(cell_w, pt * scale + 2)  # Hangul wider than the Latin cell; advance is per-glyph
    
    # ── Load original data ──
    csv_path = os.path.join(FONTWORK, f"{font_name}_glyphs.csv")
    tex_path = os.path.join(FONTWORK, "EmbeddedTextures", f"{font_name}_texture.png")
    # Glyph coords are relative to the font's page item inside a shared atlas page:
    # crop that region so the new texture (SourceX/Y=0) keeps coords valid.
    pi = open(os.path.join(FONTWORK, f"{font_name}_pageitem.txt")).read().split(";")
    px, py, pw, ph = (int(v) for v in pi[:4])
    region_path = os.path.join(FONTWORK, "EmbeddedTextures", f"{font_name}_region.png")
    Image.open(tex_path).crop((px, py, px + pw, py + ph)).save(region_path)
    tex_path = region_path
    
    if not os.path.exists(csv_path):
        print(f"  SKIP: {csv_path} not found")
        return
    
    orig_glyphs = read_glyphs(csv_path)
    print(f"  Original: {len(orig_glyphs)} glyphs, cell={cell_w}x{cell_h}, baseline_y={baseline_y}")
    
    if not os.path.exists(tex_path):
        print(f"  WARN: original texture not found at {tex_path}")
        tex_path = None
    
    # ── Load Galmuri font ──
    font_path = os.path.join(FONT_DIR, galmuri_file)
    if not os.path.exists(font_path):
        print(f"  ERROR: Font not found: {font_path}")
        return
    
    font = ImageFont.truetype(font_path, pt)
    print(f"  Font: {galmuri_file} @ {pt}pt (baseline at row {baseline_y}/{cell_h})")

    # One typeface: re-render the ASCII glyphs from Galmuri too, so Latin/digits share
    # Hangul's baseline and style. Other original glyphs (symbols/PUA) are kept.
    latin_cps = [g.cp for g in orig_glyphs if 0x20 <= g.cp <= 0x7E]
    orig_glyphs = [g for g in orig_glyphs if g.cp not in set(latin_cps)]
    hangul_cps = latin_cps + list(hangul_cps)
    
    # ── Render Hangul ──
    print(f"  Rendering {len(hangul_cps)} Hangul syllables (batch)...")
    
    t0 = time.time()
    rendered = batch_render_hangul(font, cell_w, cell_h, baseline_y, hangul_cps, scale)
    elapsed = time.time() - t0
    print(f"  Batch render: {len(rendered)} glyphs in {elapsed:.1f}s ({len(rendered)/elapsed:.0f} glyphs/s)")
    
    # Check for missing (totally blank) glyphs
    missing = []
    for cp in hangul_cps:
        rows = rendered[cp]
        has_ink = any(any(v > 30 for v in row) for row in rows)
        if not has_ink:
            missing.append(cp)
    
    if missing:
        print(f"  Missing in primary font: {len(missing)} — trying fallbacks...")
        # Try fallback fonts
        for fallback_name in FALLBACK_FONTS:
            if fallback_name == galmuri_file:
                continue
            fb_path = os.path.join(FONT_DIR, fallback_name)
            if not os.path.exists(fb_path):
                continue
            try:
                fb_font = ImageFont.truetype(fb_path, pt)
            except:
                continue
            
            still_missing = [cp for cp in missing if cp in hangul_cps]
            if not still_missing:
                break
            
            fb_result = batch_render_hangul(fb_font, cell_w, cell_h, baseline_y, still_missing, scale)
            for cp in still_missing:
                if cp in fb_result:
                    rows = fb_result[cp]
                    if any(any(v > 30 for v in row) for row in rows):
                        rendered[cp] = rows
                        missing.remove(cp)
            
            print(f"    {fallback_name}: remaining missing = {len(missing)}")
            if not missing:
                break
    
    if missing:
        print(f"  Still missing: {len(missing)} (using blank)")
    
    # Order rendered into list matching hangul_cps
    rendered_list = [rendered[cp] for cp in hangul_cps]
    
    # ── Pack into texture (below original content) ──
    orig_h = Image.open(tex_path).size[1] if tex_path and os.path.exists(tex_path) else 0
    positions, tex_w, total_height = pack_positions(len(hangul_cps), cell_w, cell_h, ROW_GAP, y_offset=orig_h)
    print(f"  Packing: {len(positions)} glyphs below row {orig_h}, texture {tex_w}x~{orig_h + total_height + 4}px")
    
    # ── Build new texture ──
    new_tex = build_new_texture(
        tex_path, rendered_list, positions,
        cell_w, cell_h, tex_w, total_height
    )
    
    print(f"  New texture: {new_tex.size}")
    
    # ── Build new glyph list ──
    # Original Latin glyphs (positions preserved — they're unchanged in new texture)
    new_glyphs = list(orig_glyphs)
    
    for idx, cp in enumerate(hangul_cps):
        gx, gy = positions[idx]
        rows = rendered_list[idx]
        
        # Compute ink bounding box within the cell
        ink_x0, ink_y0, ink_x1, ink_y1 = cell_w, cell_h, 0, 0
        for y in range(cell_h):
            for x in range(cell_w):
                if rows[y][x] > 20:
                    if x < ink_x0: ink_x0 = x
                    if y < ink_y0: ink_y0 = y
                    if x + 1 > ink_x1: ink_x1 = x + 1
                    if y + 1 > ink_y1: ink_y1 = y + 1
        
        if cp < 0x3000:
            adv = round(font.getlength(chr(cp))) * scale + scale  # proportional-ish pixel advance
        else:
            adv = None
        if ink_x1 <= ink_x0 or ink_y1 <= ink_y0:
            # Blank glyph (space-like)
            new_glyphs.append(Glyph(cp, gx, gy, cell_w, cell_h, adv or cell_w, 0))
        else:
            ink_w = ink_x1 - ink_x0
            advance = adv or max(ink_w + 2, cell_w)
            new_glyphs.append(Glyph(
                cp,
                gx + ink_x0, gy,           # srcX = ink left, srcY = cell top: GM draws glyphs at line top,
                ink_w, cell_h,             # so keep full cell height to preserve vertical position
                advance,                   # shift: advance width
                0,                         # offset: left-aligned (JetLancer recipe)
            ))
    
    new_glyphs.sort(key=lambda g: g.cp)  # GameMaker expects glyphs ordered by character code
    # ── Write outputs ──
    for subdir in [FONTWORK, OUT_DIR]:
        os.makedirs(os.path.join(subdir), exist_ok=True)
        write_glyphs(os.path.join(subdir, f"{font_name}_new_glyphs.csv"), new_glyphs)
        new_tex.save(os.path.join(subdir, f"{font_name}_new.png"))
        print(f"  -> {subdir}/{font_name}_new.png + .csv")


def main():
    """Process all configured fonts."""
    hangul_cps = compute_hangul_charset(PROJECT_DIR)
    print("=" * 60)
    print("Water Womb World — Korean Font Builder")
    print(f"Fonts: {len(FONT_CFG)}, Hangul: {len(hangul_cps)} syllables")
    print("=" * 60)
    
    for font_name in sorted(FONT_CFG):
        process_font(font_name, hangul_cps)
    
    print(f"\n{'='*60}")
    print("All fonts processed successfully.")
    print(f"Total Hangul syllables rendered: {len(hangul_cps)} (full set: {HANGUL_END - HANGUL_START})")
    print(f"Reduction: {(1 - len(hangul_cps) / (HANGUL_END - HANGUL_START)) * 100:.0f}% fewer glyphs")
    print(f"Max texture dimension: {TEX_MAX_HEIGHT}x{TEX_MAX_HEIGHT}px (capped)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()