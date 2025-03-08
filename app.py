
# app.pyx
import streamlit as st
import io
import os
import sqlite3
import hashlib   
import openai
from utils import validate_openai_api_key

OPENAI_API_KEY = "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"
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    con = sqlite3.connect("users.db")
    cursor = con.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE ,
            password TEXT)''')
    con.commit()
    con.close()

def register(username, password):
    con = sqlite3.connect("users.db")
    cursor = con.cursor()
    hashed_password = hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        con.commit()
        con.close()
        return True
    # checking if the username is entered more than once
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    hashed_password = hash(password)
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    tuppy = cursor.fetchone()
    conn.close()
    return tuppy

def init_session_state():
    """Initialize session state variables."""
    if 'open_ai' not in st.session_state:
        st.session_state.open_ai = None 

def generate_image(prompt, size="1024x1024"):
    """Generate an image using OpenAI's latest DALL·E API."""
    
    # Validate image size
    valid_sizes = ["256x256", "512x512", "1024x1024"]
    if size not in valid_sizes:
        return f"Error: Invalid size '{size}'. Choose from {valid_sizes}."
    try:
        response = client.images.generate(
            model="dall-e-3",  # Use DALL·E 3 for better quality
            prompt=prompt,
            n=1,  # Generate 1 image
            size=size
        )
        
        # Extract image URL from response
        image_url = response.data[0].url
        return image_url

    except openai.OpenAIError as e:
        return f"Error: {str(e)}"

def setup_page():
    """Configure page settings."""
    st.set_page_config(page_title="Clothing Design Generator Using DALLE-E", layout="wide")
    st.markdown(
        '''<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">''',
        unsafe_allow_html=True)
    st.markdown("""
        <div class="container text-center">
            <h1 class="display-4 text-primary">🎨 Clothing Design Generator Using DALLE-E</h1>
            <p class="lead">Generate images from text descriptions using OpenAI's DALLE</p>
        </div>
    """, unsafe_allow_html=True)

def api_input():
    """Handle token input and validation."""
    with st.form("token_form"):
        api = st.text_input("Enter your OpenAI's API:", type="password")
        api_submit = st.form_submit_button("Submit Token")
        
        if api_submit:
            if validate_openai_api_key(api):
                st.session_state.open_ai = api
                st.success("Token validated successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid token. Please check your token and try again.")
    
    st.info("To get your OpenAI API:\n1. Go to https://platform.openai.com/api-keys\n2. Create a new API key (READ access is sufficient)")
    st.stop()

def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        init_session_state()
        setup_page()
        
        # Check for token
        if st.session_state.open_ai is None:
            api_input()
            
        # Logout button
        if st.sidebar.button("Logout (Clear Token)"):
            st.session_state.hf_token = None
            st.experimental_rerun()
        
        # Generation form
        with st.form("generation_form"):
            prompt = st.text_area(
                "Enter your prompt:",
                placeholder="A serene landscape with mountains and a lake at sunset..."
            )
            submit_button = st.form_submit_button("Generate Image")
        
        # Handle image generation
        if submit_button and prompt:
            try:
                with st.spinner("Generating your image... This might take several minutes on CPU..."):
                    generated_imagee = generate_image(prompt)
                
                # Display image
                st.image(generated_imagee, caption=f"Generated image for: {prompt}", 
                        use_column_width=True)

                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                if "401" in str(e):
                    st.error("Authentication error. Please check your OpenAI API.")
                    st.session_state.open_ai = None
                    st.experimental_rerun()

        # Usage instructions
        with st.expander("How to use"):
            st.markdown("""
            1. Enter a descriptive prompt in the text area
            2. Adjust the number of inference steps if desired (higher = better quality but slower)
            3. Click 'Generate Image' button
            4. Wait for the image to be generated (this may take several minutes on CPU)
            5. Download the generated image if desired
            
            Note: This application runs on CPU which means generation will be slower than on GPU.
            Consider reducing the number of inference steps for faster generation.
            """)
        
    else:
        init_db()
        st.markdown("""
        <div class="container text-center">
            <h1 class="display-3 text-success">WELCOME!</h1>
        </div>
        """, unsafe_allow_html=True)
        action = st.selectbox("Select the action", ["Login", "Signup"])
        if action == "Signup":
            st.subheader("Create an account")
            username = st.text_input("Enter the username:")
            password = st.text_input("Enter the password", type="password", key="password")
            repassword = st.text_input("Enter the password", type="password", key="repassword")
            if st.button("submit"):
                if password != repassword:
                    st.error("Password dont match, try again")
                    st.experimental_rerun()
                elif not username or not password or not repassword:
                        st.error("Every box needed to be filled")
                        st.experimental_rerun()
                elif register(username, password):
                    st.success("Account created")
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.error("Username already exists")
                    st.experimental_rerun()
        elif action == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = login_user(username, password)
                if user:
                    st.success(f"Welcome {username}!")
                    st.session_state.authenticated = True  # Mark user as logged in
                    st.session_state.username = username  # Save username
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
        
if __name__ == "__main__":
    main()
