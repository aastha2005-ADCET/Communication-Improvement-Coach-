# ============================================================
# COMMUNICATION IMPROVEMENT COACH - COMPLETE UPDATED PROJECT
# Python 3 | Tkinter GUI | SQLite | Whisper Speech-to-Text
#
# Install in VS Code terminal:
#   python -m pip install SpeechRecognition PyAudio
#   python -m pip install openai-whisper
#   python -m pip install matplotlib
#
# Whisper may require FFmpeg installed and available on PATH.
# First Whisper use downloads the selected model (internet required).
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import re
import threading
import hashlib
import os
import tempfile
import wave
import audioop
from datetime import datetime

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ---------------- CONFIGURATION ----------------
APP_TITLE = "Communication Improvement Coach"
DB_FILE = "communication_coach.db"

BG = "#F3F5FA"
NAVY = "#202A44"
PURPLE = "#6558D3"
WHITE = "#FFFFFF"
GREEN = "#16865C"
ORANGE = "#D97706"
RED = "#C0392B"
MUTED = "#667085"

root = tk.Tk()
root.title(APP_TITLE)
root.geometry("1180x790")
root.minsize(980, 650)
root.configure(bg=BG)

current_user = {"name": ""}
active_timer = {"job": None}
quiz_state = {"page": 0, "selected": [], "answers": [], "score": 0}
speech_topic_state = {"topic": ""}

