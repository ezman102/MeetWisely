import sounddevice as sd
import soundfile as sf
import queue
import os
import whisper
from datetime import datetime
from pyannote.audio import Pipeline
from dotenv import load_dotenv

model = whisper.load_model("small")  # "medium" if system handles it

load_dotenv()
hf_token = os.getenv("HF_TOKEN")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token=hf_token)

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    q.put(indata.copy())

def assign_speakers(segments, speaker_turns):
    labeled = []
    speaker_map = {}
    speaker_counter = 1

    for seg in segments:
        start, end = seg['start'], seg['end']
        matched_speaker = "Unknown"

        # Try to find speaker label by overlap
        for turn in speaker_turns:
            if turn["start"] <= end and turn["end"] >= start:
                matched_speaker = turn["speaker"]
                break

        # Assign readable label (Speaker 1, Speaker 2)
        if matched_speaker not in speaker_map:
            speaker_map[matched_speaker] = f"Speaker {speaker_counter}"
            speaker_counter += 1

        readable_speaker = speaker_map[matched_speaker]
        labeled.append(f"[{readable_speaker}] {seg['text'].strip()}")

    return labeled


def stream_transcribe_live(chunk_duration=10, samplerate=16000):
    os.makedirs("assets/temp_chunks", exist_ok=True)
    chunk_index = 0
    with sd.InputStream(samplerate=samplerate, channels=1, callback=audio_callback):
        while True:
            frames = []
            for _ in range(int(samplerate / 1024 * chunk_duration)):
                frames.append(q.get())

            filename = f"assets/temp_chunks/chunk_{chunk_index}.wav"

            with sf.SoundFile(filename, mode='w', samplerate=samplerate, channels=1, subtype='PCM_16') as f:
                for frame in frames:
                    f.write(frame)

            # Transcription
            result = model.transcribe(filename, language="en", task="transcribe")
            segments = result.get("segments", [])

            # Diarization
            diarization = pipeline(filename)
            speaker_turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_turns.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end
                })

            labeled_transcript = assign_speakers(segments, speaker_turns)

            chunk_index += 1
            yield labeled_transcript
