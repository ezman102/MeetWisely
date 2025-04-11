# app.py
import streamlit as st
from modules.stream_transcriber import stream_transcribe_live
from modules.summarizer import generate_summary
from modules.translator import translate_text
from modules.ds_action_items import extract_action_items_with_deepseek

st.set_page_config(page_title="Smart Meeting Assistant")
st.sidebar.title("🧠 Smart Meeting Assistant")

uploaded_file = st.sidebar.file_uploader("📤 Upload a .txt transcript", type="txt")

# Load transcript into session if uploaded
if uploaded_file:
    transcript_text = uploaded_file.read().decode("utf-8")
    st.session_state.transcript = transcript_text.strip().split("\n")
    st.sidebar.success("Transcript uploaded and ready to use.")

app_mode = st.sidebar.radio("Choose an option:", [
    "Live Transcription",
    "Summarize Transcript",
    "Translate Transcript",
    "Action Items (DeepSeek)"
])


if uploaded_file:
    st.sidebar.markdown("📝 **Transcript Preview:**")
    st.sidebar.text_area("Transcript", value=transcript_text[:1000], height=200)

# Session state
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "transcript" not in st.session_state:
    st.session_state.transcript = []

if app_mode == "Live Transcription":
    st.header("🎤 Real-time Speaker-Aware Transcription")
    st.markdown("Transcribe speech from your microphone in real time and automatically assign speaker labels.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Transcription"):
            st.session_state.is_recording = True
            st.session_state.transcript = []  
            st.session_state.has_renamed = False  # ✅ Reset renaming flag
    with col2:
        if st.button("🛑 Stop Transcription"):
            st.session_state.is_recording = False


    transcript_box = st.empty()

    if st.session_state.is_recording:
        st.info("Recording started. Speak into your mic...")
        for labeled_lines in stream_transcribe_live():
            if not st.session_state.is_recording:
                break
            st.session_state.transcript.extend(labeled_lines)
            transcript_box.markdown("**📝 Transcript:**\n\n" + "\n\n".join(st.session_state.transcript))
        st.success("Recording stopped.")

    if st.session_state.transcript:
        transcript_box.markdown("**📝 Transcript:**\n\n" + "\n\n".join(st.session_state.transcript))

        # Save and download
        filename = "assets/transcript.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(st.session_state.transcript))
        with open(filename, "r", encoding="utf-8") as f:
            st.download_button("⬇️ Download Transcript", f, file_name="transcript.txt")

    # Optional: Rename speakers after transcription is done
    if not st.session_state.is_recording and st.session_state.transcript:

        if "has_renamed" not in st.session_state:
            st.session_state.has_renamed = False

        if not st.session_state.has_renamed:
            st.subheader("🔧 Rename Speakers")

            import re
            def get_speaker_labels(transcript_lines):
                speakers = set()
                for line in transcript_lines:
                    match = re.match(r"\[(.*?)\]", line)
                    if match:
                        speakers.add(match.group(0))
                return sorted(speakers)

            def replace_speaker_labels(transcript_lines, name_map):
                replaced = []
                for line in transcript_lines:
                    for original, new in name_map.items():
                        line = line.replace(original, new)
                    replaced.append(line)
                return replaced

            unique_speakers = get_speaker_labels(st.session_state.transcript)
            speaker_name_map = {}

            for idx, speaker in enumerate(unique_speakers):
                default_name = speaker.replace("Speaker ", "Speaker_")
                new_name = st.text_input(
                    f"Rename {speaker} to", default_name, key=f"rename_{idx}"
                )
                speaker_name_map[speaker] = f"{new_name}:"

            if st.button("✅ Apply Renaming"):
                renamed_transcript = replace_speaker_labels(
                    st.session_state.transcript, speaker_name_map
                )
                st.session_state.transcript = renamed_transcript
                st.session_state.has_renamed = True  # prevent showing rename inputs again
                st.success("Speaker names updated!")
                st.markdown("**📝 Renamed Transcript:**")
                st.markdown("\n\n".join(st.session_state.transcript))

elif app_mode == "Summarize Transcript":
    st.header("📋 Generate Meeting Summary")
    st.markdown("Generate a concise summary of the meeting from the transcript using AI.")

    if st.session_state.transcript:
        st.text_area("Transcript", value="\n".join(st.session_state.transcript), height=200)
        if st.button("🧠 Generate Summary"):
            with st.spinner("Summarizing..."):
                text = "\n".join(st.session_state.transcript)
                summary = generate_summary(text)
            st.subheader("📝 Summary")
            st.markdown(summary)
    else:
        st.warning("❗ No transcript found. Please record or upload one first.")


elif app_mode == "Translate Transcript":
    st.header("🌐 Translate Meeting Transcript")

    st.markdown("Translate the transcript into your preferred language. Supports French, German, Chinese, and more.")
    supported_languages = {
        "French": "fr",
        "German": "de",
        "Spanish": "es",
        "Arabic": "ar",
        "Hindi": "hi",
        "Chinese (Simplified)": "zh"
    }

    if st.session_state.transcript:
        st.text_area("Transcript", value="\n".join(st.session_state.transcript), height=200)

        target_lang = st.selectbox("Select target language:", list(supported_languages.keys()))
        if st.button("🌍 Translate"):
            with st.spinner("Translating transcript..."):
                full_text = "\n".join(st.session_state.transcript)
                translated = translate_text(full_text, src_lang="en", tgt_lang=supported_languages[target_lang])
            st.subheader(f"📄 Translation ({target_lang})")
            st.markdown(translated)
    else:
        st.warning("❗ No transcript found. Please record or upload one first.")

elif app_mode == "Action Items (DeepSeek)":
    st.header("🐋 DeepSeek Action Item Extraction")
    st.markdown("Automatically extract actionable items and tasks from your meeting transcript.")
    st.text_area("Transcript", value="\n".join(st.session_state.transcript), height=200)
    if st.session_state.transcript:
        if st.button("🐋 Extract with DeepSeek"):
            with st.spinner("Analyzing transcript with DeepSeek..."):
                full_text = extract_action_items_with_deepseek(st.session_state.transcript)
            st.subheader("📋 Action Items")
            st.markdown(full_text)
    else:
        st.warning("❗ No transcript found. Please record or upload one first.")

