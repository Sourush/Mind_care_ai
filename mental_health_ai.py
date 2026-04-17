from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="d:/mental_ai/.env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
import os

app = Flask(__name__)
app.secret_key = "secret123"
CORS(app)


# ------------------ AUTH ------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

users = {}
logout_logs = []
user_styles = {}

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    if not session.get("user"):
        return redirect("/login")
    mode = session.get("mode", None)
    return render_template("index.html", mode=mode)

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form.get("username")
        session["user"] = username
        session.pop("mode", None)

        if username not in users:
            users[username] = []

        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    username = session.get("user")
    if username:
        logout_logs.append(f"{username} logged out")
    session.pop("user", None)
    return redirect("/login")

@app.route("/admin")
def admin_login():
    return render_template("admin.html")

@app.route("/admin/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect("/dashboard")
    else:
        return "Invalid credentials ❌"

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("dashboard.html", users=users, logout_logs=logout_logs)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/login")

# ------------------ PAGES ------------------

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/train-page")
def train_page():
    return render_template("train.html")

@app.route("/therapy")
def therapy():
    return render_template("therapy.html")

@app.route("/clone")
def clone_page():
    return render_template("clone.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ------------------ TRAIN ------------------

@app.route("/train", methods=["POST"])
def train():
    data = request.json.get("chat")
    username = session.get("user")

    user_styles[username] = data
    session["mode"] = "clone"

    return jsonify({"status": "trained"})

# ------------------ EMOTION ------------------

def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["depress", "sad", "alone", "hopeless"]):
        return "Depression"
    elif any(word in text for word in ["stress", "anxiety", "fear", "pressure"]):
        return "Anxiety"
    elif "suicide" in text or "die" in text:
        return "Critical"
    else:
        return "Normal"

# ------------------ PERSONALITY ------------------

def get_personality(mode):
    if mode == "dada":
        return "Talk like a wise Indian grandfather. Calm and guiding."
    elif mode == "mom":
        return "Talk like a caring Indian mother. Emotional and warm."
    elif mode == "sister":
        return "Talk like a friendly sister. Casual and supportive."
    elif mode == "brother":
        return "Talk like a chill brother. Motivational and friendly."
    elif mode == "partner":
        return "Talk like a loving partner. Deep and caring."
    return "You are a helpful assistant."

# ------------------ CHATBOT ------------------
def chatbot_response(user_input, mode, username):
    user_style = user_styles.get(username, "")

    if mode == "clone":
        prompt = f"""
Reply like a real human WhatsApp chat.
Style: {user_style}

User: {user_input}
Reply:
"""
    else:
        personality = get_personality(mode)

        prompt = f"""
{personality}

User style: {user_style}

User: {user_input}
Reply:
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # 🔥 BEST MODEL
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"

# ------------------ CHAT API ------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    mode = data.get("mode") or session.get("mode", "dada")
    username = session.get("user")

    response = chatbot_response(user_message, mode, username)

    if username not in users:
        users[username] = []

    users[username].append({
        "user": user_message,
        "bot": response,
        "emotion": detect_emotion(user_message)
    })

    return jsonify({"response": response})

# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))