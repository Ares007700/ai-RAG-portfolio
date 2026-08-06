import streamlit as st
import requests

st.title("Friday")

if "token" not in st.session_state:
    st.session_state.token = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(
            "http://localhost:8000/login",
            json={"email": email, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.success("Logged in!")
        else:
            st.error("Login failed")

    st.divider()
    st.header("Conversations")

    if st.button("New Chat"):
        if not st.session_state.token:
            st.sidebar.warning("Please log in first.")
        else:
            st.session_state.conversation_id = None
            st.session_state.messages = []

    if st.button("Refresh List"):
        if not st.session_state.token:
            st.sidebar.warning("Please log in first.")
        else:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.get("http://localhost:8000/conversations", headers=headers, timeout=10)
            if response.status_code == 200:
                st.session_state.conversations = response.json()
            else:
                st.sidebar.error("Could not load conversations. Try logging in again.")

    for convo in st.session_state.conversations:
        label = f"#{convo['id']}: {convo['preview'][:30]}"
        if st.button(label, key=f"resume_{convo['id']}"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.get(
                f"http://localhost:8000/conversations/{convo['id']}/messages",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                st.session_state.conversation_id = convo["id"]
                st.session_state.messages = response.json()
            else:
                st.sidebar.error("Could not load that conversation.")

# ---------------- MAIN CHAT AREA ----------------
if not st.session_state.token:
    st.warning("Please log in from the sidebar first.")
else:
    if st.session_state.conversation_id:
        st.caption(f"Conversation #{st.session_state.conversation_id}")
    else:
        st.caption("New conversation")

    # Render the full conversation so far
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    message = st.chat_input("Your message")

    if message:
        # Show the user's message immediately
        st.session_state.messages.append({"role": "user", "content": message})
        with st.chat_message("user"):
            st.write(message)

        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    "message": message,
                    "conversation_id": st.session_state.conversation_id
                },
                headers=headers,
                stream=True,
                timeout=60
            )

            if response.status_code != 200:
                st.error(f"Something went wrong (status {response.status_code}). Please try again.")
            else:
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    full_reply = ""
                    first_chunk = True
                    buffer = ""

                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if not chunk:
                            continue

                        if first_chunk:
                            buffer += chunk
                            if "\n" in buffer:
                                marker_line, rest = buffer.split("\n", 1)
                                if marker_line.startswith("__CONVO_ID__:"):
                                    st.session_state.conversation_id = int(marker_line.split(":")[1])
                                full_reply += rest
                                placeholder.write(full_reply)
                                first_chunk = False
                            continue

                        full_reply += chunk
                        placeholder.write(full_reply)

                if full_reply:
                    st.session_state.messages.append({"role": "assistant", "content": full_reply})

        except requests.exceptions.RequestException as e:
            st.error("⚠️ Couldn't reach the server. Please check your connection and try again.")
            print(f"[Chat error] {e}")  # full detail stays in your terminal, not shown to the user

        except (ValueError, OSError) as e:
            st.error("⚠️ Something unexpected went wrong. Please try again.")
            print(f"[Chat error] {e}")