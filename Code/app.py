import streamlit as st
import pandas as pd
import hashlib
import os
import re
import smtplib
from email.mime.text import MIMEText
from streamlit_autorefresh import st_autorefresh
from health_model import analyze_latest_health
from dotenv import load_dotenv

# ----------------- ENV -----------------
load_dotenv()
EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

# ----------------- PASSWORD HASH -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------- USER DB -----------------
def load_users():
    if os.path.exists("users.csv"):
        return pd.read_csv("users.csv")
    return pd.DataFrame(columns=["name", "email", "age", "gender", "password_hash"])

def save_user(name, email, age, gender, password):
    df = load_users()
    if email in df["email"].values:
        return False
    new_user = pd.DataFrame([[name, email, age, gender, hash_password(password)]], columns=df.columns)
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv("users.csv", index=False)
    return True

def authenticate(email, password):
    df = load_users()
    user = df[df["email"] == email]
    if not user.empty and user.iloc[0]["password_hash"] == hash_password(password):
        return user.iloc[0]
    return None

def is_valid_gmail(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email)

# ----------------- EMAIL ALERT -----------------
def send_health_alert(recipient, name):
    try:
        msg = MIMEText(f"Hi {name},\n\nWe detected potential issues in your health metrics.\nPlease consult a medical professional.\n\n- VitalWatch AI \n Dr.Sharma \n healpline no.+918275168465")
        msg["Subject"] = "Health Alert from Smart Health Monitoring"
        msg["From"] = EMAIL
        msg["To"] = recipient

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)
        smtp.quit()
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="VitalWatch AI", page_icon="", layout="wide")
st_autorefresh(interval=120000, limit=None, key="health_dashboard_refresh")

# ----------------- SESSION -----------------
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "data_index" not in st.session_state:
    st.session_state.data_index = 0

# ----------------- LOGIN / SIGNUP -----------------
if st.session_state.logged_in_user is None:
    st.markdown("<h1 style='text-align:center;'>VitalWatch AI</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab2:
        st.subheader("Create an Account")
        name = st.text_input("Full Name")
        email = st.text_input("Gmail")
        age = st.number_input("Age", min_value=1, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if not is_valid_gmail(email):
                st.error("Use a valid Gmail address.")
            elif save_user(name, email, age, gender, password):
                st.success("Signup complete. Please login!")
            else:
                st.warning("Email already registered.")

    with tab1:
        st.subheader("Login to Dashboard")
        email = st.text_input("Gmail", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = authenticate(email, password)
            if user is not None:
                st.session_state.logged_in_user = user
                st.success(f"Welcome, {user['name']}")
                st.rerun()
            else:
                st.error("Invalid login credentials.")

# ----------------- LOGGED IN -----------------
else:
    user = st.session_state.logged_in_user

    st.sidebar.title("User Info")
    st.sidebar.markdown(f"Name: {user['name']}")
    st.sidebar.markdown(f"Email: {user['email']}")
    st.sidebar.markdown(f"Age: {user['age']}")
    st.sidebar.markdown(f"Gender: {user['gender']}")
    st.sidebar.divider()

    nav = st.sidebar.radio("Navigation", ["Dashboard", "Manual Input"])
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update(logged_in_user=None))

    st.markdown("<h1 style='text-align:center; color:teal;'>VitalWatch AI Dashboard</h1>", unsafe_allow_html=True)
    st.divider()

    # ----------------- DASHBOARD -----------------
    if nav == "Dashboard":
        try:
            df = pd.read_csv("health_data 1.csv")
            if df.empty:
                st.warning("No health data available.")
            else:
                idx = st.session_state.data_index % len(df)
                st.session_state.data_index += 1
                row = df.iloc[idx]

                result = analyze_latest_health(index=idx)
                if result:
                    metrics = result["metrics"]
                    prediction = result["prediction"]
                    recs = result["recommendations"]

                    st.subheader("Latest Metrics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Heart Rate", f"{metrics['Heart Rate']} bpm")
                        st.metric("Systolic", f"{metrics['Systolic']} mmHg")
                        st.metric("Diastolic", f"{metrics['Diastolic']} mmHg")
                    with col2:
                        st.metric("Sleep Duration", f"{metrics['Sleep Duration']} hrs")
                        st.metric("Sleep Quality", f"{metrics['Quality of Sleep']}/10")
                        st.metric("Steps", f"{metrics['Daily Steps']}")

                    if prediction == 1:
                        st.error("Alert: Potential risk found.")
                        if send_health_alert(user["email"], user["name"]):
                            st.info("Health alert sent to your Gmail.")
                    else:
                        st.success("You're all good!")

                    if recs:
                        st.markdown("### Recommendations")
                        for r in recs:
                            st.markdown(f"- {r}")
        except Exception as e:
            st.error(f"Error: {e}")

    # ----------------- MANUAL INPUT -----------------
    elif nav == "Manual Input":
        st.subheader("Simulate Health Input")

        col1, col2 = st.columns(2)
        with col1:
            heart_rate = st.slider("Heart Rate (bpm)", 40, 200, 72)
            systolic = st.slider("Systolic BP", 90, 180, 120)
            diastolic = st.slider("Diastolic BP", 60, 120, 80)
        with col2:
            sleep_duration = st.slider("Sleep Hours", 0, 12, 7)
            sleep_quality = st.slider("Sleep Quality (/10)", 1, 10, 8)
            daily_steps = st.slider("Daily Steps", 0, 20000, 5000)

        if st.button("Analyze"):
            input_data = {
                "Heart Rate": heart_rate,
                "Systolic": systolic,
                "Diastolic": diastolic,
                "Sleep Duration": sleep_duration,
                "Quality of Sleep": sleep_quality,
                "Daily Steps": daily_steps,
            }

            result = analyze_latest_health(input_data=input_data)
            if result:
                prediction = result["prediction"]
                recs = result["recommendations"]

                st.subheader("Health Status")
                if prediction == 1:
                    st.error("Warning: Health issue detected!")
                    if send_health_alert(user["email"], user["name"]):
                        st.success("Email alert sent.")
                else:
                    st.success("No issues detected.")

                if recs:
                    st.markdown("### Suggestions")
                    for rec in recs:
                        st.markdown(f"- {rec}")