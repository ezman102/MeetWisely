import time
import sqlite3
import streamlit as st

from modules.translator import translate_text

from modules.summarizer import generate_summary
from modules.ds_action_items import extract_action_items_with_deepseek

default_language = "en"

supported_languages = {
    "English": "en",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Arabic": "ar",
    "Hindi": "hi",
    "Chinese (Simplified)": "zh",
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
    # chatrooms = [row[0] for row in c.fetchall()]
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


def format_message(user_name, message):
    return "[" + user_name + "]" + message + "\n"


# Initialize the database
init_db()

# Streamlit UI
st.title("Chatroom App")
st.sidebar.title("📂 Menu")

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
            print(st.session_state.user_language_code)
            st.session_state["logged_in_user"] = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password.")

elif menu == "Chatroom":
    # st.session_state.keep_refresh_msg = False
    # current_time_stamp = get_current_timestamp()
    if st.session_state["logged_in_user"]:
        st.subheader(f"Welcome, {st.session_state['logged_in_user']}!")
        chat_option = st.radio("Choose an option", ["Create Chatroom", "Join Chatroom"])

        if chat_option == "Create Chatroom":
            st.session_state.is_joined_chatroom = False
            st.session_state.keep_refresh_msg = False

            room_name = st.text_input("Chatroom Name")
            if st.button("Create"):
                if create_chatroom(room_name, st.session_state["logged_in_user"]):
                    st.success(f"Chatroom '{room_name}' created!")
                    # current_time_stamp = get_current_timestamp()
                else:
                    st.error("Chatroom already exists.")

        elif chat_option == "Join Chatroom":
            # st.session_state.keep_refresh_msg = False
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
                # print("debyg", chatrooms_status["is_closed"])
                st.session_state.chatrooms_is_active = (
                    chatrooms_status["is_closed"] == False
                )
                # print(chatrooms_owner, st.session_state["logged_in_user"])
                st.subheader(f"Chatroom: {room_name}")
                members = get_chatroom_members(room_name)
                st.write("Users joined:", ", ".join(members))

                if chatrooms_owner == st.session_state["logged_in_user"]:
                    if st.sidebar.button("▶️ End Meeting"):
                        message = "End Meeting"
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
                        # if st.sidebar.button("End meeting"):
                        # update meeting status to "end"
                        # print(st.session_state["logged_in_user"])
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
                                    # st.session_state.is_loaded_chathistory = True
                                    # text = "Hello123"
                                    print("Debug: summary content- ", text)
                                    summary = generate_summary(text)
                                update_chatroom_summary(
                                    room_name, default_language, summary
                                )
                                # st.subheader("📝 Summary")
                                # st.markdown(summary)

                            # Add your code for summarizing the meeting here
                        elif app_mode == "Action Items (DeepSeek)":
                            if st.sidebar.button("🐋 DeepSeek Action Item Extraction"):
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
                                    # st.session_state.is_loaded_chathistory = True
                                    # text = "Hello123"
                                    full_text = extract_action_items_with_deepseek(text)
                                    # full_text = "Hello456"
                                update_chatroom_action_item(
                                    room_name, default_language, full_text
                                )
                                # st.subheader("📋 Action Items")
                                # st.markdown(full_text)
                            # Add your code for DeepSeek-related actions here

                chatroom_summary = get_chatroom_summary(room_name)
                print(chatroom_summary)
                if chatroom_summary is not None:
                    if (
                        chatroom_summary["summary"]
                        and chatroom_summary["summary"].strip()
                    ):
                        st.subheader("📝 Summary")
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

                        st.subheader("📋 Action Items")
                        st.write(display_content)

                st.subheader("Chat Messages")
                # load chat history
                # unknow why: A create room
                # B join, and send message -> for B: always reload history
                # if st.session_state.is_loaded_chathistory == False:
                print("debug361", st.session_state.keep_refresh_msg)
                if st.session_state.chatrooms_is_active == False:
                    show_message(st.session_state.messages)
                if st.session_state.keep_refresh_msg == False:
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
                        # st.write(f"{timestamp} - {user}: {display_msg}")
                        print(
                            "debug",
                            timestamp,
                            user,
                            display_msg,
                            st.session_state.is_loaded_chathistory,
                        )
                        st.session_state.current_time_stamp = timestamp
                        # st.session_state.is_loaded_chathistory = True
                    show_message(st.session_state.messages)

                st.session_state.keep_refresh_msg = True
                # if chatroom doesn't closed by owner, user can send message
                if st.session_state.chatrooms_is_active:
                    message = st.sidebar.text_input("Send Message")
                    translated_message = ""

                    if st.sidebar.button("Send"):
                        trim_msg = message.strip()
                        # st.session_state.keep_refresh_msg = False
                        if trim_msg != "":
                            # print("is not empty")
                            if st.session_state.user_language_code == default_language:
                                translated_message = message
                            else:
                                translated_message = translate_text(
                                    message,
                                    src_lang=st.session_state.user_language_code,
                                    tgt_lang=default_language,
                                )
                            print(
                                "Add debug message",
                                room_name,
                                st.session_state["logged_in_user"],
                                message,
                                st.session_state.user_language_code,
                                translated_message,
                                default_language,
                            )
                            add_message(
                                room_name,
                                st.session_state["logged_in_user"],
                                message,
                                st.session_state.user_language_code,
                                translated_message,
                                default_language,
                            )
                            show_message(st.session_state.messages)
                        # st.session_state.keep_refresh_msg = True
                    print(
                        "current_time_stamp",
                        st.session_state.current_time_stamp,
                        st.session_state.keep_refresh_msg,
                    )
                    while st.session_state.keep_refresh_msg:
                        # debug usage
                        # print(st.session_state.user_language_code)
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
                            print(
                                "debug463",
                                timestamp,
                                user,
                                display_msg,
                                st.session_state.keep_refresh_msg,
                            )
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
