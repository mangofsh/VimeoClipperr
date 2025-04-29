import json
from flask import Flask, render_template, request, jsonify
import os
import openai
from openai import OpenAI
import VimeoTools.deepgramTranscriber
import VimeoTools.videoDownloader
from VimeoTools.videoDownloader import download_video, fetch_metadata_as_string
from VimeoTools.deepgramTranscriber import transcribe_audio
from dotenv import load_dotenv

app = Flask(__name__, template_folder="MatchMakingUI", static_folder="static")

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
        # Fetch metadata
        metadata = fetch_metadata_as_string(vid)

        # Download video
        video_file = download_video(vid)

        # Transcribe audio (pass the downloaded file path)
        transcript_file = transcribe_audio(video_file)
        if not transcript_file:
            raise Exception("Transcription failed.")

        # Read the transcript text
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()

        # Return both metadata and transcript
        return jsonify(success=True, transcript=transcript, metadata=metadata)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@app.route("/api/generate-profile", methods=["POST"])
def generate_profile():
    try:
        data = request.get_json()
        prompt_text = data.get("prompt")
        
        if not prompt_text:
            return jsonify({"error": "No prompt provided"}), 400
            
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert profile generation assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.4
        )
        
        content = completion.choices[0].message.content
        return jsonify({"content": content})
    except Exception as e:
        print(f"Error generating profile: {str(e)}")
        return jsonify({"error": "Failed to generate profile"}), 500
        
if __name__ == "__main__":
    app.run(debug=True)