#!/usr/bin/env bash
# Water Womb World — Korean font injection build script
# Usage: GAME=/path/to/game/dir bash scripts/build.sh
# Default GAME: /mnt/s/Installation/Steam/steamapps/common/Water Womb World
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/out"

# ---- Configurable paths ----
GAME="${GAME:-/mnt/s/Installation/Steam/steamapps/common/Water Womb World}"
DATA_WIN="$GAME/data.win"
UTMT="/tmp/utmt/UndertaleModCli"
FONTWORK="/tmp/water/font_export"
WORKDIR="/tmp/water"

# ---- Prerequisites ----
echo "=== Checking prerequisites ==="

if [ ! -x "$UTMT" ]; then
    echo "ERROR: UTMT CLI not found at $UTMT"
    echo "Extract UTMT to /tmp/utmt/ first"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

if ! python3 -c "from PIL import Image" 2>/dev/null; then
    echo "ERROR: Python Pillow not installed (pip install Pillow)"
    exit 1
fi

if ! python3 -c "from fonttools.ttLib import TTFont" 2>/dev/null; then
    echo "WARNING: fonttools not installed; build_fonts.py may fail"
    echo "  Run: pip install fonttools"
fi

if [ ! -f "$DATA_WIN" ]; then
    echo "ERROR: data.win not found at $DATA_WIN"
    echo "  Set GAME env var to the game directory containing data.win"
    exit 1
fi

if [ ! -f "$ROOT/scripts/build_fonts.py" ]; then
    echo "ERROR: scripts/build_fonts.py not found"
    echo "  This script is generated separately."
    exit 1
fi

if [ ! -f "$ROOT/scripts/inject_fonts.csx" ]; then
    echo "ERROR: scripts/inject_fonts.csx not found"
    exit 1
fi

echo "  All prerequisites met."
echo ""

# ---- Setup ----
echo "=== Setting up working directory ==="
mkdir -p "$WORKDIR" "$FONTWORK" "$OUT"
# 게임 폴더가 이미 패치되었으면 설치기가 만든 백업(원본, kor_bak)을 쓴다
BAK="$GAME/kor_bak"
if [ -f "$BAK/data.win" ]; then
  echo "  Using pristine backup: $BAK/data.win size=$(stat -c%s "$BAK/data.win")"
  cp "$BAK/data.win" "$WORKDIR/data.win"
elif [ -f "$DATA_WIN" ]; then
  cp "$DATA_WIN" "$WORKDIR/data.win"
  echo "  Pristine data.win copied from game dir ($(stat -c%s "$WORKDIR/data.win") bytes)"
else
  echo "ERROR: data.win not found"
  exit 1
fi
echo "  Pristine data.win copied ($(stat -c%s "$WORKDIR/data.win") bytes)"
echo ""

# ---- Export original font data ----
echo "=== Step 1: Export original glyphs and textures ==="
export FONTWORK_DIR="$FONTWORK"
"$UTMT" load "$WORKDIR/data.win" \
    -s "$ROOT/scripts/export_font_data.csx" \
    -o "$WORKDIR/data.win" \
    -f 2>&1 | grep -v '^Wall time:'
echo ""

# ---- Generate new textures with Hangul ----
echo "=== Step 2: Generate new font textures with Hangul ==="
python3 "$ROOT/scripts/build_fonts.py" "$FONTWORK" 2>&1
echo ""

# ---- Inject new fonts into data.win ----
echo "=== Step 3: Inject new font data ==="
"$UTMT" load "$WORKDIR/data.win" \
    -s "$ROOT/scripts/inject_fonts.csx" \
    -o "$OUT/data.win" \
    -f 2>&1 | grep -v '^Wall time:'
echo ""

# ---- Apply UI string translations ----
echo "=== Step 3.5: Apply UI string translations ==="
export UI_STRINGS_TSV="$ROOT/legacy/ui_strings.tsv"
"$UTMT" load "$OUT/data.win" \
    -s "$ROOT/scripts/apply_strings.csx" \
    -o "$OUT/data.win" \
    -f 2>&1 | grep -v '^Wall time:'
echo ""

echo "=== Step 4: Copy Korean dialogue ==="
if [ -f "$ROOT/legacy/www_ko.yarn" ]; then
    cp "$ROOT/legacy/www_ko.yarn" "$OUT/www.yarn"
    echo "  Copied legacy/www_ko.yarn -> $OUT/www.yarn"
else
    echo "  SKIP: legacy/www_ko.yarn not found"
fi
echo ""

# ---- Verify ----
echo "=== Step 5: Verification ==="
"$UTMT" load "$OUT/data.win" \
    -s "$ROOT/scripts/verify.csx" \
    -o /dev/null 2>&1 | grep -v '^Wall time:'
echo ""

DATA_SIZE=$(stat -c%s "$OUT/data.win" 2>/dev/null || echo "?")
YARN_SIZE=$(stat -c%s "$OUT/www.yarn" 2>/dev/null || echo "?")
echo "=== Build complete ==="
echo "  Output:"
echo "    $OUT/data.win  ($DATA_SIZE bytes)"
echo "    $OUT/www.yarn  ($YARN_SIZE bytes)"
echo "  Install: bash scripts/build_installer.sh  (설치기 exe 생성; 직접 복사하지 말 것)"