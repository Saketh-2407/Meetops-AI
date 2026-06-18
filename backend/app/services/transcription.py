from app.services.openai_client import client
from app.config import TRANSCRIBE_MODEL


def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file to text.

    Note for the README: audio transcription can contain errors, so users
    must review the transcript before approving any actions.
    """
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=audio_file,
        )
    return transcript.text
