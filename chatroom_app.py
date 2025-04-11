import time
import sqlite3
import streamlit as st
import speech_recognition as sr
import threading

from modules.translator import translate_text

from modules.summarizer import generate_summary
from modules.ds_action_items import extract_action_items_with_deepseek

st.set_page_config(page_title="Smart Meeting Assistant (Online)")

default_language = "en"

# language that support translation
supported_languages = {
    "English": "en",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Arabic": "ar",
    "Hindi": "hi",
    "Chinese (Simplified)": "zh",
}

# Mapping of text content to language codes
recognize_google_language_mapping = {
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "ar": "ar-SA",
    "hi": "hi-IN",
    "zh": "zh-CN",
}


# Database setup
def init_db():
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                language TEXT NOT NULL)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS chatrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                owner TEXT NOT NULL,
                is_closed BOOLEAN DEFAULT FALSE)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS chatroom_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chatroom_id INTEGER,
                username TEXT,
                FOREIGN KEY(chatroom_id) REFERENCES chatrooms(id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chatroom_id INTEGER,
                username TEXT,
                message TEXT,
                language TEXT,
                translated_message TEXT,
                translated_language TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chatroom_id) REFERENCES chatrooms(id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS chatrooms_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chatroom_id INTEGER,
                summary TEXT,
                action_item TEXT,
                languages TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chatroom_id) REFERENCES chatrooms(id))"""
    )
    conn.commit()
    conn.close()


def register_user(username, password, language):
    try:
        conn = sqlite3.connect("chatroom.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password, language) VALUES (?, ?, ?)",
            (username, password, language),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, password):
    conn = sqlite3.connect("chatroom.db")
    # Enable dictionary-style access
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
    )
    user = c.fetchone()
    conn.close()
    return user


def create_chatroom(name, owner):
    try:
        conn = sqlite3.connect("chatroom.db")
        c = conn.cursor()
        c.execute("INSERT INTO chatrooms (name, owner) VALUES (?,?)", (name, owner))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def join_chatroom(chatroom_name, username):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "SELECT * FROM chatroom_members WHERE chatroom_id = ? AND username = ?",
            (chatroom_id, username),
        )
        if not c.fetchone():
            c.execute(
                "INSERT INTO chatroom_members (chatroom_id, username) VALUES (?, ?)",
                (chatroom_id, username),
            )
            conn.commit()
    conn.close()


def get_chatrooms():
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT name FROM chatrooms")
    chatrooms = [row[0] for row in c.fetchall()]
    conn.close()
    return chatrooms


def get_chatrooms_status(chatroom_name):
    conn = sqlite3.connect("chatroom.db")
    # Enable dictionary-style access
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT owner, is_closed FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatrooms = c.fetchone()
    conn.close()
    return chatrooms


def end_chatroom(chatroom_name):
    try:
        conn = sqlite3.connect("chatroom.db")
        c = conn.cursor()
        c.execute(
            "UPDATE chatrooms SET is_closed = TRUE WHERE name = ?", (chatroom_name,)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_chatroom_members(chatroom_name):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "SELECT username FROM chatroom_members WHERE chatroom_id = ?",
            (chatroom_id,),
        )
        members = [row[0] for row in c.fetchall()]
    else:
        members = []
    conn.close()
    return members


def add_message(
    chatroom_name, username, message, language, translated_message, translated_languag
):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "INSERT INTO messages (chatroom_id, username, message, language, translated_message, translated_language) VALUES (?, ?, ?, ?, ?, ?)",
            (
                chatroom_id,
                username,
                message,
                language,
                translated_message,
                translated_languag,
            ),
        )
        conn.commit()
    conn.close()


def get_messages(chatroom_name):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "SELECT username, message, language, translated_message, translated_language, timestamp FROM messages WHERE chatroom_id = ? ORDER BY timestamp ASC",
            (chatroom_id,),
        )
        messages = c.fetchall()
    else:
        messages = []
    conn.close()
    return messages


def get_current_timestamp():
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT datetime('now')")
    current_timestamp = c.fetchone()[0]
    conn.close()
    return current_timestamp


def update_chatroom_summary(chatroom_name, languages, summary):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]

        c.execute(
            "SELECT id FROM chatrooms_summary WHERE chatroom_id = ?",
            (chatroom_id,),
        )
        chatrooms_summary = c.fetchone()
        if chatrooms_summary:
            c.execute(
                "UPDATE chatrooms_summary SET summary = ? WHERE chatroom_id = ?",
                (summary, chatroom_id),
            )
        else:
            c.execute(
                "INSERT INTO chatrooms_summary (chatroom_id, summary, languages) VALUES (?, ?, ?)",
                (chatroom_id, summary, languages),
            )
        conn.commit()
    conn.close()


def update_chatroom_action_item(chatroom_name, languages, action_item):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]

        c.execute(
            "SELECT id FROM chatrooms_summary WHERE chatroom_id = ?",
            (chatroom_id,),
        )
        chatrooms_summary = c.fetchone()
        if chatrooms_summary:
            c.execute(
                "UPDATE chatrooms_summary SET action_item = ? WHERE chatroom_id = ?",
                (action_item, chatroom_id),
            )
        else:
            c.execute(
                "INSERT INTO chatrooms_summary (chatroom_id, action_item, languages) VALUES (?, ?, ?)",
                (chatroom_id, action_item, languages),
            )
        conn.commit()
    conn.close()


def get_chatroom_summary(chatroom_name):
    conn = sqlite3.connect("chatroom.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]

        c.execute(
            "SELECT summary, action_item, languages FROM chatrooms_summary WHERE chatroom_id = ?",
            (chatroom_id,),
        )
        chatrooms_summary = c.fetchone()
    conn.close()
    # Check if any record is found
    if chatrooms_summary is None:
        return None  # No record found
    return chatrooms_summary


# Function to fetch messages periodically
# only message after current_time_stamp will be selected
def get_messages_periodically(chatroom_name, current_time_stamp):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "SELECT username, message, language, translated_message, translated_language, timestamp FROM messages WHERE chatroom_id = ? AND timestamp > ? ORDER BY timestamp ASC",
            (
                chatroom_id,
                current_time_stamp,
            ),
        )
        messages = c.fetchall()
    else:
        messages = []
    conn.close()
    return messages


def show_message(chat_message):
    for message in chat_message:
        st.write(message)


# format message to a specific format - pass to summarizar / deepseek for extract action item
def format_message(user_name, message):
    return user_name + " : " + message + "\n"


def start_recording():
    st.session_state.recording = True
    st.session_state.captured_text = ""
    listen_in_background(st.session_state.user_language_code)


def stop_recording():
    st.session_state.recording = False


# Initialize recognizer
recognizer = sr.Recognizer()

if "recording" not in st.session_state:
    st.session_state.recording = False
if "captured_text" not in st.session_state:
    st.session_state.captured_text = ""


# Function to get the corresponding language code
def get_recognize_google_language_code(text):
    return recognize_google_language_mapping.get(text, default_language)


def get_key_from_value(mapping, value):
    for key, val in mapping.items():
        if val == value:
            return key
    return None


# Function to process audio in real time
def listen_in_background(language_code):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while st.session_state.recording:
            try:
                audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                # print("Debug-selected language",get_recognize_google_language_code(language_code),)
                text = recognizer.recognize_google(
                    audio_data,
                    language=get_recognize_google_language_code(language_code),
                )
                st.session_state.captured_text += text + " "
                # "en-US"
                # print("Debug-listen_in_background", text)
            except sr.UnknownValueError:
                st.warning("Listening... (Could not understand)")
            except sr.RequestError:
                st.error("Error: Unable to reach Google Speech Recognition API")
            except Exception as e:
                st.error(f"Error: {e}")


# Initialize the database
init_db()

# Streamlit UI
st.title("Chatroom App")
st.sidebar.title("📂 Menu")

# basic fucntion
menu = st.sidebar.selectbox("", ["Register", "Login", "Chatroom"])

if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

if menu == "Register":
    st.session_state.keep_refresh_msg = False
    st.session_state.is_joined_chatroom = False

    st.subheader("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    selected_language = st.selectbox(
        "Preferred Language", list(supported_languages.keys())
    )

    if st.button("Register"):
        # Get the corresponding mapping
        language_code = supported_languages[selected_language]
        if register_user(username, password, language_code):
            st.success("Registration successful! Please log in.")
        else:
            st.error("Username already exists.")

elif menu == "Login":
    st.session_state.keep_refresh_msg = False
    st.session_state.is_joined_chatroom = False

    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user_language_code = user["language"]
            # print(st.session_state.user_language_code)
            st.session_state["logged_in_user"] = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password.")

elif menu == "Chatroom":
    # only logged user can use
    if st.session_state["logged_in_user"]:
        st.subheader(f"Welcome, {st.session_state['logged_in_user']}!")
        chat_option = st.radio("Choose an option", ["Create Chatroom", "Join Chatroom"])

        # create chat room
        if chat_option == "Create Chatroom":
            st.session_state.is_joined_chatroom = False
            st.session_state.keep_refresh_msg = False

            room_name = st.text_input("Chatroom Name")
            if st.button("Create"):
                if create_chatroom(room_name, st.session_state["logged_in_user"]):
                    st.success(f"Chatroom '{room_name}' created!")
                else:
                    st.error("Chatroom already exists.")
        elif chat_option == "Join Chatroom":

            rooms = get_chatrooms()
            room_name = st.selectbox("Select Chatroom", rooms)
            st.session_state.chatrooms_is_active = True
            if st.button("Join"):
                join_chatroom(room_name, st.session_state["logged_in_user"])
                st.session_state.is_joined_chatroom = True
                st.session_state.is_loaded_chathistory = False
                st.session_state.messages = []
                st.session_state.current_time_stamp = get_current_timestamp()

            if room_name and st.session_state.is_joined_chatroom:
                chatrooms_status = get_chatrooms_status(room_name)
                chatrooms_owner = chatrooms_status["owner"]
                st.session_state.chatrooms_is_active = (
                    chatrooms_status["is_closed"] == False
                )
                st.subheader(f"Chatroom: {room_name}")
                st.write(
                    f"Language: {get_key_from_value(supported_languages, st.session_state.user_language_code)}"
                )
                members = get_chatroom_members(room_name)
                st.write("Users joined:", ", ".join(members))

                # owner of the chatroom can end meeting, generate summary, and, extract action item
                if chatrooms_owner == st.session_state["logged_in_user"]:
                    if st.sidebar.button("🔚 End Meeting"):
                        message = "Meeting Ended"
                        if default_language != st.session_state.user_language_code:
                            translated_msg = translate_text(
                                message,
                                src_lang=default_language,
                                tgt_lang=st.session_state.user_language_code,
                            )
                        else:
                            translated_msg = message
                        add_message(
                            room_name,
                            st.session_state["logged_in_user"],
                            translated_msg,
                            st.session_state.user_language_code,
                            message,
                            default_language,
                        )
                        end_chatroom(room_name)
                        st.session_state.chatrooms_is_active = False
                    if st.session_state.chatrooms_is_active == False:
                        # user can
                        # 1 "Summarize Transcript",
                        # 2 "Translate Transcript"
                        app_mode = st.sidebar.radio(
                            "Choose an action:",
                            [
                                "Summarize Meeting",
                                "Action Items (DeepSeek)",
                            ],
                        )

                        if app_mode == "Summarize Meeting":
                            if st.sidebar.button("🧠 Generate Summary"):
                                with st.spinner("Summarizing..."):
                                    messages = get_messages(room_name)
                                    text = ""
                                    for (
                                        user,
                                        msg,
                                        lang,
                                        translated_msg,
                                        translated_lang,
                                        timestamp,
                                    ) in messages:
                                        text += format_message(user, translated_msg)
                                    summary = generate_summary(text)
                                    # print("Debug: summary content- ", text)

                                update_chatroom_summary(
                                    room_name, default_language, summary
                                )
                        elif app_mode == "Action Items (DeepSeek)":
                            if st.sidebar.button("🐋 Extract with DeepSeek"):
                                with st.spinner(
                                    "Analyzing transcript with DeepSeek..."
                                ):
                                    messages = get_messages(room_name)
                                    text = ""
                                    for (
                                        user,
                                        msg,
                                        lang,
                                        translated_msg,
                                        translated_lang,
                                        timestamp,
                                    ) in messages:
                                        text += format_message(user, translated_msg)
                                    full_text = extract_action_items_with_deepseek(text)
                                update_chatroom_action_item(
                                    room_name, default_language, full_text
                                )

                chatroom_summary = get_chatroom_summary(room_name)
                # print(chatroom_summary)
                if chatroom_summary is not None:
                    if (
                        chatroom_summary["summary"]
                        and chatroom_summary["summary"].strip()
                    ):
                        display_content = chatroom_summary["summary"]
                        if (
                            chatroom_summary["languages"]
                            != st.session_state.user_language_code
                        ):
                            display_content = translate_text(
                                display_content,
                                src_lang=chatroom_summary["languages"],
                                tgt_lang=st.session_state.user_language_code,
                            )

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📝 Summary")
                        with col2:
                            filename = "assets/Summary.txt"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(display_content)
                            with open(filename, "r", encoding="utf-8") as f:
                                st.download_button(
                                    "⬇️ Summary",
                                    f,
                                    file_name="Summary.txt",
                                )
                        st.write(display_content)
                    if (
                        chatroom_summary["action_item"]
                        and chatroom_summary["action_item"].strip()
                    ):
                        display_content = chatroom_summary["action_item"]
                        if (
                            chatroom_summary["languages"]
                            != st.session_state.user_language_code
                        ):
                            display_content = translate_text(
                                display_content,
                                src_lang=chatroom_summary["languages"],
                                tgt_lang=st.session_state.user_language_code,
                            )
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📋 Download Action Items")
                        with col2:
                            filename = "assets/ActionItems.txt"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(display_content)
                            with open(filename, "r", encoding="utf-8") as f:
                                st.download_button(
                                    "⬇️ Action Items",
                                    f,
                                    file_name="ActionItems.txt",
                                )
                        st.write(display_content)

                # load chat history
                if (st.session_state.keep_refresh_msg == False) or (
                    not st.session_state.messages
                ):
                    messages = get_messages(room_name)
                    for (
                        user,
                        msg,
                        lang,
                        translated_msg,
                        translated_lang,
                        timestamp,
                    ) in messages:
                        display_msg = ""
                        if st.session_state.user_language_code == lang:
                            display_msg = msg
                        elif st.session_state.user_language_code == translated_lang:
                            display_msg = translated_msg
                        else:
                            # use default lang and translate to target language
                            display_msg = translate_text(
                                translated_msg,
                                src_lang=translated_lang,
                                tgt_lang=st.session_state.user_language_code,
                            )
                        st.session_state.messages.append(
                            f"{timestamp} - {user}: {display_msg}"
                        )
                        st.session_state.current_time_stamp = timestamp

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Chat Messages")
                with col2:
                    filename = "assets/ChatMessage.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        display_content = ""
                        for content in st.session_state.messages:
                            display_content += content + "\n"
                        f.write(display_content)
                    with open(filename, "r", encoding="utf-8") as f:
                        st.download_button(
                            "⬇️ Chat Message",
                            f,
                            file_name="ChatMessage.txt",
                        )
                if (st.session_state.chatrooms_is_active == False) or (
                    st.session_state.keep_refresh_msg == False
                ):
                    show_message(st.session_state.messages)

                st.session_state.keep_refresh_msg = True
                # if chatroom doesn't closed by owner, user can send message
                if st.session_state.chatrooms_is_active:
                    st.sidebar.button("▶️ Start Transcription", on_click=start_recording)
                    st.sidebar.button("🛑 Stop Transcription", on_click=stop_recording)

                    if st.session_state.recording == False:
                        if st.session_state.captured_text != "":
                            translated_message = ""
                            st.session_state.recording = False
                            time.sleep(1)  # Allow the thread to finish properly
                            st.session_state.captured_text = ""
                            captured_text = st.session_state.captured_text
                            # st.write(st.session_state.captured_text)
                            if st.session_state.user_language_code == default_language:
                                translated_message = captured_text
                            else:
                                translated_message = translate_text(
                                    captured_text,
                                    src_lang=st.session_state.user_language_code,
                                    tgt_lang=default_language,
                                )
                            add_message(
                                room_name,
                                st.session_state["logged_in_user"],
                                captured_text,
                                st.session_state.user_language_code,
                                translated_message,
                                default_language,
                            )
                            show_message(st.session_state.messages)

                    message = st.sidebar.text_input("Send Message")
                    translated_message = ""

                    if st.sidebar.button("Send"):
                        trim_msg = message.strip()
                        if trim_msg != "":
                            if st.session_state.user_language_code == default_language:
                                translated_message = message
                            else:
                                translated_message = translate_text(
                                    message,
                                    src_lang=st.session_state.user_language_code,
                                    tgt_lang=default_language,
                                )
                            # print(
                            #     "Add debug message",
                            #     room_name,
                            #     st.session_state["logged_in_user"],
                            #     message,
                            #     st.session_state.user_language_code,
                            #     translated_message,
                            #     default_language,
                            # )
                            add_message(
                                room_name,
                                st.session_state["logged_in_user"],
                                message,
                                st.session_state.user_language_code,
                                translated_message,
                                default_language,
                            )
                            show_message(st.session_state.messages)
                    while st.session_state.keep_refresh_msg:
                        have_new_message = False
                        messages = get_messages_periodically(
                            room_name, st.session_state.current_time_stamp
                        )
                        for (
                            user,
                            msg,
                            lang,
                            translated_msg,
                            translated_lang,
                            timestamp,
                        ) in messages:
                            display_msg = ""
                            if st.session_state.user_language_code == lang:
                                display_msg = msg
                            elif st.session_state.user_language_code == translated_lang:
                                display_msg = translated_msg
                            else:
                                # use default lang and translate to target language
                                display_msg = translate_text(
                                    translated_msg,
                                    src_lang=translated_lang,
                                    tgt_lang=st.session_state.user_language_code,
                                )
                            # keep message that will be show when user click send button
                            st.session_state.messages.append(
                                f"{timestamp} - {user}: {display_msg}"
                            )
                            st.write(f"{timestamp} - {user}: {display_msg}")
                            # print(
                            #     "debug463",
                            #     timestamp,
                            #     user,
                            #     display_msg,
                            #     st.session_state.keep_refresh_msg,
                            # )
                            st.session_state.current_time_stamp = timestamp
                            have_new_message = True
                        # if have_new_message:
                        # show_message(st.session_state.messages)
                        time.sleep(5)  # Refresh every 5 seconds
    else:
        st.warning("Please log in to access chatroom features.")


def repeated_task(st):
    while True:
        st.write("Content write by thread")
        # Wait for 5 seconds
        time.sleep(5)
