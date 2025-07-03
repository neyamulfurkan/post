import streamlit as st
import requests
import io
import csv

# Your backend API base URL (update if different)
API_BASE_URL = "https://post-generator-2.onrender.com"

# Unsplash API key
UNSPLASH_ACCESS_KEY = "q36fBLF488CCnNh8T08hDL7sfe8RR-yRYYxhumtlkoY"

# Initialize session state variables
if "token" not in st.session_state:
    st.session_state.token = ""

if "generated_post" not in st.session_state:
    st.session_state.generated_post = ""

if "image_url" not in st.session_state:
    st.session_state.image_url = ""

# Helper functions to call backend APIs
def signup(username, password):
    try:
        response = requests.post(f"{API_BASE_URL}/signup", json={"username": username, "password": password})
        return response
    except Exception as e:
        st.error(f"Signup API error: {e}")
        return None

def login(username, password):
    try:
        response = requests.post(f"{API_BASE_URL}/token", data={"username": username, "password": password})
        return response
    except Exception as e:
        st.error(f"Login API error: {e}")
        return None

def fetch_unsplash_image(topic: str, client_id: str) -> str:
    url = f"https://api.unsplash.com/photos/random?query={topic}&client_id={client_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        image_url = data.get('urls', {}).get('regular')
        if image_url:
            return image_url
        else:
            return "https://picsum.photos/600/400"  # fallback image
    except Exception as e:
        st.warning(f"Could not fetch image from Unsplash, using placeholder. Reason: {e}")
        return "https://picsum.photos/600/400"  # fallback image

st.title("Social Media Post Generator")

# Signup form
with st.expander("Signup"):
    username_su = st.text_input("Username (Signup)", key="username_su")
    password_su = st.text_input("Password (Signup)", type="password", key="password_su")
    if st.button("Signup"):
        res = signup(username_su, password_su)
        if res and res.status_code == 201:
            st.success("Signup successful! Please login now.")
        elif res:
            st.error(f"Signup failed: {res.json().get('detail', res.text)}")

# Login form
with st.expander("Login"):
    username_li = st.text_input("Username (Login)", key="username_li")
    password_li = st.text_input("Password (Login)", type="password", key="password_li")
    if st.button("Login"):
        res = login(username_li, password_li)
        if res and res.status_code == 200:
            token = res.json().get("access_token")
            st.session_state.token = token
            st.success("Login successful! Token saved.")
        elif res:
            st.error(f"Login failed: {res.json().get('detail', res.text)}")

# Show the token (readonly)
st.text_area("JWT Token", value=st.session_state.token, height=100)

# Inputs for generating post
topic = st.text_input("Enter topic")
platform = st.selectbox("Select platform", ["Twitter", "Facebook", "Instagram", "LinkedIn"])

if st.button("Generate Post"):
    if not topic:
        st.error("Please enter a topic.")
    elif not st.session_state.token:
        st.error("Please login to generate posts.")
    else:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        json_data = {"topic": topic, "platform": platform}
        try:
            with st.spinner("Generating post..."):
                response = requests.post(f"{API_BASE_URL}/generate_post", json=json_data, headers=headers)
            response.raise_for_status()
            data = response.json()
            post = data.get("post")
            if post:
                st.session_state.generated_post = post
                st.session_state.image_url = fetch_unsplash_image(topic, UNSPLASH_ACCESS_KEY)
            else:
                st.error("No post returned from backend.")
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e.response.status_code} - {e.response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"Error: {e}")

# Show generated post and downloads
if st.session_state.generated_post:
    edited_post = st.text_area("Edit Generated Post", value=st.session_state.generated_post, height=200)
    st.session_state.generated_post = edited_post

    st.download_button(
        label="Download Post as TXT",
        data=edited_post,
        file_name="post.txt",
        mime="text/plain"
    )

    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(["Post"])
    csv_writer.writerow([edited_post])

    st.download_button(
        label="Download Post as CSV",
        data=csv_buffer.getvalue(),
        file_name="post.csv",
        mime="text/csv"
    )

    st.markdown(
        "**Note:** To copy the post text, select the text above and press Ctrl+C (Cmd+C on Mac)."
    )

# Show related image
if st.session_state.image_url:
    st.image(st.session_state.image_url, caption=f"Image related to '{topic}'", use_column_width=True)
