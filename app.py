import json
from flask import Flask, render_template, request, jsonify
import os
import openai
from openai import OpenAI
from VimeoTools import deepgramTranscriber
import VimeoTools.videoDownloader
from VimeoTools.videoDownloader import download_video, fetch_metadata_as_string
from VimeoTools.deepgramTranscriber import transcribe_audio
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="MatchMakingUI", static_folder="static")

# Increase Flask's timeout
app.config['TIMEOUT'] = 300  # 5 minutes

load_dotenv()  # This loads the .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template(
        "bio_psycho_social_generator_clean.html",
    )

@app.route("/api/run_pipeline", methods=["POST"])
def run_pipeline():
    data = request.get_json()
    vid = data.get("video_id")
    if not vid:
        return jsonify(success=False, error="No video_id provided"), 400
    try:
        # Log start of process
        logger.info(f"Starting pipeline for video ID: {vid}")

        # Fetch metadata
        logger.info("Fetching metadata...")
        metadata = fetch_metadata_as_string(vid)
        logger.info("Metadata fetched successfully")

        # Download video
        logger.info("Downloading video...")
        video_file = download_video(vid)
        logger.info(f"Video downloaded: {video_file}")

        # Verify file exists and size
        if not os.path.exists(video_file):
            raise Exception(f"Video file not found: {video_file}")
        file_size = os.path.getsize(video_file)
        logger.info(f"Video file size: {file_size} bytes")

        # Transcribe audio with additional logging
        logger.info("Starting transcription...")
        try:
            # Verify Deepgram API key
            deepgram_key = os.getenv("DEEPGRAM_API_KEY")
            if not deepgram_key:
                raise Exception("DEEPGRAM_API_KEY not found in environment")
            logger.info("Deepgram API key found")
            
            transcript_file = transcribe_audio(video_file)
            if not transcript_file:
                raise Exception("Transcription failed - no transcript file returned")
            if not os.path.exists(transcript_file):
                raise Exception(f"Transcript file not found: {transcript_file}")
            logger.info("Transcription completed successfully")
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")

        # Read the transcript text
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript = f.read()
            logger.info(f"Transcript read successfully, length: {len(transcript)}")
        except Exception as e:
            logger.error(f"Error reading transcript file: {e}")
            raise

        # Clean up the video file after processing
        try:
            os.remove(video_file)
            logger.info("Cleaned up video file")
        except Exception as e:
            logger.warning(f"Could not remove video file: {e}")

        # Return both metadata and transcript
        return jsonify(success=True, transcript=transcript, metadata=metadata)
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        return jsonify(success=False, error=str(e)), 500

@app.route("/api/generate-profile", methods=["POST"])
def generate_profile():
    try:
        data = request.get_json()
        prompt_text = data.get("prompt")
        
        if not prompt_text:
            return jsonify({"error": "No prompt provided"}), 400
            
        completion = client.chat.completions.create(
            model="gpt-4",  # Fixed typo in model name from "gpt-4o"
            messages=[
                {"role": "system", "content": "You are an expert profile generation assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.4
        )
        
        content = completion.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        logger.error(f"Error generating profile: {str(e)}")
        return jsonify({"error": "Failed to generate profile"}), 500
        
if __name__ == "__main__":
    app.run(debug=True, threaded=True)