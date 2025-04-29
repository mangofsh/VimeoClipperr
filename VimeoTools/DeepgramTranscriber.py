import random, json, os
from deepgram import DeepgramClient, PrerecordedOptions
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Ideally load from env: os.environ["DEEPGRAM_API_KEY"]
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]

def transcribe_audio(file_path: str) -> str:
    """
    Sends `file_path` to Deepgram, writes a JSON dump plus a plain‑text transcript.
    Returns the transcript TXT filename.
    """
    client = DeepgramClient(DEEPGRAM_API_KEY)
    with open(file_path, "rb") as f:
        buffer = f.read()

    opts = PrerecordedOptions(
        model="nova-3",
        language="en",
        detect_entities=True,
        smart_format=True,
        punctuate=True,
        paragraphs=True,
        utterances=True,
        diarize=True,
        filler_words=True,
    )

    resp = client.listen.rest.v("1").transcribe_file({"buffer": buffer}, opts, timeout=300)

    # save JSON (optional)
    json_fn = f"transcript.json"
    with open(json_fn, "w", encoding="utf-8") as j:
        j.write(resp.to_json(indent=4))

    # build a simple “Speaker X: …” transcript
    words = resp.to_dict()["results"]["channels"][0]["alternatives"][0]["words"]
    lines, cur_spk, cur_words = [], None, []
    for w in words:
        spk, wd = w["speaker"], w["word"]
        if cur_spk is None:
            cur_spk = spk
        if spk != cur_spk:
            lines.append(f"Speaker {cur_spk}: " + " ".join(cur_words))
            cur_spk, cur_words = spk, [wd]
        else:
            cur_words.append(wd)
    if cur_words:
        lines.append(f"Speaker {cur_spk}: " + " ".join(cur_words))

    txt_fn = "transcript_output.txt"
    with open(txt_fn, "w", encoding="utf-8") as t:
        t.write("\n".join(lines))

    print(f"✅ Transcript written to {txt_fn}")
    return txt_fn
