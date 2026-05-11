from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_audio(audio_path: str) -> str:
    segments, info = model.transcribe(audio_path, language="en")

    transcript = ""

    for segment in segments:
        transcript += segment.text.strip() + "\n"

    return transcript