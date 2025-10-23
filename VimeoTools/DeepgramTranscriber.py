import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from deepgram import Deepgram
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_DEEPGRAM_CLIENT: Optional[Deepgram] = None


def _get_deepgram_client() -> Deepgram:
    """Return a cached Deepgram client instance."""
    global _DEEPGRAM_CLIENT
    if _DEEPGRAM_CLIENT is not None:
        return _DEEPGRAM_CLIENT

    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing DEEPGRAM_API_KEY in environment configuration.")

    _DEEPGRAM_CLIENT = Deepgram(api_key)
    return _DEEPGRAM_CLIENT


# -------------------------------------------------------------------
# Helper: Check if ffmpeg is installed
# -------------------------------------------------------------------

def check_ffmpeg_installed() -> bool:
    """Return True when ffmpeg is available on PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


# -------------------------------------------------------------------
# Async transcription function
# -------------------------------------------------------------------

async def deepgram_async_transcribe(audio_path: str, mimetype: str = "audio/mp4") -> Dict[str, Any]:
    """Handles the actual Deepgram API async call."""
    client = _get_deepgram_client()

    with open(audio_path, "rb") as f:
        buffer = f.read()

    logger.info("Uploading %s to Deepgram (awaited async call)...", audio_path)

    response = await client.transcription.prerecorded(
        {"buffer": buffer, "mimetype": mimetype},
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

    logger.info("Deepgram transcription complete (async).")
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
        raise FileNotFoundError(f"File not found: {file_path}")

    if not check_ffmpeg_installed():
        raise EnvironmentError("FFmpeg not found. Please install FFmpeg and add it to PATH.")

    file_size = os.path.getsize(file_path)
    logger.info(
        "Starting transcription for %s (%.2f MB)",
        file_path,
        round(file_size / 1_000_000, 2),
    )

    base, ext = os.path.splitext(file_path)
    audio_path = file_path
    cleanup_audio = False

    if ext.lower() == ".mp4":
        audio_path = f"{base}_audio.m4a"
        logger.info("Extracting audio from video to %s", audio_path)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", file_path, "-vn", "-acodec", "aac", audio_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            cleanup_audio = True
            logger.info("Audio extraction complete.")
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg failed: %s", e.stderr.decode(errors="ignore"))
            raise RuntimeError(
                "Audio extraction failed - check FFmpeg installation or video file integrity."
            ) from e

    # STEP 2: Run Deepgram transcription (async)
    try:
        response = asyncio.run(deepgram_async_transcribe(audio_path))
    except Exception as e:  # noqa: BLE001 - propagate descriptive message
        logger.exception("Deepgram transcription failed: %s", e)
        raise

    # STEP 3: Save JSON + plain text
    json_path = "transcript.json"
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(response, jf, indent=4)
        logger.info("Transcript JSON saved to %s", json_path)
    except Exception as e:  # noqa: BLE001 - log and continue
        logger.error("Failed to save transcript JSON: %s", e)

    txt_path: Optional[str] = None
    try:
        alternatives: List[Dict[str, Any]] = response["results"]["channels"][0]["alternatives"]
        words = alternatives[0].get("words", []) if alternatives else []
        lines: List[str] = []
        current_speaker: Optional[int] = None
        buffer: List[str] = []

        for word_info in words:
            speaker = word_info.get("speaker")
            word = word_info.get("word")
            if speaker is None or word is None:
                continue

            if current_speaker is None:
                current_speaker = speaker

            if speaker != current_speaker:
                lines.append(f"Speaker {current_speaker}: " + " ".join(buffer))
                buffer = [word]
                current_speaker = speaker
            else:
                buffer.append(word)

        if buffer and current_speaker is not None:
            lines.append(f"Speaker {current_speaker}: " + " ".join(buffer))

        txt_path = "transcript_output.txt"
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("\n".join(lines))
        logger.info("Transcript TXT saved to %s", txt_path)
    except Exception as e:  # noqa: BLE001 - log and continue
        logger.warning("Failed to build text transcript: %s", e)

    # STEP 4: Cleanup temp files
    if cleanup_audio:
        try:
            os.remove(audio_path)
            logger.info("Removed temp file %s", audio_path)
        except Exception as e:  # noqa: BLE001 - log and continue
            logger.warning("Could not delete temp file %s: %s", audio_path, e)

    return txt_path or json_path
