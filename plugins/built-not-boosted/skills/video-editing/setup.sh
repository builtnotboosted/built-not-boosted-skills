#!/usr/bin/env bash
# One-time setup for the video-editing tool. Safe to re-run: it only installs what is missing.
# Works on macOS and Linux; on Windows run it in WSL or Git Bash.
# Everything heavy lives in $VEDIT_HOME (default ~/.vedit), never in your project folders:
#   venv/   Python with a Whisper backend, numpy, Pillow, OpenCV (face checks), noisereduce
#   node/   Playwright + Chromium (motion graphics, page captures)
#   fonts/  Barlow Condensed + Inter (open licence), the default headline and caption faces
#   work/   one scratch folder per video
#
# Options (environment variables):
#   VEDIT_HOME=/path            where to install (default ~/.vedit)
#   VEDIT_WHISPER=openai        use openai-whisper instead of faster-whisper (default: faster)
#   VEDIT_SKIP_MODELS=1         don't pre-download the Whisper models now
#   VEDIT_MODELS="small.en base.en"   which models to pre-download (default "medium.en large-v3")
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VH="${VEDIT_HOME:-$HOME/.vedit}"
mkdir -p "$VH/work" "$VH/node" "$VH/fonts"

hint() {
  case "$1" in
    ffmpeg|ffprobe)
      if command -v brew >/dev/null; then echo "brew install ffmpeg";
      elif command -v apt-get >/dev/null; then echo "sudo apt-get install -y ffmpeg";
      elif command -v dnf >/dev/null; then echo "sudo dnf install -y ffmpeg";
      elif command -v winget >/dev/null; then echo "winget install Gyan.FFmpeg";
      else echo "install ffmpeg from https://ffmpeg.org/download.html"; fi ;;
    node) echo "install Node.js 18+ from https://nodejs.org (or brew install node / apt-get install nodejs npm)" ;;
    python3) echo "install Python 3.10+ from https://python.org" ;;
  esac
}
missing=0
for b in ffmpeg ffprobe node npm python3; do
  if ! command -v "$b" >/dev/null 2>&1; then echo "MISSING: $b  ->  $(hint "$b")"; missing=1; fi
done
[ "$missing" = 0 ] || { echo "Install the missing tools above, then run this again."; exit 1; }

# --- Python venv ---------------------------------------------------------------------------------
if [ -x "$VH/venv/bin/python" ]; then PY="$VH/venv/bin/python";
elif [ -x "$VH/venv/Scripts/python.exe" ]; then PY="$VH/venv/Scripts/python.exe";
else
  echo "creating venv in $VH/venv"
  python3 -m venv "$VH/venv"
  if [ -x "$VH/venv/bin/python" ]; then PY="$VH/venv/bin/python"; else PY="$VH/venv/Scripts/python.exe"; fi
fi
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q "numpy>=1.26" "pillow>=10.1"
if [ "${VEDIT_WHISPER:-faster}" = "openai" ]; then
  "$PY" -m pip install -q "openai-whisper"
else
  "$PY" -m pip install -q "faster-whisper>=1.0" || {
    echo "faster-whisper failed to install; falling back to openai-whisper"; "$PY" -m pip install -q "openai-whisper"; }
fi
# OpenCV 4.10 (not 5.x, some builds of which ship without the face cascades): cover face check, lip-sync check
"$PY" -m pip install -q "opencv-python-headless==4.10.0.84" || echo "WARNING: OpenCV not installed (face checks will be skipped)"
# spectral noise gate for project "audio": {"denoise": "firm"}
"$PY" -m pip install -q "noisereduce>=3" || echo "WARNING: noisereduce not installed (audio.denoise unavailable)"

# --- Node + Playwright -----------------------------------------------------------------------------
cd "$VH/node"
[ -f package.json ] || npm init -y >/dev/null
[ -d node_modules/playwright ] || npm install --silent playwright
npx --yes playwright install chromium >/dev/null || echo "WARNING: Chromium download failed; run: cd $VH/node && npx playwright install chromium"

# --- Fonts (open licence, from the Google Fonts repository) ---------------------------------------
gf="https://github.com/google/fonts/raw/main/ofl"
for spec in \
  "BarlowCondensed-ExtraBold.ttf:$gf/barlowcondensed/BarlowCondensed-ExtraBold.ttf" \
  "BarlowCondensed-Bold.ttf:$gf/barlowcondensed/BarlowCondensed-Bold.ttf" \
  "BarlowCondensed-SemiBold.ttf:$gf/barlowcondensed/BarlowCondensed-SemiBold.ttf" \
  "Inter.ttf:$gf/inter/Inter%5Bopsz,wght%5D.ttf" ; do
  name="${spec%%:*}"; url="${spec#*:}"
  [ -f "$VH/fonts/$name" ] || curl -fsSL -o "$VH/fonts/$name" "$url" || echo "WARNING: could not fetch $name (set brand head_ttf/body_ttf to fonts you have)"
done

# --- Whisper models (cached by the backend; large-v3 is ~3 GB) -----------------------------------
if [ "${VEDIT_SKIP_MODELS:-0}" != "1" ]; then
  VEDIT_MODELS="${VEDIT_MODELS:-medium.en large-v3}" "$PY" - <<'PY' || echo "WARNING: model download failed; they will download on first use"
import os
names = os.environ["VEDIT_MODELS"].split()
try:
    from faster_whisper import WhisperModel
    for m in names: WhisperModel(m, device="cpu", compute_type="int8"); print("model ready:", m)
except ImportError:
    import whisper
    for m in names: whisper.load_model(m, device="cpu"); print("model ready:", m)
PY
fi

echo "video-editing tool ready in $VH"
echo "check it with:  python3 \"$SKILL_DIR/vedit.py\" doctor"
