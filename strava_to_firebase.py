import requests
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import csv
import time  # ✅ Added for refresh logic

# === CONFIGURATION ===
CLIENT_ID = "155051"
CLIENT_SECRET = "192cb020e3c6ccfa8283257981d90ec868db186e"
REDIRECT_URI = "http://localhost"
TOKEN_FILE = "strava_token.json"

# === Step 1: Initialize Firebase ===
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# === Step 2: Handle Token Management ===

def save_token(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def get_new_token():
    print("🔑 Visit the following URL to authorize Strava:")
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=force&scope=read,activity:read_all"
    print(auth_url)

    code = input("Paste the code from redirect URL: ").strip()

    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=payload)
    token_data = response.json()
    save_token(token_data)
    return token_data

def refresh_token(refresh_token):
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(token_url, data=payload)
    token_data = response.json()
    save_token(token_data)
    return token_data

# === Step 3: Get Access Token ===

token_data = load_token()
if token_data:
    if token_data.get("expires_at", 0) < int(time.time()):
        print("🔄 Refreshing expired token...")
        token_data = refresh_token(token_data["refresh_token"])
else:
    token_data = get_new_token()

access_token = token_data["access_token"]
print("✅ Access token ready.")

# === Step 4: Fetch Activities ===

headers = {"Authorization": f"Bearer {access_token}"}
activities_url = "https://www.strava.com/api/v3/athlete/activities"
params = {"per_page": 20}

res = requests.get(activities_url, headers=headers, params=params)
activities = res.json()
print(f"📥 Fetched {len(activities)} activities.")

# === Step 5: Store to Firebase & CSV ===

csv_file = "strava_activities.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "name", "distance", "moving_time", "elapsed_time", "type", "start_date"])

    for activity in activities:
        doc_ref = db.collection("stravaActivities").document(str(activity["id"]))
        doc_ref.set(activity)
        writer.writerow([
            activity.get("id"),
            activity.get("name"),
            activity.get("distance"),
            activity.get("moving_time"),
            activity.get("elapsed_time"),
            activity.get("type"),
            activity.get("start_date")
        ])
        print(f"☁️ Stored & logged: {activity['name']}")

print("✅ All activities stored in Firebase and saved to CSV.")
