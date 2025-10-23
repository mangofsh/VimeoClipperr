import os
import json
import time
import asyncio
import subprocess
import logging
from deepgram import Deepgram
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise EnvironmentError("❌ Missing DEEPGRAM_API_KEY in .env")

dg = Deepgram(DEEPGRAM_API_KEY)

# -------------------------------------------------------------------
# Helper: Check if ffmpeg is installed
# -------------------------------------------------------------------

def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False


# -------------------------------------------------------------------
# Async transcription function
# -------------------------------------------------------------------

async def deepgram_async_transcribe(audio_path: str):
    """Handles the actual Deepgram API async call"""
    with open(audio_path, "rb") as f:
        buffer = f.read()

    logger.info(f"🚀 Uploading {audio_path} to Deepgram (awaited async call)...")

    response = await dg.transcription.prerecorded(
        {"buffer": buffer, "mimetype": "audio/mp4"},
        {
            "model": "nova-3",
            "smart_format": True,
            "punctuate": True,
            "paragraphs": True,
            "utterances": True,
            "diarize": True,
            "filler_words": True,
            "detect_entities": True,
        },
    )

    logger.info("✅ Deepgram transcription complete (async)")
    return response


# -------------------------------------------------------------------
# Main function
# -------------------------------------------------------------------

def transcribe_audio(file_path: str) -> str:
    """
    Extracts audio (if needed), uploads to Deepgram asynchronously,
    and saves both JSON + plain text transcripts.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    if not check_ffmpeg_installed():
        raise EnvironmentError("❌ FFmpeg not found. Please install FFmpeg and add it to PATH.")

    file_size = os.path.getsize(file_path)
    logger.info(f"🎧 Starting transcription for {file_path} ({round(file_size / 1_000_000, 2)} MB)")

    # ----------------------------------------------------------------
    # STEP 1: Extract audio from .mp4 (if needed)
    # ----------------------------------------------------------------
    base, ext = os.path.splitext(file_path)
    audio_path = f"{base}_audio.m4a"

    if ext.lower() == ".mp4":
        logger.info(f"🎬 Extracting audio from video → {audio_path}")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", file_path, "-vn", "-acodec", "aac", audio_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info("✅ Audio extraction complete")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ FFmpeg failed: {e.stderr.decode(errors='ignore')}")
            raise RuntimeError("Audio extraction failed — check FFmpeg installation or video file integrity.")
    else:
        logger.info("📁 File already audio; skipping extraction")
        audio_path = file_path

    # ----------------------------------------------------------------
    # STEP 2: Run Deepgram transcription (async)
    # ----------------------------------------------------------------
    try:
        response = asyncio.run(deepgram_async_transcribe(audio_path))
    except Exception as e:
        logger.exception(f"❌ Deepgram transcription failed: {e}")
        raise

    # ----------------------------------------------------------------
    # STEP 3: Save JSON + plain text
    # ----------------------------------------------------------------
    json_path = "transcript.json"
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(response, jf, indent=4)
        logger.info(f"🧾 Transcript JSON saved → {json_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save transcript JSON: {e}")

    # Build readable speaker transcript
    try:
        words = response["results"]["channels"][0]["alternatives"][0].get("words", [])
        lines, spk, current = [], None, []

        for w in words:
            speaker, word = w.get("speaker"), w.get("word")
            if spk is None:
                spk = speaker
            if speaker != spk:
                lines.append(f"Speaker {spk}: " + " ".join(current))
                spk, current = speaker, [word]
            else:
                current.append(word)
        if current:
            lines.append(f"Speaker {spk}: " + " ".join(current))

        txt_path = "transcript_output.txt"
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("\n".join(lines))
        logger.info(f"✅ Transcript TXT saved → {txt_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to build text transcript: {e}")
        txt_path = None

    # ----------------------------------------------------------------
    # STEP 4: Cleanup temp files
    # ----------------------------------------------------------------
    if audio_path != file_path:
        try:
            os.remove(audio_path)
            logger.info(f"🧹 Removed temp file → {audio_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete temp file: {e}")

    return txt_path or json_path
