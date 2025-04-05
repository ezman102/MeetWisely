import streamlit as st
from modules.stream_transcriber import stream_transcribe_live
from modules.summarizer import generate_summary
from modules.translator import translate_text
from modules.ds_action_items import extract_action_items_with_deepseek

st.set_page_config(page_title="Smart Meeting Assistant")
st.sidebar.title("📂 Menu")

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


st.title("🧠 Smart Meeting Assistant")

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

    if st.button("▶️ Start Transcription"):
        st.session_state.is_recording = True
        st.session_state.transcript = []  
        
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

elif app_mode == "Summarize Transcript":
    st.header("📋 Generate Meeting Summary")

    if st.session_state.transcript:
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

    supported_languages = {
        "French": "fr",
        "German": "de",
        "Spanish": "es",
        "Arabic": "ar",
        "Hindi": "hi",
        "Chinese (Simplified)": "zh"
    }

    if st.session_state.transcript:
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

    if st.session_state.transcript:
        if st.button("🐋 Extract with DeepSeek"):
            with st.spinner("Analyzing transcript with DeepSeek..."):
                full_text = extract_action_items_with_deepseek(st.session_state.transcript)
            st.subheader("📋 Action Items")
            st.markdown(full_text)
    else:
        st.warning("❗ No transcript found. Please record or upload one first.")

