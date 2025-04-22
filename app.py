import json
from flask import Flask, render_template, request, jsonify
from video_downloader import download_video
from DeepgramTranscriber import transcribe_audio
from dotenv import load_dotenv
import os

load_dotenv()  # This loads the .env file


app = Flask(__name__, template_folder="MatchMakingUI", static_folder="static")

# replicate your mock DB (or load from a file) exactly as in the HTML
mockDatabase = {
    "ya214": """# Bio-Psycho-Social Business Profile

## Bio  
**Name:** Dr. Yusef Alimam  
**Profession:** Medical AI Strategist, CTO, Educator  
**Business Name:** Green Medical Network Group  
**Place of Work:** Global / Remote

## Psycho  
Dr. Yusef Alimam is driven by a deep belief in using AI to solve meaningful problems in healthcare and education. With dual strengths in biomedical science and artificial intelligence, he thrives at the intersection of innovation and impact.  
His inner motivation stems from the desire to build systems that are not just efficient, but ethical — aiming to reduce friction in care delivery and elevate clinical intelligence.  
He is intellectually curious, systems-oriented, and constantly learning to refine both himself and the tools he builds.

## Social  
Dr. Alimam is embedded in a highly interdisciplinary and international network — with active ties in **San Diego, Bahrain, Dallas**, and multiple **global innovation hubs**.  
His social presence spans **startups**, **faith-based initiatives**, **academic ecosystems**, and **high-performing medical networks**.  
He is known as a **thoughtful collaborator**, **educator-mentor**, and a **connector** between technical and clinical worlds.

## Business Needs
- **AI Automation for Healthcare:** Building or partnering with tools that use LLMs and computer vision to improve workflows in radiology, memory clinics, and administrative processes.  
- **Strategic Partnerships:** Identifying early-stage ventures that align with ethical medical AI.  
- **Scalable Revenue Streams:** Designing platforms or licensing models for white-labeled AI infrastructure (e.g., *Muse* for eyewear, *RLA* for supply chains).  
- **Networked Intelligence:** Integrating data from hundreds of physicians into shared knowledge systems and patient-enabling interfaces.  
- **Delegation & Offshore Teams:** Efficiently managing vetted remote contributors in design, engineering, and content ops.

## Income  
**Estimated Annual Income:** $120K

## Opportunities
- Can organize business relationships with hungry doctors to help them build their own AI tools.  
- Interested in investing in **early-stage biotech** in **Europe**."""
}

@app.route("/")
def index():
    return render_template(
        "bio_psycho_social_generator_clean.html",
        mock_database=json.dumps(mockDatabase)
    )
'''
@app.route("/api/run_pipeline", methods=["POST"])
def run_pipeline():
    data = request.get_json()
    vid = data.get("video_id")
    if not vid:
        return jsonify(success=False, error="No video_id provided"), 400
    try:
        video_file = download_video(vid)
        txt_file = transcribe_audio(video_file)
        with open(txt_file, "r", encoding="utf-8") as f:
            transcript = f.read()
        return jsonify(success=True, transcript=transcript)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
'''
import DeepgramTranscriber
import video_downloader
from video_downloader import download_video, fetch_metadata_as_string
from DeepgramTranscriber import transcribe_audio

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
        
if __name__ == "__main__":
    app.run(debug=True)