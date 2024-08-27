import streamlit as st
from st_audiorec import st_audiorec
import io
import whisper
import os
from string import punctuation
from heapq import nlargest
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import en_core_web_sm


import streamlit as st
from streamlit import session_state
import json
import os
import numpy as np
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI
import whisper
from st_audiorec import st_audiorec
import io
from gtts import gTTS
from datetime import datetime
from googlesearch import search
# datetime object containing current date and time

load_dotenv()


def generate_search_terms(Highlights):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        prompt = (
            """
As a smart teaching assistant, your task is to generate relevant search terms based on the provided highlights for the previous teaching sessions. You should identify the key topics discussed during the session and generate search terms that can be used to find more information on those topics. Do not mention that you are an AI assistant.

Your responsibilities also include:
- Identifying the main topics discussed in the class.
- Generating search terms based on those topics.
- Search term should be in the form of a list separated by newline python characters ordered from most to least relevant topics.
- Format: 
search term 1
search term 2
search term 3
..
- Do not add anythig else in the response."""
            + Highlights
        )
        messages = [{"role": "system", "content": prompt}]
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-0125",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def smart_assistant_query(email,query):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        Highlights = []
        with open("data.json", "r") as json_file:
            user_data = json.load(json_file)
            for user in user_data["users"]:
                if user["email"] == email:
                    if user["Highlights"] is None or len(user["Highlights"]) == 0:
                        return "No previous MoMs found for the user."
                    Highlights = user["Highlights"]
                    break
                    
        prompt = (
            f"""
As a smart business assistant, your task is to answer the user's queries based on the provided data. The provided data is of highlights of the previous teaching sessions. You should be able to give all the insights possible only from the given data. You should provide detailed responses to the user's questions without revealing that you are an AI assistant. You should also be able to answer follow-up questions and provide additional information as needed. If the user asks for more information, you should be able to provide it. You should also be able to answer any questions that the user may have about the data.

Your responsibilities also include:
- Identifying useful insights from the provided data.
- Answering queries based on the information in the data.
- Providing additional information or answering questions from the user.
- Conducting internet searches to gather relevant results if needed. + Query: {query}

Previous Teaching session (Provided data):
"""
            + str(Highlights)
        )
        messages = [{"role": "system", "content": prompt}]
        response = client.chat.completions.create(
            messages=messages,
            # model="gpt-3.5-turbo",
            model="gpt-3.5-turbo-0125",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def smart_teaching_assistant(session_transcription):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        prompt = """
As a smart teaching assistant, your task is to generate detailed class session highlights based on the provided session transcription. Additionally, you are responsible for conducting relevant internet research to supplement the teaching with necessary information. This includes details about discussed topics such as Homework, Assignments, Projects,Food for thoughts, Higher Order thinking questions, and other important information. You should provide a detailed summary of the session and highlight key takeaways without revealing that you are an AI assistant.
Your responsibilities also include:
- Identifying the main topics discussed in the class.
- Executing possible insights from the provided data.
- Providing additional information or answering questions from the user.
- Conducting internet searches to gather relevant results if the meeting involves gathering information on a specific topic.

Session Transcription:
""" +session_transcription
            
            
        prompt += session_transcription
        messages = [{"role": "system", "content": prompt}]
        response = client.chat.completions.create(
            messages=messages,
            # model="gpt-3.5-turbo",
            model="gpt-3.5-turbo-0125",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


session_state = st.session_state
if "user_index" not in st.session_state:
    st.session_state["user_index"] = 0
    
def transcribe_audio_from_data(file_data):
    with open("temp.mp3", "wb") as f:
        f.write(file_data)
    model = whisper.load_model("base")
    result = model.transcribe("temp.mp3")
    os.remove("temp.mp3")
    return result["text"]

def signup(json_file_path="data.json"):
    st.title("Signup Page")
    with st.form("signup_form"):
        st.write("Fill in the details below to create an account:")
        name = st.text_input("Name:")
        email = st.text_input("Email:")
        age = st.number_input("Age:", min_value=0, max_value=120)
        sex = st.radio("Sex:", ("Male", "Female", "Other"))
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        
        if st.form_submit_button("Signup"):
            if password == confirm_password:
                user = create_account(
                    name,
                    email,
                    age,
                    sex,
                    password,
                    json_file_path,
                )
                session_state["logged_in"] = True
                session_state["user_info"] = user
            else:
                st.error("Passwords do not match. Please try again.")


def check_login(username, password, json_file_path="data.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)

        for user in data["users"]:
            if user["email"] == username and user["password"] == password:
                session_state["logged_in"] = True
                session_state["user_info"] = user
                st.success("Login successful!")
                return user
        return None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return None


def initialize_database(json_file_path="data.json"):
    try:
        if not os.path.exists(json_file_path):
            data = {"users": []}
            with open(json_file_path, "w") as json_file:
                json.dump(data, json_file)
    except Exception as e:
        print(f"Error initializing database: {e}")


def create_account(
    name,
    email,
    age,
    sex,
    password,
    json_file_path="data.json",
):
    try:

        if not os.path.exists(json_file_path) or os.stat(json_file_path).st_size == 0:
            data = {"users": []}
        else:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)

        # Append new user data to the JSON structure
        user_info = {
            "name": name,
            "email": email,
            "age": age,
            "sex": sex,
            "password": password,
            "Highlights": None,
        }
        data["users"].append(user_info)

        # Save the updated data to JSON
        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        st.success("Account created successfully! You can now login.")
        return user_info
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Error creating account: {e}")
        return None


def login(json_file_path="data.json"):
    st.title("Login Page")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    login_button = st.button("Login")

    if login_button:
        user = check_login(username, password, json_file_path)
        if user is not None:
            session_state["logged_in"] = True
            session_state["user_info"] = user
        else:
            st.error("Invalid credentials. Please try again.")


def get_user_info(email, json_file_path="data.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)
            for user in data["users"]:
                if user["email"] == email:
                    return user
        return None
    except Exception as e:
        st.error(f"Error getting user information: {e}")
        return None

def render_dashboard(user_info, json_file_path="data.json"):
    try:
        st.title(f"Welcome to the Dashboard, {user_info['name']}!")
        
        st.subheader("User Information:")
        st.write(f"Name: {user_info['name']}")
        st.write(f"Sex: {user_info['sex']}")
        st.write(f"Age: {user_info['age']}")
        st.image("image.jpg", caption="VoyageAI - Your AI Business Assistant", use_column_width=True)
        
    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")
        
        
def get_summary(text_content, percent):
    nlp = en_core_web_sm.load()
    stop_words = list(STOP_WORDS)
    punctuation_items = punctuation + "\n"
    nlp = spacy.load("en_core_web_sm")
    nlp_object = nlp(text_content)
    word_frequencies = {}
    for word in nlp_object:
        if word.text.lower() not in stop_words:
            if word.text.lower() not in punctuation_items:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1

    max_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word] / max_frequency
    sentence_token = [sentence for sentence in nlp_object.sents]
    sentence_scores = {}
    for sent in sentence_token:
        sentence = sent.text.split(" ")
        for word in sentence:
            if word.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.lower()]
    select_length = int(len(sentence_token) * (int(percent) / 100))
    summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)
    final_summary = [word.text for word in summary]
    summary = " ".join(final_summary)
    return summary

