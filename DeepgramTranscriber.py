'''
import os
import random
import json
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

# Path to the audio file and Deepgram API key
AUDIO_FILE = "C:/Users/4iakh/OneDrive/Desktop/GMNG/896729164_sd_240p.mp4"
DEEPGRAM_API_KEY = "b11dabc7477c289a7934bdb3d11f369257ae64e2"

def transcribe_audio():
    """
    Creates a Deepgram client and transcribes the audio file.
    Returns the Deepgram response object.
    """
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    
        # Read the audio file as binary data
        with open(AUDIO_FILE, "rb") as file:
            buffer_data = file.read()
    
        payload: FileSource = {
            "buffer": buffer_data,
        }
    
        # Set up transcription options
        options = PrerecordedOptions(
            model="nova-2",
            language="en",
            summarize="v2",
            detect_entities=True,
            smart_format=True,
            punctuate=True,
            paragraphs=True,
            utterances=True,
            diarize=True,
            sentiment=True,
        )
    
        # Transcribe the audio file using Deepgram
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options, timeout=300)
        return response
    except Exception as e:
        print(f"Exception during transcription: {e}")
        return None

def process_transcription(transcription_data):
    """
    Processes the Deepgram JSON transcription data to group words into speaker turns.
    Writes the final transcript to a text file.
    """
    try:
        # 'transcription_data' should be a dictionary containing the Deepgram response.
        # Extract the list of words with speaker tags
        words = transcription_data["results"]["channels"][0]["alternatives"][0]["words"]
    
        # Variables to build the transcript by speaker
        current_speaker = None
        current_words = []
        output_lines = []
    
        for word_obj in words:
            speaker = word_obj["speaker"]
            word = word_obj["word"]
    
            # Initialize the current speaker on the first word
            if current_speaker is None:
                current_speaker = speaker
    
            # When speaker changes, append the current speaker's line and reset the accumulator
            if speaker != current_speaker:
                output_lines.append(f"Speaker {current_speaker}: " + " ".join(current_words))
                current_words = [word]
                current_speaker = speaker
            else:
                current_words.append(word)
    
        # Append any remaining words from the last speaker turn
        if current_words:
            output_lines.append(f"Speaker {current_speaker}: " + " ".join(current_words))
    
        # Write the final output to a text file
        output_filename = "transcript_output.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        print(f"Transcription has been processed and saved to {output_filename}")
    except Exception as e:
        print(f"Exception during transcription processing: {e}")

def main():
    # Transcribe the audio file using Deepgram
    response = transcribe_audio()
    if response is not None:
        # Convert the Deepgram response to a JSON string
        response_json_str = response.to_json(indent=4)
        
        # Optionally, save the full JSON transcription to a file with a random prefix
        random_number = random.randint(1, 100000)
        transcript_filename = f"{random_number}_transcript.json"
        with open(transcript_filename, "w", encoding="utf-8") as outfile:
            outfile.write(response_json_str)
        print(f"Transcription JSON saved to {transcript_filename}")
        
        # Parse the JSON string to a dictionary for processing
        transcription_data = json.loads(response_json_str)
        process_transcription(transcription_data)
    else:
        print("Transcription failed.")

if __name__ == "__main__":
    main()
'''

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
        model="nova-2",
        language="en",
        summarize="v2",
        detect_entities=True,
        smart_format=True,
        punctuate=True,
        paragraphs=True,
        utterances=True,
        diarize=True,
        sentiment=True,
    )

    resp = client.listen.rest.v("1").transcribe_file({"buffer": buffer}, opts, timeout=300)

    # save JSON (optional)
    json_fn = f"{random.randint(1,99999)}_transcript.json"
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
