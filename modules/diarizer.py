from pyannote.audio import Pipeline
from dotenv import load_dotenv
import os

# Hugging Face token
load_dotenv()
hf_token = os.getenv("HF_TOKEN")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token=hf_token)

def diarize_audio(file_path):
    diarization = pipeline(file_path)
    turns = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end
        })
    return turns

def assign_speakers(segments, speaker_turns):
    result = []
    for segment in segments:
        mid = (segment['start'] + segment['end']) / 2
        speaker = "Unknown"
        for turn in speaker_turns:
            if turn["start"] <= mid <= turn["end"]:
                speaker = turn["speaker"]
                break
        result.append({
            "speaker": speaker,
            "text": segment['text']
        })
    return result
