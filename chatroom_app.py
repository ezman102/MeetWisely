import time
import sqlite3
import streamlit as st


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
                name TEXT UNIQUE NOT NULL)"""
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
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
    )
    user = c.fetchone()
    conn.close()
    return user


def create_chatroom(name):
    try:
        conn = sqlite3.connect("chatroom.db")
        c = conn.cursor()
        c.execute("INSERT INTO chatrooms (name) VALUES (?)", (name,))
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


def add_message(chatroom_name, username, message):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "INSERT INTO messages (chatroom_id, username, message) VALUES (?, ?, ?)",
            (chatroom_id, username, message),
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
            "SELECT username, message, timestamp FROM messages WHERE chatroom_id = ? ORDER BY timestamp ASC",
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


# Function to fetch messages periodically
def get_messages_periodically(chatroom_name, current_time_stamp):
    conn = sqlite3.connect("chatroom.db")
    c = conn.cursor()
    c.execute("SELECT id FROM chatrooms WHERE name = ?", (chatroom_name,))
    chatroom = c.fetchone()
    if chatroom:
        chatroom_id = chatroom[0]
        c.execute(
            "SELECT username, message, timestamp FROM messages WHERE chatroom_id = ? AND timestamp > ? ORDER BY timestamp ASC",
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


# Initialize the database
init_db()

# Streamlit UI
st.title("Chatroom App")

menu = st.sidebar.selectbox("Menu", ["Register", "Login", "Chatroom"])

keep_refresh_msg = False

if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

if menu == "Register":
    st.subheader("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    language = st.text_input("Preferred Language")
    keep_refresh_msg = False
    if st.button("Register"):
        if register_user(username, password, language):
            st.success("Registration successful! Please log in.")
        else:
            st.error("Username already exists.")

elif menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    keep_refresh_msg = False
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state["logged_in_user"] = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password.")

elif menu == "Chatroom":
    keep_refresh_msg = False
    if st.session_state["logged_in_user"]:
        st.subheader(f"Welcome, {st.session_state['logged_in_user']}!")
        chat_option = st.radio("Choose an option", ["Create Chatroom", "Join Chatroom"])

        if chat_option == "Create Chatroom":
            room_name = st.text_input("Chatroom Name")
            if st.button("Create"):
                if create_chatroom(room_name):
                    st.success(f"Chatroom '{room_name}' created!")
                else:
                    st.error("Chatroom already exists.")

        elif chat_option == "Join Chatroom":
            rooms = get_chatrooms()
            room_name = st.selectbox("Select Chatroom", rooms)
            if st.button("Join"):
                join_chatroom(room_name, st.session_state["logged_in_user"])
                st.success(f"Joined chatroom '{room_name}'!")
                keep_refresh_msg = False
            if room_name:
                st.subheader(f"Chatroom: {room_name}")
                members = get_chatroom_members(room_name)
                st.write("Users in chatroom:", ", ".join(members))

                message = st.text_input("Message")
                if st.button("Send"):
                    add_message(room_name, st.session_state["logged_in_user"], message)

                st.subheader("Chat Messages")
                current_time_stamp = get_current_timestamp()
                messages = get_messages(room_name)
                for user, msg, timestamp in messages:
                    st.write(f"{timestamp} - {user}: {msg}")
                    current_time_stamp = timestamp
                keep_refresh_msg = True
                while keep_refresh_msg:
                    messages = get_messages_periodically(room_name, current_time_stamp)
                    for user, msg, timestamp in messages:
                        # if message.strip():
                        st.write(f"{timestamp} - {user}: {msg}")
                        current_time_stamp = timestamp
                    time.sleep(5)  # Refresh every 5 seconds
    else:
        st.warning("Please log in to access chatroom features.")
