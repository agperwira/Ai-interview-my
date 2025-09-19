# app.py
import streamlit as st
import json
# import requests  # not required for STT, but kept since you listed it
import speech_recognition as sr
from io import BytesIO

st.set_page_config(page_title="Speech-to-Text (WAV, in-memory)", page_icon="🎙️", layout="centered")
st.title("🎙️ Speech-to-Text (in-memory, WAV only)")
st.caption("Mic recording via st.audio_input() or upload a WAV file. Uses SpeechRecognition + Google Web Speech API.")

# Choose recognition language (add any BCP-47 code you need)
LANG = st.selectbox(
    "Recognition language",
    options=["my", "id-ID", "en-US"],
    index=0,
    help="BCP-47 codes. 'my' = Burmese, 'id-ID' = Indonesian, 'en-US' = English (US)."
)

def recognize_google_from_wav_bytes(wav_bytes: bytes, language: str) -> str:
    """Run SpeechRecognition on WAV bytes entirely in memory."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(BytesIO(wav_bytes)) as source:
        # Optional: light noise adaptation
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        audio = recognizer.record(source)
    # Requires internet connection
    return recognizer.recognize_google(audio, language=language)

# ---- UI: choose mic vs upload ----
mode = st.radio(
    "Audio source",
    options=("mic", "upload"),
    format_func=lambda x: "🎤 Microphone (st.audio_input)" if x == "mic" else "📤 Upload WAV file",
    horizontal=True,
    key="mode_radio"
)

# ===== MIC MODE =====
if mode == "mic":
    audio_value = st.audio_input("Record your answer:", key="audio_mic")
    if audio_value is not None:
        st.audio(audio_value)  # playback preview

    if st.button("📝 Transcribe microphone audio", use_container_width=True, key="btn_transcribe_mic"):
        if audio_value is None:
            st.error("No recording yet. Please record first.")
        else:
            try:
                mime = (audio_value.type or "").lower()
                if "wav" not in mime:
                    st.error(f"Input is not WAV (detected: {mime}). Please use a browser/device that provides WAV.")
                else:
                    wav_bytes = audio_value.getvalue()
                    text = recognize_google_from_wav_bytes(wav_bytes, language=LANG)
                    st.success("Transcription complete ✅")
                    st.text_area("Transcribed text", value=text, height=220)
                    st.code(json.dumps({"source": "mic", "mime": mime, "lang": LANG}, ensure_ascii=False, indent=2))
            except sr.UnknownValueError:
                st.error("Could not understand the audio.")
            except sr.RequestError as e:
                st.error(f"STT service error: {e}")

# ===== UPLOAD MODE =====
else:
    uploaded = st.file_uploader("Upload a WAV file (PCM 16-bit mono recommended)", type=["wav"], key="audio_upload")
    if uploaded is not None:
        st.audio(uploaded)

    if st.button("📝 Transcribe uploaded file", use_container_width=True, key="btn_transcribe_upload"):
        if uploaded is None:
            st.error("Please upload a WAV file first.")
        else:
            try:
                wav_bytes = uploaded.read()
                text = recognize_google_from_wav_bytes(wav_bytes, language=LANG)
                st.success("Transcription complete ✅")
                st.text_area("Transcribed text", value=text, height=220)
                st.code(json.dumps(
                    {"source": "upload", "mime": uploaded.type, "lang": LANG, "filename": uploaded.name},
                    ensure_ascii=False, indent=2
                ))
            except sr.UnknownValueError:
                st.error("Could not understand the audio.")
            except sr.RequestError as e:
                st.error(f"STT service error: {e}")