# ---------------- DATABASE ----------------
db = sqlite3.connect(DB_FILE)
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY, password TEXT NOT NULL, created_at TEXT
)""")
cur.execute("PRAGMA table_info(users)")
user_columns = [row[1] for row in cur.fetchall()]
if "created_at" not in user_columns:
    cur.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
if "username" not in user_columns:
    raise RuntimeError("Existing users table has no username column.")
if "password" not in user_columns:
    raise RuntimeError("Existing users table has no password column.")

cur.execute("""CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL, activity TEXT NOT NULL,
    score INTEGER NOT NULL, date TEXT NOT NULL,
    improvement_feedback TEXT DEFAULT ''
)""")
cur.execute("PRAGMA table_info(progress)")
progress_columns = [row[1] for row in cur.fetchall()]
if "improvement_feedback" not in progress_columns:
    cur.execute("ALTER TABLE progress ADD COLUMN improvement_feedback TEXT DEFAULT ''")
db.commit()

# ---------------- DATA ----------------
vocabulary = [
("Abundant","Available in large quantities"),("Accurate","Correct and exact"),
("Adapt","Adjust to a new situation"),("Admire","Respect or appreciate"),
("Ambitious","Having strong goals"),("Ancient","Very old"),("Approach","A way of dealing with something"),
("Benefit","An advantage or helpful result"),("Brave","Showing courage"),("Calm","Peaceful and relaxed"),
("Capable","Able to do something"),("Careful","Taking care to avoid mistakes"),
("Challenge","A difficult task"),("Clarify","Make something clear"),("Collaborate","Work together"),
("Confident","Believing in your own ability"),("Consistent","Doing something regularly"),
("Creative","Using imagination to make something new"),("Curious","Eager to learn"),
("Decision","A choice made after thinking"),("Dedicated","Committed to a task"),
("Demonstrate","Show how something works"),("Develop","Grow or improve"),
("Efficient","Working well without wasting time"),("Encourage","Give support or confidence"),
("Essential","Very important or necessary"),("Evaluate","Judge or assess something"),
("Excellent","Extremely good"),("Expand","Make larger or increase"),
("Experience","Knowledge gained by doing something"),("Flexible","Able to change easily"),
("Fluent","Able to speak smoothly and easily"),("Focus","Give attention to something"),
("Generous","Willing to give or share"),("Genuine","Real, honest, and sincere"),
("Grateful","Feeling thankful"),("Improve","Make something better"),
("Independent","Able to act without help"),("Innovative","Introducing new ideas"),
("Inspire","Motivate someone"),("Knowledge","Information and understanding"),
("Logical","Based on reason"),("Maintain","Keep in good condition"),
("Motivate","Give someone a reason to act"),("Observe","Watch carefully"),
("Opportunity","A chance to do something"),("Patient","Able to wait calmly"),
("Persuade","Convince someone with reasons"),("Precise","Exact and accurate"),
("Reliable","Can be trusted"),("Resilient","Able to recover from difficulty"),
("Respect","Show consideration for others"),("Significant","Important or meaningful"),
("Solution","An answer to a problem"),("Support","Help or encourage"),
("Thoughtful","Showing care and consideration"),("Unique","Different from others"),
("Valuable","Useful or worth a lot"),("Versatile","Useful in many different ways"),
("Wisdom","Good judgement and understanding")
]

grammar_questions = [
("She ___ to college every day.",["go","goes","going"],1),
("They ___ playing cricket.",["is","am","are"],2),
("I ___ a student.",["is","am","are"],1),
("He has ___ apple.",["a","an","the"],1),
("We ___ finished our work.",["has","have","is"],1),
("She ___ not like tea.",["do","does","are"],1),
("The sun ___ in the east.",["rise","rises","rising"],1),
("I went ___ school.",["to","at","on"],0),
("There ___ five books.",["is","are","am"],1),
("He is taller ___ me.",["than","then","that"],0),
("I ___ English now.",["study","am studying","studied"],1),
("They have lived here ___ 2020.",["for","since","from"],1),
("She can ___ fast.",["runs","running","run"],2),
("Neither answer ___ correct.",["are","is","were"],1),
("If I study, I ___ pass.",["will","would","was"],0),
("I have ___ my homework.",["do","did","done"],2),
("He ___ yesterday.",["come","came","comes"],1),
("The children ___ happy.",["is","are","was"],1),
("Please listen ___ me.",["to","at","on"],0),
("She speaks English ___.",["good","well","bestly"],1),
("I am interested ___ music.",["on","at","in"],2),
("This is ___ book.",["my","me","I"],0),
("We ___ visit tomorrow.",["will","was","has"],0),
("He did not ___.",["came","come","comes"],1),
("There isn't ___ milk.",["many","much","few"],1),
("Each student ___ a pen.",["have","has","are"],1),
("I prefer tea ___ coffee.",["than","to","from"],1),
("She was born ___ May.",["in","on","at"],0),
("He arrived ___ 9 AM.",["in","on","at"],2),
("The plural of child is ___.",["childs","children","childes"],1),
("I ___ never seen it.",["has","have","was"],1),
("She ___ cooking when I came.",["was","were","is"],0),
("A group of students ___ here.",["are","is","were"],1),
("The opposite of difficult is ___.",["easy","hard","tough"],0),
("Please give it to ___.",["I","me","my"],1),
("He is good ___ mathematics.",["in","at","on"],1),
("I look forward to ___ you.",["meet","meeting","met"],1),
("She ___ already left.",["have","has","are"],1),
("We were tired, ___ we rested.",["so","because","although"],0),
("He is ___ honest man.",["a","an","the"],1),
("The train ___ before we arrived.",["leave","had left","leaves"],1),
("I wish I ___ fly.",["can","could","will"],1),
("You should ___ water.",["drink","drank","drinking"],0),
("My friends ___ coming.",["is","are","am"],1),
("She is the ___ student.",["good","better","best"],2),
("I have been waiting ___ two hours.",["since","for","from"],1),
("The news ___ surprising.",["are","is","were"],1),
("He asked me ___ I was ready.",["if","what","which"],0),
("This is the place ___ I live.",["where","who","whose"],0),
("Let's ___ a break.",["take","takes","taking"],0)
]

daily_questions = [
"Introduce yourself in English.","Describe your college.","What is your favourite hobby and why?",
"Why is communication important?","Describe your daily routine.","What are your career goals?",
"How do you handle a difficult situation?","Describe your favourite book.","What does teamwork mean to you?",
"How can technology improve education?","Describe a person who inspires you.","What are your strengths?",
"How do you manage your time?","What is cybersecurity?","Why do you want to learn English?",
"Describe a memorable day.","How do you solve problems?","What makes a good leader?",
"What did you learn this week?","What is your dream job?","How do you overcome fear?",
"Why is reading useful?","Describe your favourite place.","What is artificial intelligence?",
"How do you help your family?","What does success mean to you?","What would you change in your college?",
"How do you learn new skills?","What is your biggest achievement?","How can students protect their data?",
"Describe your favourite festival.","What makes a good friend?","Why should we respect others?",
"How do you prepare for an exam?","What is your favourite subject?","How can we reduce pollution?",
"What is the value of discipline?","Describe your ideal teacher.","How do you handle feedback?",
"What is the importance of exercise?","How can you build confidence?","What is your plan for tomorrow?",
"Describe a problem you solved.","What is the benefit of teamwork?","How do you stay motivated?",
"Why is honesty important?","What skill would you like to master?","Describe a technology you use.",
"How can you become a better speaker?","What advice would you give a friend?"
]

pronunciation_words = [
"Entrepreneur","Pronunciation","Rural","Literature","Particularly","February","Hierarchy","Architecture",
"Entrepreneurship","Miscellaneous","Colonel","Worcestershire","Sixth","Specific","Statistics","Comfortable",
"Vegetable","Wednesday","Library","Jewellery","Receipt","Debt","Subtle","Queue","Choir","Anxiety",
"Phenomenon","Onomatopoeia","Conscientious","Inconvenience","Preliminary","Exaggerate","Thorough",
"Throughout","Strengths","Clothes","Months","World","Squirrel","Regularly","Necessary","Environment",
"Development","Communication","Opportunity","Responsibility","Analysis","Certificate","Technology","Cybersecurity"
]

interview_questions = [
"Tell me about yourself.","What are your greatest strengths?","What is one weakness you are improving?",
"Why should we select you?","Why do you want this role?","What do you know about our organisation?",
"Describe a challenge you overcame.","Tell me about a time you worked in a team.",
"How do you handle pressure?","Where do you see yourself in five years?",
"What motivates you?","How do you prioritise tasks?","Describe a mistake and what you learned.",
"How do you accept feedback?","What does success mean to you?","Why should we hire a fresher?",
"What skills make you suitable for this role?","How do you learn a new tool?",
"Tell me about a project you completed.","What was your role in that project?",
"What was the biggest project challenge?","How do you solve a problem you do not understand?",
"How do you manage deadlines?","Do you prefer working alone or in a team?",
"Describe a time you showed leadership.","How do you handle disagreement with a teammate?",
"What are your short-term goals?","What are your long-term goals?","Why did you choose your course?",
"What subject do you enjoy most and why?","What technical skills are you learning?",
"Explain a technical concept in simple words.","How do you keep your skills updated?",
"What is your proudest achievement?","What have you learned outside the classroom?",
"How would your friends describe you?","What do you do when you do not know an answer?",
"How do you respond to change?","How do you maintain quality in your work?",
"Tell me about a time you solved a conflict.","What do you expect from a manager?",
"What kind of workplace helps you do your best?","What makes you different from other candidates?",
"How do you balance study and personal activities?","What is your preferred way to receive feedback?",
"What would you do if you made an urgent mistake at work?",
"How would you explain a gap in your knowledge?","What questions would you ask the interviewer?",
"Are you willing to learn new responsibilities?","Is there anything else you would like us to know?"
]

speaking_topics = [
"Introduce yourself","Describe your college","Talk about your favourite subject","Describe your hobbies",
"Talk about your family","Explain your career goal","Describe your future plans","How are you improving your English?",
"Describe your daily routine","Talk about your best friend","Describe a memorable day","Explain why teamwork matters",
"Talk about a technology you like","Describe your strengths","Explain your dream job"
]

# ---------------- UI HELPERS ----------------
def safe_after(func, *args):
    try:
        root.after(0, lambda: func(*args))
    except tk.TclError:
        pass

def clear_page():
    stop_timer()
    for widget in root.winfo_children():
        widget.destroy()

def make_button(parent, text, command, color=PURPLE, width=None):
    return tk.Button(parent, text=text, command=command, bg=color, fg=WHITE,
        activebackground=color, activeforeground=WHITE, font=("Segoe UI", 10, "bold"),
        relief="flat", bd=0, cursor="hand2", padx=13, pady=9, width=width)

def page_heading(title, subtitle=""):
    tk.Label(root, text=title, bg=BG, fg=NAVY,
             font=("Segoe UI", 22, "bold")).pack(pady=(14, 3))
    if subtitle:
        tk.Label(root, text=subtitle, bg=BG, fg=MUTED,
                 font=("Segoe UI", 10)).pack(pady=(0, 8))

def back_button(parent=root):
    make_button(parent, "← Back to Dashboard", dashboard, NAVY).pack(pady=10)

def make_improvement_advice(activity, score, notes=""):
    if score >= 85:
        level = "You are doing well. Keep practising regularly and aim for more natural, precise answers."
    elif score >= 65:
        level = "You have a good foundation. Review the mistakes shown and practise for 10 minutes daily."
    else:
        level = "Focus on the basics. Practise slowly, review examples, and repeat this activity before moving ahead."
    if activity.lower().startswith("grammar"):
        action = "Revise subject–verb agreement, tenses, articles, and prepositions. Write five example sentences for each weak rule."
    elif activity.lower().startswith("vocabulary"):
        action = "Review the word and meaning, say the word aloud, and use it in one original sentence. Revisit difficult words tomorrow."
    elif activity.lower().startswith("pronunciation"):
        action = "Break the word into syllables, listen to a trusted dictionary audio, repeat it slowly three times, then use it in a sentence."
    else:
        action = "Use complete sentences, organise your answer into a beginning, main point, and conclusion, and add one reason or example. Reduce filler words."
    parts = [level, "Recommended next step: " + action]
    if notes:
        parts.append(notes)
    return " ".join(parts)

def save_progress(activity, score, feedback=None):
    score = max(0, min(100, int(score)))
    feedback = feedback or make_improvement_advice(activity, score)
    cur.execute("INSERT INTO progress(username, activity, score, date, improvement_feedback) VALUES (?, ?, ?, ?, ?)",
        (current_user["name"], activity, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), feedback))
    db.commit()

def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def analyse_text(text, activity="Practice"):
    words = re.findall(r"\b[\w'-]+\b", text)
    lower = text.lower()
    fillers = re.findall(r"\b(um|uh|erm|actually|basically|literally|like|you know)\b", lower)
    issues = []
    replacements = [
        (r"\bi is\b", "I am"), (r"\bhe don't\b", "he doesn't"),
        (r"\bshe don't\b", "she doesn't"), (r"\bi has\b", "I have"),
        (r"\bhe have\b", "he has"), (r"\bshe have\b", "she has"),
        (r"\bthey was\b", "they were"), (r"\bwe was\b", "we were"),
        (r"\bi didn't went\b", "I didn't go"), (r"\bmore better\b", "better"),
        (r"\bdiscuss about\b", "discuss"), (r"\breturn back\b", "return"),
        (r"\byour welcome\b", "you're welcome")
    ]
    corrected = text
    for pattern, replacement in replacements:
        match = re.search(pattern, corrected, flags=re.I)
        if match:
            issues.append(f"Possible correction: '{match.group(0)}' → '{replacement}'")
            corrected = re.sub(pattern, replacement, corrected, flags=re.I)
    if text and text[-1] not in ".!?":
        issues.append("Add suitable punctuation at the end.")
        corrected = corrected.rstrip() + "."
    if len(words) < 8:
        issues.append("Try giving a longer answer with a reason or example.")
    if fillers:
        issues.append("Reduce filler words: " + ", ".join(sorted(set(fillers))))
    if not issues:
        issues.append("No obvious rule-based issue detected. Keep practising; this is not a full grammar checker.")
    score = max(20, min(100, 75 + min(len(words), 50)//3 - len(fillers)*5 - len(issues)*2))
    feedback = (
        f"Activity: {activity}\nWords detected: {len(words)}\nFiller words: {len(fillers)}\n"
        f"Estimated practice score: {score}/100\n\nFeedback:\n• " + "\n• ".join(issues) +
        "\n\nCorrected / polished text:\n" + corrected +
        "\n\nTeacher tip: Answer clearly, use complete sentences, and add one reason or example."
    )
    return score, feedback, corrected

def show_feedback_page(title, feedback, activity, score, corrected=None):
    clear_page()
    page_heading(title, "Review your result, then return to the dashboard.")
    box = tk.Text(root, wrap="word", font=("Segoe UI", 11), height=23, width=115)
    box.pack(fill="both", expand=True, padx=24, pady=12)
    box.insert("1.0", feedback)
    box.configure(state="disabled")
    make_button(root, "← Back to Dashboard", dashboard, NAVY).pack(pady=10)

def stop_timer():
    if active_timer["job"] is not None:
        try:
            root.after_cancel(active_timer["job"])
        except tk.TclError:
            pass
        active_timer["job"] = None

# ---------------- WELCOME / REGISTER / LOGIN ----------------
def welcome_page():
    clear_page()
    splash = tk.Frame(root, bg=NAVY)
    splash.pack(fill="both", expand=True)
    tk.Label(splash, text="WELCOME TO", bg=NAVY, fg="#C7D2FE",
             font=("Segoe UI", 18, "bold")).pack(pady=(190, 8))
    tk.Label(splash, text="COMMUNICATION IMPROVEMENT COACH", bg=NAVY, fg=WHITE,
             font=("Segoe UI", 25, "bold"), wraplength=1000).pack(pady=8)
    tk.Label(splash, text="Build confidence. Improve clarity. Communicate professionally.",
             bg=NAVY, fg="#E5E7EB", font=("Segoe UI", 12)).pack(pady=10)
    progress = ttk.Progressbar(splash, mode="indeterminate", length=280)
    progress.pack(pady=22)
    progress.start(10)
    root.after(1800, login_page)

def login_page():
    clear_page()
    frame = tk.Frame(root, bg=WHITE, padx=45, pady=28,
                     highlightthickness=1, highlightbackground="#D9DFEA")
    frame.place(relx=0.5, rely=0.5, anchor="center")
    tk.Label(frame, text="Communication Improvement Coach", bg=WHITE, fg=NAVY,
             font=("Segoe UI", 21, "bold")).pack(pady=(0, 8))
    tk.Label(frame, text="Sign in or create your own learner account. Multiple users are supported.",
             bg=WHITE, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(0, 16))
    tk.Label(frame, text="Username", bg=WHITE, fg=NAVY,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    username = tk.Entry(frame, font=("Segoe UI", 12), width=32, relief="solid", bd=1)
    username.pack(pady=(4, 10), ipady=4)
    tk.Label(frame, text="Password (minimum 4 characters)", bg=WHITE, fg=NAVY,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    password = tk.Entry(frame, font=("Segoe UI", 12), width=32, show="*", relief="solid", bd=1)
    password.pack(pady=(4, 10), ipady=4)

    def register():
        u, p = username.get().strip(), password.get()
        if not u or not p:
            messagebox.showwarning("Missing details", "Enter both a username and a password.", parent=root)
            return
        if len(u) > 40 or any(ch.isspace() for ch in u):
            messagebox.showwarning("Invalid username", "Use a username of up to 40 characters without spaces.", parent=root)
            return
        if len(p) < 4:
            messagebox.showwarning("Password too short", "Choose a password with at least 4 characters.", parent=root)
            return
        try:
            cur.execute("SELECT 1 FROM users WHERE username=?", (u,))
            if cur.fetchone():
                messagebox.showerror("Username already exists", "This username is already registered. Please choose another.", parent=root)
                return
            cur.execute("PRAGMA table_info(users)")
            columns_info = cur.fetchall()
            available_columns = {row[1] for row in columns_info}
            values_by_column = {
                "username": u, "name": u, "password": password_hash(p),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            insert_columns = [c for c in values_by_column if c in available_columns]
            placeholders = ", ".join(["?"] * len(insert_columns))
            cur.execute(
                f"INSERT INTO users ({', '.join(insert_columns)}) VALUES ({placeholders})",
                [values_by_column[c] for c in insert_columns]
            )
            db.commit()
            password.delete(0, "end")
            messagebox.showinfo("Account created successfully",
                f"The account for '{u}' has been created. You can now log in.", parent=root)
            username.focus_set()
        except sqlite3.Error as exc:
            db.rollback()
            messagebox.showerror("Registration error", f"The account could not be created.\n\nDetails: {exc}", parent=root)

    def login():
        u, p = username.get().strip(), password.get()
        if not u or not p:
            messagebox.showwarning("Missing details", "Enter your username and password to log in.", parent=root)
            return
        try:
            cur.execute("SELECT username FROM users WHERE username=? AND password=?", (u, password_hash(p)))
            found = cur.fetchone()
            if not found:
                cur.execute("SELECT username FROM users WHERE username=? AND password=?", (u, p))
                found = cur.fetchone()
                if found:
                    cur.execute("UPDATE users SET password=? WHERE username=?", (password_hash(p), u))
                    db.commit()
            if found:
                current_user["name"] = found[0]
                dashboard()
            else:
                messagebox.showerror("Login failed", "The username or password is incorrect. Create an account first if you are a new user.", parent=root)
        except sqlite3.Error as exc:
            messagebox.showerror("Login error", str(exc), parent=root)

    make_button(frame, "Login", login, GREEN).pack(fill="x", pady=(8, 5))
    make_button(frame, "Create Account", register, PURPLE).pack(fill="x")
    tk.Label(frame, text="Allow microphone access in Windows when using speaking practice.",
             bg=WHITE, fg=MUTED, font=("Segoe UI", 9), wraplength=340).pack(pady=(13, 0))
    username.bind("<Return>", lambda event: password.focus_set())
    password.bind("<Return>", lambda event: login())
    username.focus_set()

# ---------------- DASHBOARD ----------------
def dashboard():
    clear_page()
    top = tk.Frame(root, bg=NAVY, height=76)
    top.pack(fill="x")
    tk.Label(top, text="🎓 Communication Mastery Coach", bg=NAVY, fg=WHITE,
             font=("Segoe UI", 20, "bold")).pack(side="left", padx=24, pady=18)
    tk.Label(top, text=f"Welcome, {current_user['name']}", bg=NAVY, fg=WHITE,
             font=("Segoe UI", 11, "bold")).pack(side="right", padx=24)
    tk.Label(root, text="Your Personal Communication Learning Dashboard", bg=BG, fg=NAVY,
             font=("Segoe UI", 17, "bold")).pack(pady=(15, 2))
    tk.Label(root, text="Choose a module, practise, submit, and review your feedback.",
             bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(0, 9))
    cur.execute("SELECT COUNT(*), COALESCE(ROUND(AVG(score)),0) FROM progress WHERE username=?",
                (current_user["name"],))
    total, avg = cur.fetchone()
    metric = tk.Frame(root, bg=BG)
    metric.pack(pady=4)
    for label, value in [("Practice Sessions", total), ("Average Score", f"{avg}/100")]:
        card = tk.Frame(metric, bg=WHITE, padx=22, pady=9)
        card.pack(side="left", padx=8)
        tk.Label(card, text=str(value), bg=WHITE, fg=PURPLE, font=("Segoe UI", 17, "bold")).pack()
        tk.Label(card, text=label, bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack()
    grid = tk.Frame(root, bg=BG)
    grid.pack(pady=10, expand=True)
    items = [
        ("🎤 Speaking Practice", speaking_page, "Speak, capture full transcript and analyse"),
        ("📝 Grammar Practice", grammar_page, "50 questions in 5 sets of 10"),
        ("📚 Vocabulary Builder", vocabulary_page, "60 words with simple meanings"),
        ("❓ Daily Questions", questions_page, "20+ prompts with timer and feedback"),
        ("🗣 Pronunciation", pronunciation_page, "50 difficult words to practise"),
        ("💼 Interview Practice", interview_page, "50 common interview questions"),
        ("📈 Daily Progress & Graph", progress_page, "Scores, history and chart")
    ]
    for i, (label, action, desc) in enumerate(items):
        card = tk.Frame(grid, bg=WHITE, padx=15, pady=9, highlightthickness=1, highlightbackground="#E7EAF1")
        card.grid(row=i//3, column=i%3, padx=9, pady=8, sticky="nsew")
        tk.Label(card, text=label, bg=WHITE, fg=NAVY, font=("Segoe UI", 12, "bold")).pack(pady=(3, 4))
        tk.Label(card, text=desc, bg=WHITE, fg=MUTED, font=("Segoe UI", 9), wraplength=270).pack(pady=3)
        make_button(card, "Start Practice", action).pack(pady=(5, 1), fill="x")
    for col in range(3):
        grid.grid_columnconfigure(col, weight=1)
    bottom = tk.Frame(root, bg=BG)
    bottom.pack(pady=3)
    make_button(bottom, "Logout", login_page, NAVY).pack(side="left", padx=5)
    make_button(bottom, "Exit", root.destroy, RED).pack(side="left", padx=5)

# ---------------- SPEECH PRACTICE CORE (UPDATED) ----------------
def build_speech_page(title, prompt, activity, question_list=None):
    clear_page()
    page_heading(title, "Record your full answer, wait for transcription, review/edit the text, then analyse.")
    tk.Label(root, text=prompt, bg=WHITE, fg=NAVY, wraplength=1000,
             font=("Segoe UI", 13, "bold"), padx=20, pady=12).pack(fill="x", padx=22, pady=7)

    controls = tk.Frame(root, bg=BG)
    controls.pack(pady=5)
    tk.Label(controls, text="Time limit:", bg=BG, fg=NAVY).pack(side="left", padx=5)
    time_choice = ttk.Combobox(controls, values=["15","30","45","60","90","120"], state="readonly", width=8)
    time_choice.set("60")
    time_choice.pack(side="left", padx=5)
    timer_label = tk.Label(controls, text="Ready", bg=BG, fg=PURPLE, font=("Segoe UI", 11, "bold"))
    timer_label.pack(side="left", padx=14)

    transcript = tk.Text(root, height=13, width=110, wrap="word", font=("Segoe UI", 11))
    transcript.pack(fill="both", expand=True, padx=22, pady=8)
    placeholder = "Your recognised speech will appear here. You can also type or edit your answer."
    transcript.insert("1.0", placeholder)
    status = tk.Label(root, text="Ready to practise.", bg=BG, fg=MUTED, font=("Segoe UI", 10))
    status.pack(pady=3)

    state = {
        "running": False, "recording": False, "seconds": 0,
        "stop_event": threading.Event(), "thread": None,
        "frames": [], "sample_rate": 16000, "channels": 1,
        "audio_error": None
    }

    def timer_tick():
        if not state["running"]:
            return
        if state["seconds"] <= 0:
            state["running"] = False
            state["stop_event"].set()
            timer_label.config(text="Time completed")
            status.config(text="Time limit reached. Finishing audio processing...")
            return
        timer_label.config(text=f"{state['seconds']} sec remaining")
        state["seconds"] -= 1
        active_timer["job"] = root.after(1000, timer_tick)

    def reset_placeholder():
        if transcript.get("1.0", "end-1c").strip() == placeholder:
            transcript.delete("1.0", "end")

    def append_status(message):
        status.config(text=message)

    def start():
        if sr is None:
            messagebox.showerror(
                "Speech package missing",
                "Install microphone packages:\npython -m pip install SpeechRecognition PyAudio",
                parent=root
            )
            return
        if state["running"] or state["recording"]:
            return
        reset_placeholder()
        transcript.delete("1.0", "end")
        state["frames"] = []
        state["audio_error"] = None
        state["stop_event"] = threading.Event()
        state["running"] = True
        state["recording"] = True
        state["seconds"] = int(time_choice.get())
        timer_tick()
        status.config(text="Starting microphone. Please wait...")

        def recorder():
            try:
                # Record the whole selected practice into one audio file.
                # PyAudio callback captures audio continuously, including pauses.
                import pyaudio
                pa = pyaudio.PyAudio()
                stream = None
                sample_rate = 16000
                chunk = 1024
                try:
                    stream = pa.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk
                    )
                    safe_after(append_status, "Microphone ready. Speak naturally; your complete answer is recording.")
                    start_time = __import__("time").time()
                    while not state["stop_event"].is_set():
                        data = stream.read(chunk, exception_on_overflow=False)
                        state["frames"].append(data)
                        if __import__("time").time() - start_time >= state["seconds"]:
                            # Timer is also UI-driven; this is a safety stop.
                            state["stop_event"].set()
                            break
                finally:
                    if stream is not None:
                        stream.stop_stream()
                        stream.close()
                    pa.terminate()
            except Exception as exc:
                state["audio_error"] = str(exc)
            finally:
                state["recording"] = False
                state["running"] = False
                safe_after(stop_timer)
                if state["audio_error"]:
                    safe_after(append_status, "Microphone recording failed. You can type your answer manually.")
                    safe_after(messagebox.showerror, "Microphone Error", state["audio_error"])
                elif state["frames"]:
                    safe_after(append_status, "Recording complete. Transcribing the full recording... Please wait.")
                    threading.Thread(target=transcribe_full_recording, daemon=True).start()
                else:
                    safe_after(append_status, "No audio captured. Check microphone permission and try again.")

        state["thread"] = threading.Thread(target=recorder, daemon=True)
        state["thread"].start()

    def transcribe_full_recording():
        temp_path = None
        try:
            if whisper is None:
                # Fallback to Google recognition by processing audio in segments.
                # This is less reliable for long paragraphs; Whisper is recommended.
                recognizer = sr.Recognizer()
                recognised_parts = []
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                with wave.open(temp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(state["sample_rate"])
                    wf.writeframes(b"".join(state["frames"]))
                with sr.AudioFile(temp_path) as source:
                    while True:
                        try:
                            audio = recognizer.record(source, duration=12)
                            if not audio.frame_data:
                                break
                            try:
                                recognised_parts.append(recognizer.recognize_google(audio, language="en-IN"))
                            except sr.UnknownValueError:
                                continue
                        except Exception:
                            break
                result_text = " ".join(recognised_parts).strip()
                if not result_text:
                    raise RuntimeError("No speech was recognised. Try speaking clearly or type your answer.")
            else:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                with wave.open(temp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(state["sample_rate"])
                    wf.writeframes(b"".join(state["frames"]))
                # base model is a good accuracy/speed compromise.
                # Use model='small' for more accuracy on a capable computer.
                model = whisper.load_model("base")
                result = model.transcribe(
                    temp_path,
                    language="en",
                    task="transcribe",
                    fp16=False,
                    verbose=False,
                    condition_on_previous_text=True
                )
                result_text = result.get("text", "").strip()
                if not result_text:
                    raise RuntimeError("No speech was recognised. Try again in a quieter place.")

            def display_transcript():
                transcript.delete("1.0", "end")
                transcript.insert("1.0", result_text)
                status.config(text=f"Transcription completed. {len(result_text.split())} words captured. Review it, then submit for analysis.")
            safe_after(display_transcript)

        except Exception as exc:
            err = str(exc)
            safe_after(append_status, "Transcription failed. You can type/edit your answer in the text box.")
            safe_after(messagebox.showerror, "Transcription Error", err)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def stop():
        if state["recording"] or state["running"]:
            state["stop_event"].set()
            status.config(text="Stopping recording and preparing the full transcript...")
            timer_label.config(text="Stopped")
            stop_timer()
        else:
            status.config(text="Recording is not active. You can edit the transcript or start again.")

    def clear_text():
        if state["recording"]:
            messagebox.showwarning("Recording active", "Stop recording before clearing the transcript.", parent=root)
            return
        transcript.delete("1.0", "end")

    def analyse():
        if state["recording"] or state["running"]:
            messagebox.showwarning(
                "Recording in progress",
                "Press Stop Listening and wait until transcription is complete before analysis.",
                parent=root
            )
            return
        text = transcript.get("1.0", "end-1c").strip()
        if not text or text == placeholder:
            messagebox.showwarning("No answer", "Speak first or type your answer in the box.", parent=root)
            return
        score, feedback, corrected = analyse_text(text, activity)
        save_progress(activity, score)
        full = f"YOUR FULL TRANSCRIPT:\n{text}\n\n{feedback}"
        show_feedback_page(f"📊 {activity} Analysis", full, activity, score, corrected)

    row = tk.Frame(root, bg=BG)
    row.pack(pady=5)
    make_button(row, "🎙 Start Recording", start, GREEN).pack(side="left", padx=5)
    make_button(row, "Stop Listening", stop, ORANGE).pack(side="left", padx=5)
    make_button(row, "Clear Text", clear_text, NAVY).pack(side="left", padx=5)
    make_button(row, "Submit & Analyse", analyse, GREEN).pack(side="left", padx=5)
    back_button(root)

def speaking_page():
    build_speech_page("🎤 Speaking Practice", "Topic: " + random.choice(speaking_topics), "Speaking")

def interview_page():
    build_speech_page("💼 Interview Practice", "Interview question: " + random.choice(interview_questions), "Interview")

# ---------------- GRAMMAR: 5 SETS OF 10 ----------------
def grammar_page():
    clear_page()
    page_heading("📝 Grammar Practice", "Complete 10 questions, submit, then continue to the next set. Total: 50 questions.")
    quiz_state["page"] = 0
    quiz_state["score"] = 0
    quiz_state["selected"] = random.sample(grammar_questions, len(grammar_questions))
    quiz_state["answers"] = [None] * len(grammar_questions)
    render_grammar_set()

def render_grammar_set():
    for widget in root.winfo_children():
        widget.destroy()
    page = quiz_state["page"]
    start_i = page * 10
    batch = quiz_state["selected"][start_i:start_i+10]
    page_heading(f"📝 Grammar Quiz — Set {page+1}/5", f"Questions {start_i+1}–{start_i+10} of 50 | Choose one answer for each.")
    canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(15,0), pady=5)
    scrollbar.pack(side="right", fill="y", pady=5)
    vars_ = []
    for i, (q, opts, correct) in enumerate(batch):
        frame = tk.Frame(inner, bg=WHITE, padx=12, pady=8)
        frame.pack(fill="x", padx=10, pady=5)
        tk.Label(frame, text=f"{start_i+i+1}. {q}", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 11, "bold"), wraplength=1000).pack(anchor="w")
        var = tk.IntVar(value=quiz_state["answers"][start_i+i] if quiz_state["answers"][start_i+i] is not None else -1)
        vars_.append(var)
        for j, option in enumerate(opts):
            tk.Radiobutton(frame, text=option, variable=var, value=j, bg=WHITE,
                           activebackground=WHITE, activeforeground=PURPLE,
                           selectcolor="#EAE8FF", fg="#344054",
                           font=("Segoe UI", 10), cursor="hand2").pack(side="left", padx=10, pady=(6, 0))
    def submit_set():
        unanswered = [i for i, v in enumerate(vars_) if v.get() == -1]
        if unanswered and not messagebox.askyesno("Unanswered", f"{len(unanswered)} question(s) unanswered. Submit this set anyway?"):
            return
        correct_now = 0
        for i, var in enumerate(vars_):
            global_i = start_i+i
            quiz_state["answers"][global_i] = var.get()
            if var.get() == batch[i][2]:
                correct_now += 1
        quiz_state["score"] += correct_now
        if page < 4:
            messagebox.showinfo("Set result", f"Set {page+1}: {correct_now}/10 correct.\nNext set is ready.")
            quiz_state["page"] += 1
            render_grammar_set()
        else:
            final_score = round(quiz_state["score"] * 2)
            grammar_advice = make_improvement_advice("Grammar", final_score,
                f"You answered {quiz_state['score']} out of 50 questions correctly. Review each incorrect answer in the result summary.")
            save_progress("Grammar", final_score, grammar_advice)
            details = [f"Total score: {quiz_state['score']}/50 ({final_score}/100)", ""]
            for i, item in enumerate(quiz_state["selected"]):
                q, opts, correct = item
                given = quiz_state["answers"][i]
                details.append(f"{i+1}. {q}\nYour answer: {opts[given] if given >= 0 else 'Not answered'} | Correct: {opts[correct]}")
            show_feedback_page("📊 Grammar Analysis & Feedback", "\n".join(details) +
                "\n\nTeacher feedback:\n• Revise the rules behind incorrect answers.\n• Practise subject–verb agreement, tenses, articles and prepositions.\n• Review all five sets regularly.", "Grammar", final_score)
    bottom = tk.Frame(root, bg=BG)
    bottom.pack(fill="x", pady=7)
    make_button(bottom, "Submit Set of 10", submit_set, GREEN).pack(side="left", padx=20)
    make_button(bottom, "← Back to Dashboard", dashboard, NAVY).pack(side="left", padx=5)

# ---------------- VOCABULARY ----------------
def vocabulary_page():
    clear_page()
    page_heading("📚 Vocabulary Builder", "Learn one word at a time: think, reveal the meaning, then submit and continue.")
    vocab_state = {"index": 0, "revealed": False, "correct": 0, "attempts": 0}
    order = list(vocabulary)
    random.shuffle(order)
    card = tk.Frame(root, bg=WHITE, padx=35, pady=24, highlightthickness=1, highlightbackground="#E2E6EF")
    card.pack(fill="both", expand=True, padx=50, pady=16)
    counter = tk.Label(card, text="", bg=WHITE, fg=MUTED, font=("Segoe UI", 10, "bold"))
    counter.pack(pady=(0, 12))
    word_label = tk.Label(card, text="", bg=WHITE, fg=PURPLE, font=("Segoe UI", 30, "bold"))
    word_label.pack(pady=12)
    tk.Label(card, text="Think about the meaning, then enter your guess below.",
             bg=WHITE, fg=NAVY, font=("Segoe UI", 11)).pack(pady=6)
    guess = tk.Entry(card, font=("Segoe UI", 12), width=55, relief="solid", bd=1)
    guess.pack(pady=10, ipady=5)
    meaning_label = tk.Label(card, text="", bg=WHITE, fg=GREEN, font=("Segoe UI", 12, "bold"),
                             wraplength=800, justify="center")
    meaning_label.pack(pady=12)
    feedback_label = tk.Label(card, text="", bg=WHITE, fg=MUTED, font=("Segoe UI", 10), wraplength=800)
    feedback_label.pack(pady=5)
    buttons = tk.Frame(card, bg=WHITE)
    buttons.pack(pady=14)
    def render():
        idx = vocab_state["index"]
        if idx >= len(order):
            score = round(vocab_state["correct"] / max(vocab_state["attempts"], 1) * 100)
            advice = make_improvement_advice("Vocabulary", score,
                f"Words completed: {vocab_state['attempts']}. Self-rated correct meanings: {vocab_state['correct']}.")
            save_progress("Vocabulary", score, advice)
            clear_page()
            page_heading("Vocabulary Practice Complete", "Review your result and improvement plan.")
            tk.Label(root, text=f"Completed {len(order)} words\nSelf-rated score: {score}/100\n\n{advice}",
                     bg=WHITE, fg=NAVY, font=("Segoe UI", 13), padx=30, pady=28,
                     wraplength=900, justify="left").pack(fill="both", expand=True, padx=40, pady=20)
            back_button(root)
            return
        word, meaning = order[idx]
        counter.config(text=f"WORD {idx + 1} OF {len(order)}")
        word_label.config(text=word)
        guess.delete(0, "end")
        meaning_label.config(text="")
        feedback_label.config(text="")
        vocab_state["revealed"] = False
        show_btn.config(state="normal")
        submit_btn.config(state="disabled")
        guess.focus_set()
    def show_meaning():
        word, meaning = order[vocab_state["index"]]
        meaning_label.config(text=f"Meaning: {meaning}")
        feedback_label.config(text="Now decide whether your guess was correct, then submit to continue.")
        vocab_state["revealed"] = True
        show_btn.config(state="disabled")
        submit_btn.config(state="normal")
    def submit_next():
        if not vocab_state["revealed"]:
            messagebox.showwarning("Reveal the meaning", "Select Show Meaning before submitting this word.", parent=root)
            return
        word, meaning = order[vocab_state["index"]]
        if not guess.get().strip() and not messagebox.askyesno("No guess entered", "You did not enter a guess. Submit this word anyway?", parent=root):
            return
        correct = messagebox.askyesno("Self-check", f"Word: {word}\nMeaning: {meaning}\n\nDid you understand and correctly guess this meaning?", parent=root)
        vocab_state["attempts"] += 1
        if correct: vocab_state["correct"] += 1
        vocab_state["index"] += 1
        render()
    show_btn = make_button(buttons, "Show Meaning", show_meaning, ORANGE); show_btn.pack(side="left", padx=6)
    submit_btn = make_button(buttons, "Submit & Next Word", submit_next, GREEN); submit_btn.pack(side="left", padx=6)
    make_button(buttons, "← Back to Dashboard", dashboard, NAVY).pack(side="left", padx=6)
    render()

# ---------------- DAILY QUESTIONS ----------------
def questions_page():
    clear_page()
    page_heading("❓ Daily Communication Questions", "Choose a prompt, set a timer, write or speak your answer, then analyse.")
    question_var = tk.StringVar(value=random.choice(daily_questions))
    tk.Label(root, textvariable=question_var, bg=WHITE, fg=NAVY, wraplength=1000,
             font=("Segoe UI", 13, "bold"), padx=18, pady=12).pack(fill="x", padx=22, pady=7)
    row = tk.Frame(root, bg=BG); row.pack(pady=4)
    time_var = tk.StringVar(value="60")
    ttk.Combobox(row, textvariable=time_var, values=["15","30","45","60","90","120"],
                 state="readonly", width=8).pack(side="left", padx=5)
    clock = tk.Label(row, text="Ready", bg=BG, fg=PURPLE, font=("Segoe UI", 11, "bold")); clock.pack(side="left", padx=8)
    answer = tk.Text(root, height=14, wrap="word", font=("Segoe UI", 11)); answer.pack(fill="both", expand=True, padx=22, pady=8)
    def new_question():
        question_var.set(random.choice(daily_questions)); answer.delete("1.0", "end"); stop_timer(); clock.config(text="Ready")
    def start_timer():
        stop_timer(); remaining = {"n": int(time_var.get())}
        def tick():
            if remaining["n"] <= 0:
                clock.config(text="Time completed"); active_timer["job"] = None; return
            clock.config(text=f"{remaining['n']} sec remaining"); remaining["n"] -= 1
            active_timer["job"] = root.after(1000, tick)
        tick()
    def submit():
        text = answer.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Answer", "Please type your answer, or use Interview/Speaking Practice for microphone."); return
        score, feedback, corrected = analyse_text(text, "Daily Questions")
        save_progress("Daily Questions", score)
        show_feedback_page("📊 Daily Question Feedback", f"Question: {question_var.get()}\n\nYour answer:\n{text}\n\n{feedback}", "Daily Questions", score, corrected)
    buttons = tk.Frame(root, bg=BG); buttons.pack(pady=4)
    make_button(buttons, "Start Timer", start_timer).pack(side="left", padx=4)
    make_button(buttons, "Next Question", new_question, NAVY).pack(side="left", padx=4)
    make_button(buttons, "Submit & Analyse", submit, GREEN).pack(side="left", padx=4)
    make_button(buttons, "Answer with Microphone", lambda: build_speech_page("❓ Daily Question — Voice Answer", question_var.get(), "Daily Questions"), ORANGE).pack(side="left", padx=4)
    back_button(root)

# ---------------- PRONUNCIATION ----------------
def pronunciation_page():
    clear_page()
    page_heading("🗣 Pronunciation Practice", "Practise one word at a time. Read it aloud, reveal a learning tip, then submit and continue.")
    state = {"index": 0, "completed": 0}; words = list(pronunciation_words); random.shuffle(words)
    card = tk.Frame(root, bg=WHITE, padx=35, pady=22, highlightthickness=1, highlightbackground="#E2E6EF")
    card.pack(fill="both", expand=True, padx=55, pady=16)
    counter = tk.Label(card, text="", bg=WHITE, fg=MUTED, font=("Segoe UI", 10, "bold")); counter.pack(pady=(0, 10))
    word_label = tk.Label(card, text="", bg=WHITE, fg=PURPLE, font=("Segoe UI", 30, "bold")); word_label.pack(pady=16)
    tip = tk.Label(card, text="Read the word slowly. Break it into syllables if it feels difficult.",
                   bg=WHITE, fg=NAVY, font=("Segoe UI", 11), wraplength=800); tip.pack(pady=8)
    result = tk.Label(card, text="", bg=WHITE, fg=GREEN, font=("Segoe UI", 11, "bold"), wraplength=800); result.pack(pady=10)
    row = tk.Frame(card, bg=WHITE); row.pack(pady=16)
    def render():
        if state["index"] >= len(words):
            score = round(state["completed"] / max(len(words), 1) * 100)
            advice = make_improvement_advice("Pronunciation", score, f"Words marked as practised: {state['completed']} out of {len(words)}.")
            save_progress("Pronunciation", score, advice); clear_page()
            page_heading("Pronunciation Practice Complete", "Your practice summary and next steps")
            tk.Label(root, text=f"Words practised: {state['completed']}/{len(words)}\nPractice completion score: {score}/100\n\n{advice}",
                     bg=WHITE, fg=NAVY, font=("Segoe UI", 13), padx=30, pady=28, wraplength=900, justify="left").pack(fill="both", expand=True, padx=40, pady=20)
            back_button(root); return
        counter.config(text=f"WORD {state['index'] + 1} OF {len(words)}"); word_label.config(text=words[state["index"]])
        tip.config(text="Read the word slowly. Break it into syllables if it feels difficult. Use the microphone option to compare the recognised word.")
        result.config(text=""); reveal_btn.config(state="normal"); next_btn.config(state="disabled")
    def reveal_tip():
        word = words[state["index"]]
        tip.config(text=f"Practice tip for '{word}': say it slowly three times, listen to a dictionary pronunciation, notice the stressed syllable, and then use it in a sentence.")
        result.config(text="After practising, select Submit & Next Word."); reveal_btn.config(state="disabled"); next_btn.config(state="normal")
    def microphone_practice():
        word = words[state["index"]]
        build_speech_page("🗣 Pronunciation — Voice Check", f"Pronounce this word clearly: {word}. The transcript can help you compare the recognised result.", "Pronunciation")
    def next_word():
        if not messagebox.askyesno("Submit pronunciation practice", "Have you practised this word aloud? Submit and continue?", parent=root): return
        state["completed"] += 1; state["index"] += 1; render()
    reveal_btn = make_button(row, "Show Practice Tip", reveal_tip, ORANGE); reveal_btn.pack(side="left", padx=5)
    next_btn = make_button(row, "Submit & Next Word", next_word, GREEN); next_btn.pack(side="left", padx=5)
    make_button(row, "Practise with Microphone", microphone_practice, PURPLE).pack(side="left", padx=5)
    make_button(row, "← Back to Dashboard", dashboard, NAVY).pack(side="left", padx=5)
    render()

# ---------------- PROGRESS & GRAPH ----------------
def progress_page():
    clear_page()
    page_heading("📈 Daily Progress & Performance Graph", "Progress is saved separately for each logged-in user.")
    cur.execute("SELECT activity, score, date, COALESCE(improvement_feedback, '') FROM progress WHERE username=? ORDER BY id DESC LIMIT 100",
                (current_user["name"],))
    records = cur.fetchall(); total = len(records)
    avg = round(sum(r[1] for r in records)/total) if total else 0
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for r in records if r[2].startswith(today))
    summary = tk.Frame(root, bg=BG); summary.pack(pady=5)
    for label, value in [("Total Practices", total), ("Average Score", f"{avg}/100"), ("Today's Practices", today_count)]:
        card = tk.Frame(summary, bg=WHITE, padx=20, pady=10); card.pack(side="left", padx=7)
        tk.Label(card, text=str(value), bg=WHITE, fg=PURPLE, font=("Segoe UI", 17, "bold")).pack()
        tk.Label(card, text=label, bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack()
    if records:
        if HAS_MATPLOTLIB:
            chart_frame = tk.Frame(root, bg=BG); chart_frame.pack(fill="both", expand=True, padx=20, pady=5)
            chronological = list(reversed(records[:20]))
            fig = Figure(figsize=(8.5, 3.0), dpi=90); ax = fig.add_subplot(111)
            scores = [r[1] for r in chronological]; labels = [f"{i+1}" for i in range(len(scores))]
            ax.plot(labels, scores, marker="o"); ax.set_title("Last practice scores")
            ax.set_xlabel("Practice (oldest → newest)"); ax.set_ylabel("Score / 100"); ax.set_ylim(0, 105); ax.grid(True, alpha=0.3)
            fig.tight_layout(); canvas = FigureCanvasTkAgg(fig, master=chart_frame); canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(root, text="Install matplotlib for a graph: python -m pip install matplotlib", bg=BG, fg=ORANGE).pack(pady=4)
        table_frame = tk.Frame(root, bg=BG); table_frame.pack(fill="both", expand=True, padx=22, pady=5)
        tree = ttk.Treeview(table_frame, columns=("Activity","Score","Date","Improvement Feedback"), show="headings", height=7)
        for col, width in [("Activity",170),("Score",80),("Date",155),("Improvement Feedback",600)]:
            tree.heading(col, text=col); tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for activity, score, date, feedback in records:
            tree.insert("", "end", values=(activity, f"{score}/100", date, feedback))
    else:
        tk.Label(root, text="No progress yet. Complete any practice to see your graph and history.", bg=BG, fg=MUTED, font=("Segoe UI", 12)).pack(pady=30)
    back_button(root)

# ---------------- CLOSE APP ----------------
def on_close():
    stop_timer()
    try:
        db.commit()
        db.close()
    except Exception:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
welcome_page()
root.mainloop()
