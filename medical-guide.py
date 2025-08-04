# app.py

import streamlit as st
from openai import OpenAI
from PIL import Image
import pytesseract
import requests
import urllib.parse

# Initialize OpenAI client
client = OpenAI(api_key="") 
GOOGLE_MAPS_API_KEY = ""  # <-- Optional

st.title("🩺 Patient Report Analyzer & Verified Doctor Suggestion")

# --- Step 1: User Bio Details ---
st.header("Enter Your Bio Details")
age = st.number_input("Age", min_value=0, max_value=120, step=1)
weight = st.number_input("Weight (kg)", min_value=0.0, max_value=200.0, step=0.1)
location = st.text_input("Your City/Location")

# --- Step 2: Upload Medical Report ---
st.header("Upload Your Medical Report (PDF/Image)")
uploaded_file = st.file_uploader("Choose a PDF or an Image file", type=["pdf", "png", "jpg", "jpeg"])

# --- Step 3: Helper functions ---

# Extract text from uploaded image
def extract_text_from_file(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)
    except Exception:
        text = "Unable to extract text from the uploaded file."
    return text

# Use OpenAI to suggest initial treatment
def analyze_report(report_text, age, weight):
    messages = [
        {"role": "system", "content": "You are a healthcare assistant. Based on patient's report text, age, and weight, suggest an initial step like recommending tablets, precautions, or visiting a doctor. Be cautious, do not diagnose complex diseases."},
        {"role": "user", "content": f"Patient Report: {report_text}\nAge: {age}\nWeight: {weight}\nWhat should the patient do next?"}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )
    suggestion = response.choices[0].message.content
    return suggestion

# Try to fetch real nearby doctors using Google Maps API
def find_doctors_google_maps(location, specialty="doctor"):
    try:
        if not GOOGLE_MAPS_API_KEY:
            return None
        
        query = f"{specialty} near {location}"
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={urllib.parse.quote_plus(query)}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        results = response.json().get('results', [])

        doctors_list = []
        for doctor in results[:5]:  # Top 5 results
            name = doctor.get("name")
            address = doctor.get("formatted_address")
            maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(name)}"
            doctors_list.append(f"{name} - {address} ([View on Maps]({maps_link}))")
        return doctors_list
    except Exception as e:
        return None

# If no real API, fallback to OpenAI suggestion
def suggest_doctors_openai(location):
    messages = [
        {"role": "system", "content": "You are a helpful health assistant. Based on a city or location, suggest popular hospitals, clinics, and good doctor types nearby. Always encourage consulting licensed practitioners."},
        {"role": "user", "content": f"Suggest best doctors or clinics around {location}."}
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )
    fallback_suggestion = response.choices[0].message.content
    return fallback_suggestion

# --- Step 4: Main Processing ---

if uploaded_file and age and weight and location:
    st.success("✅ File uploaded successfully. Analyzing...")
    report_text = extract_text_from_file(uploaded_file)

    with st.spinner("🔎 Analyzing the report and suggesting treatment..."):
        treatment_suggestion = analyze_report(report_text, age, weight)

    st.header("🩺 Initial Treatment Suggestion")
    st.write(treatment_suggestion)

    st.header("🏥 Doctor / Clinic Suggestions")

    # First try Google Maps if API key available
    doctors_list = find_doctors_google_maps(location)
    
    if doctors_list:
        st.subheader("Top Nearby Doctors (Verified via Google Maps):")
        for doc in doctors_list:
            st.markdown(f"- {doc}")
    else:
        # fallback to GPT suggestion
        fallback_suggestion = suggest_doctors_openai(location)
        st.subheader("Doctor / Clinic Recommendations Based on Location:")
        st.write(fallback_suggestion)

else:
    st.info("Please complete all bio fields and upload a medical report to get suggestions.")

