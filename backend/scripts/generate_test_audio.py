"""Generate a synthetic test audio clip for exercising /upload-audio.

Reads sample_data/product_meeting.txt and synthesizes it with OpenAI TTS,
so the full transcribe -> analyze -> approve flow can be tested without
needing a real recording.

Usage (from backend/, venv active):
    python scripts/generate_test_audio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openai_client import client

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANSCRIPT_PATH = os.path.join(REPO_ROOT, "sample_data", "product_meeting.txt")
OUT_PATH = os.path.join(REPO_ROOT, "sample_data", "product_meeting_test_audio.mp3")


def main():
    text = open(TRANSCRIPT_PATH, encoding="utf-8").read()

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
    ) as response:
        response.stream_to_file(OUT_PATH)

    print(f"Wrote {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")


if __name__ == "__main__":
    main()
