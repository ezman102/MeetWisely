# Smart Meeting Assistant - MeetWise

## Overview

The **Smart Meeting Assistant** is an AI Streamlit-based tool that enhances both virtual and in-person meetings. It uses state-of-the-art speech processing and natural language processing (NLP) techniques to provide real-time transcription, automatic summarization, machine translation, and action item extraction. This project is built as part of a university course assignment for "Virtual Reality Technologies and Applications."

## Features

### 1. 🎤 Real-Time Speaker-Aware Transcription

#### 1.1 In-preson meeting

- Live transcription of speech from a microphone.
- Speaker diarization using `pyannote.audio` to distinguish multiple speakers.
- Automatically labeled transcript output.

#### 1.2 Online meeting

- Speech recognition to spoken conversations into text

### 2. 📝 Automatic Meeting Summarization

- Summarizes the key points, decisions, and follow-ups using `knkarthick/MEETING_SUMMARY`.
- Generates a concise and informative summary of the meeting.

### 3. 🌐 Multilingual Translation

- Translates the transcript into multiple languages including French, German, Chinese, Arabic, and more.
- Powered by MarianMT models from HuggingFace.

### 4. 👉 Action Item Extraction (DeepSeek)

- Extracts actionable tasks and commitments from the transcript.
- Utilizes `deepseek-ai/deepseek-llm-7b-chat` to identify task ownership and due dates.

## How to Use

### 1. Setup

Create and activate a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

Ensure you have a valid HuggingFace token stored in a `.env` file:

```
HF_TOKEN=your_token_here
```

### 2. Launch the App

#### 2.1 Launch In-preson meeting

```bash
streamlit run app.py
```

#### 2.2 Launch Online meeting

```bash
streamlit run chatroom_app.py
```

### 3. Functional Tabs

- **Live Transcription**: Start/Stop real-time voice transcription.
- **Summarize Transcript**: Generate an AI summary.
- **Translate Transcript**: Translate the transcript into other languages.
- **Action Items (DeepSeek)**: Get tasks and follow-ups automatically.

## Example

Sample transcript:

```
Bob: Good morning, let’s start with updates.
Tom: We completed the login feature.
```

Summary:

> The login feature was completed. Next steps involve further development and team review.

## File Structure

```
.
├── app.py                    # Main Streamlit application (In-person meeting)
├── chatroom_app.py           # Main Streamlit application (Online meeting)
├── assets/                   # Temp audio and transcript files
├── modules/
│   ├── stream_transcriber.py # Real-time transcription + diarization
│   ├── summarizer.py         # Meeting summarization module
│   ├── translator.py         # Multilingual translation
│   └── ds_action_items.py    # DeepSeek-based action item extractor
├── requirements.txt
└── .env                      # HuggingFace token
```

## Acknowledgments

- [HuggingFace Transformers](https://huggingface.co)
- [Whisper by OpenAI](https://github.com/openai/whisper)
- [pyannote-audio](https://github.com/pyannote/pyannote-audio)
- [Streamlit](https://streamlit.io)
- [SpeechRecognition](https://github.com/Uberi/speech_recognition)