def main(json_file_path="data.json"):
    # st.markdown(
    #     """
    # <style>
    #     body {
    #         background-color: #0b1e34;
    #         color: white;
    #     }
    #     .st-bw {
    #         color: white;
    #     }
    # </style>
    # """,
    #     unsafe_allow_html=True,
    # )
    # st.markdown(
    #     f"""
    #     <style>
    #     .stApp {{
    #         background: url("https://learn.g2.com/hubfs/G2CM_FI671_Learn_Article_Images_%5BNote_taking_apps%5D_V1b.png");
    #         background-size: cover
    #     }}
    #     </style>
    #     """,
    #     unsafe_allow_html=True,
    # )
    st.title("SoundScript")

    page = st.sidebar.radio(
        "Go to",
        (
            "Signup/Login",
            "Dashboard",
            "Take Notes",
            "Smart Tutoring Assistant",
            "View Previous Sessions",
        ),
        key="Automatic Speech Recognition",
    )

    if page == "Signup/Login":
        st.title("Signup/Login Page")
        login_or_signup = st.radio(
            "Select an option", ("Login", "Signup"), key="login_signup"
        )
        if login_or_signup == "Login":
            login(json_file_path)
        else:
            signup(json_file_path)

    elif page == "Dashboard":
        if session_state.get("logged_in"):
            render_dashboard(session_state["user_info"])
        else:
            st.warning("Please login/signup to view the dashboard.")
            
            
    elif page == "Take Notes":
        if session_state.get("logged_in"):
            user_info = session_state["user_info"]
            st.title("Take Notes and highlight key takeaways")
            st.write("Record the session or upload an audio file to generate the Notes and highlight key takeaways:")
            transcriptions_or_summary = st.radio(
        "Choose an option:", ("Get Transcription", "Get Summary")
    )
            if transcriptions_or_summary == "Get Transcription":
                button_name = "Get Transcription"
                type_ = "transcription"
                length = "100%"
            else:
                button_name = "Get Summary"
                type_ = "summary"
                length = st.select_slider(
                "Specify length of Summary",
                options=["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"],
        )
            options = ["Record", "Upload"]
            choice = st.radio("Choose an option", options)
            highlights = None
            Speech = None
            if choice == "Record":
                st.write("Click the button below to start recording:")
                audio = st_audiorec()
                if audio is not None and st.button("Submit"):
                    transcription = transcribe_audio_from_data(audio)
                    if transcriptions_or_summary == "Get Summary":
                        summary = get_summary(transcription, int(length[:2]))
                        st.write("Summary:\n", summary)
                        speech = summary
                    else:
                        st.write("Transcription:\n", transcription)
                        speech = transcription
                    highlights = smart_teaching_assistant(transcription)
                    st.subheader("Key Highlights and Takeaways:")
                    st.write(highlights)
                    with open(json_file_path, "r+") as json_file:
                        data = json.load(json_file)
                        for user in data["users"]:
                            if user["email"] == user_info["email"]:
                                if user["Highlights"] is None:
                                    user["Highlights"] = [{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Highlight": highlights}]
                                else:
                                    user["Highlights"].append({"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Highlight": highlights})
                                json_file.seek(0)
                                json.dump(data, json_file, indent=4)
                                json_file.truncate()
                                                    
            elif choice == "Upload":
                st.write("Upload an audio file:")
                audio = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"])
                if audio is not None and st.button("Submit"):
                    st.audio(audio, format="audio/wav")
                    transcription = transcribe_audio_from_data(audio.read())
                    if transcriptions_or_summary == "Get Summary":
                        summary = get_summary(transcription, int(length[:2]))
                        st.write("Summary:\n", summary)
                        speech = summary
                    else:
                        st.write("Transcription:\n", transcription)
                        speech = transcription
                    highlights = smart_teaching_assistant(transcription)
                    st.subheader("Key Highlights and Takeaways:")
                    st.write(highlights)
                    with open(json_file_path, "r+") as json_file:
                        data = json.load(json_file)
                        for user in data["users"]:
                            if user["email"] == user_info["email"]:
                                if user["Highlights"] is None:
                                    user["Highlights"] = [{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Highlight": highlights}]
                                else:
                                    user["Highlights"].append({"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Highlight": highlights})
                                json_file.seek(0)
                                json.dump(data, json_file, indent=4)
                                json_file.truncate()
            if highlights and speech:
                search_terms = generate_search_terms(highlights).split("\n")
                search_terms = search_terms[:(min(3, len(search_terms)))]
                st.subheader("Suggested links for further reading:")
                for search_term in search_terms:
                    searches = search(search_term, num_results=2)
                    for search_ in searches:
                        st.write(search_)
                st.success("###  \U0001F3A7 Hear your Highlights")
                speech = gTTS(text = highlights,lang="en", slow = False)
                speech.save('user_trans.mp3')          
                audio_file = open('user_trans.mp3', 'rb')    
                audio_bytes = audio_file.read()    
                st.audio(audio_bytes, format='audio/ogg',start_time=0)
                audio_file.close()
                download_button_str = f"Download Highlights and Takeaways"
                with io.BytesIO(highlights.encode()) as stream:
                    st.download_button(
                        download_button_str, stream, file_name="highlights.txt"
                    )
            
        else:
            st.warning("Please login/signup to chat.")
    
    elif page == "Smart Tutoring Assistant":
        if session_state.get("logged_in"):
            user_info = session_state["user_info"]
            st.title("Smart Assistant")
            st.write("Ask your query to the smart assistant:")
            query = st.text_area("Enter your query:")
            if st.button("Ask"):
                email = user_info["email"]
                response = smart_assistant_query(email,query)
                st.subheader("Response:")
                st.write(response)
        else:
            st.warning("Please login/signup to meditate.")
            
            
    elif page == "View Previous Sessions":
        if session_state.get("logged_in"):
            user_info = session_state["user_info"]
            st.title("View All Previous Highlights and keys")
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
                for user in data["users"]:
                    if user["email"] == user_info["email"]:
                        user_info = user
                        break
            if user_info["Highlights"] is not None:
                st.subheader("Previous highlights:")
                for highlight in user_info["Highlights"]:
                    st.markdown(f"### {highlight['Timestamp']}")
                    st.write(highlight["Highlight"])
            else:
                st.warning("You do not have any previous Sessions.")
        else:
            st.warning("Please login/signup to meditate.")
    else:
        st.error("Invalid page selection.")
if __name__ == "__main__":
    initialize_database()
    main()
