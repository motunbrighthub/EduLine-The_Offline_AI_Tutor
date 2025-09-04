import gradio as gr
import pandas as pd
import random
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List

# ==============================
# Config
# ==============================
import os
BASE_DIR = os.path.dirname(__file__)
QUESTIONS_CSV = os.path.join(BASE_DIR, "questions_clus8.csv")
DB_PATH = "eduline.db"
DEFAULT_TOTAL_Q = 5
CLUSTER_LIMITS = {"English": 7, "Mathematics": 8}
MIN_CLUSTER = 1

# ==============================
# Database utils
# ==============================
def init_db(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_uuid TEXT UNIQUE,
            name TEXT,
            area TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_uuid TEXT,
            subject TEXT,
            score INTEGER,
            total_questions INTEGER,
            progress REAL,
            weak_clusters_json TEXT,
            taken_at TEXT
        )
    """)
    conn.commit()
    return conn

def insert_user(conn, student_uuid: str, name: str, area: str):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (student_uuid, name, area, created_at) VALUES (?, ?, ?, ?)
    """, (student_uuid, name, area, datetime.now().isoformat()))
    conn.commit()

def save_result(conn, student_uuid: str, subject: str, score: int, total_questions: int, progress: float, weak_clusters: dict):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO results (student_uuid, subject, score, total_questions, progress, weak_clusters_json, taken_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_uuid, subject, score, total_questions, progress, json.dumps(weak_clusters), datetime.now().isoformat()))
    conn.commit()

conn = init_db(DB_PATH)

# ==============================
# Load questions
# ==============================
def load_questions(path):
    df = pd.read_csv(path)
    df["Cluster"] = df["Cluster"].astype(int)
    return df
df_all = load_questions(QUESTIONS_CSV)
SUBJECTS = sorted(df_all["Subject"].unique())

# ==============================
# Helpers
# ==============================
def gen_uuid() -> str:
    return "EDU-" + str(uuid.uuid4())[:8].upper()

def get_cluster_name(subject: str, cluster_id: int) -> str:
    defaults = {1: "Foundations", 2: "Basics", 3: "Practice", 4: "Intermediate", 5: "Advanced Practice", 6: "Advanced", 7: "Expert", 8: "Mastery"}
    return defaults.get(cluster_id, f"Cluster {cluster_id}")

# ==============================
# Gradio app functions
# ==============================

def initialize_state():
    return {
        "stage": "register",
        "student_uuid": None,
        "name": "",
        "area": "",
        "quiz": {
            "started": False,
            "subject": None,
            "cluster": 0,
            "question_index": 0,
            "total_questions": DEFAULT_TOTAL_Q,
            "score": 0,
            "used_indices": [],
            "current_question": None,
            "submitted": False,
            "feedback": "",
            "weak_clusters": {},
            "mode": "normal",
            "weak_only_list": [],
        }
    }

def handle_registration(name, area, state):
    student_uuid = gen_uuid()
    state["student_uuid"] = student_uuid
    state["name"] = name.strip()
    state["area"] = area
    state["stage"] = "subject"
    try:
        insert_user(conn, student_uuid, state["name"], state["area"])
        feedback = f"Registered! Your Student ID is: **{student_uuid}**"
    except Exception as e:
        feedback = f"Could not save registration: {e}"
    
    return state, gr.update(visible=True), gr.update(visible=False), feedback

def start_quiz(subject, total_questions, state):
    mid = CLUSTER_LIMITS.get(subject, 6) // 2
    state["quiz"].update({
        "started": True,
        "subject": subject,
        "cluster": mid,
        "question_index": 0,
        "total_questions": total_questions,
        "score": 0,
        "used_indices": [],
        "current_question": None,
        "submitted": False,
        "feedback": "",
        "weak_clusters": {},
        "mode": "normal",
        "weak_only_list": []
    })
    state["stage"] = "quiz"
    return state, *load_next_question(state)

def start_weak_quiz(subject, total_questions, state):
    weak_list = [c for c, m in state["quiz"]["weak_clusters"].items() if m > 0]
    if not weak_list:
        return state, gr.update(visible=True), "No recorded weak areas yet. Try a normal quiz first."
    
    mid = CLUSTER_LIMITS.get(subject, 6) // 2
    state["quiz"].update({
        "started": True,
        "subject": subject,
        "cluster": weak_list[0] if weak_list else mid,
        "question_index": 0,
        "total_questions": total_questions,
        "score": 0,
        "used_indices": [],
        "current_question": None,
        "submitted": False,
        "feedback": "",
        "weak_clusters": {c: 0 for c in weak_list},
        "mode": "weak_only",
        "weak_only_list": weak_list
    })
    state["stage"] = "quiz"
    return state, *load_next_question(state)

def load_next_question(state):
    quiz = state["quiz"]
    df_subj = df_all[df_all["Subject"] == quiz["subject"]]
    
    target_cluster = quiz["cluster"]
    if quiz["mode"] == "weak_only" and quiz["weak_only_list"]:
        if target_cluster not in quiz["weak_only_list"]:
            target_cluster = random.choice(quiz["weak_only_list"])
            quiz["cluster"] = target_cluster
    
    subset = df_subj[df_subj["Cluster"] == target_cluster].drop(quiz["used_indices"], errors="ignore")
    if subset.empty:
        if quiz["mode"] == "weak_only" and quiz["weak_only_list"]:
            subset = df_subj[df_subj["Cluster"].isin(quiz["weak_only_list"])].drop(quiz["used_indices"], errors="ignore")
        else:
            subset = df_subj.drop(quiz["used_indices"], errors="ignore")
    
    if subset.empty:
        state["stage"] = "finished"
        return state, gr.update(visible=False), "No more questions available for this subject/mode.", "Completed", "0%", "0/0"
    
    q = subset.sample(1).iloc[0]
    quiz["current_question"] = q.to_dict()
    quiz["used_indices"].append(q.name)
    quiz["submitted"] = False
    
    friendly_name = get_cluster_name(quiz["subject"], quiz["cluster"])
    question_text = q["Question"]
    options = {
        "A": q["Option A"], 
        "B": q["Option B"], 
        "C": q["Option C"], 
        "D": q["Option D"]
    }
    progress_val = quiz["question_index"] / quiz["total_questions"]
    progress_text = f"Question {quiz['question_index'] + 1} of {quiz['total_questions']}"
    score_text = f"Score: {quiz['score']}"
    
    return (
        state, 
        gr.update(visible=True), 
        gr.update(value=question_text), 
        gr.update(value=list(options.keys())), 
        gr.update(label=f"Topic: **{friendly_name}** (Cluster {quiz['cluster']})"), 
        gr.update(value=progress_val), 
        gr.update(value=progress_text),
        gr.update(value=score_text),
        gr.update(value=None), # reset radio button
        "" # clear feedback
    )

def handle_submit(choice, state):
    quiz = state["quiz"]
    q = quiz["current_question"]
    correct = str(q["Correct Answer"]).strip().upper()
    cluster_at_time = q["Cluster"]

    if choice == correct:
        quiz["score"] += 1
        if quiz["mode"] == "normal":
            quiz["cluster"] = min(CLUSTER_LIMITS.get(quiz["subject"], quiz["cluster"] + 1), quiz["cluster"] + 1)
        feedback = "✅ Correct! Great job."
    else:
        if quiz["mode"] == "normal":
            quiz["cluster"] = max(MIN_CLUSTER, quiz["cluster"] - 1)
        feedback = f"❌ Wrong! Correct answer: {correct}"
        quiz["weak_clusters"][cluster_at_time] = quiz["weak_clusters"].get(cluster_at_time, 0) + 1
    
    quiz["submitted"] = True
    
    score_text = f"Score: {quiz['score']}"
    
    return state, feedback, gr.update(interactive=False), gr.update(interactive=True), gr.update(value=score_text)

def next_question(state):
    quiz = state["quiz"]
    quiz["question_index"] += 1
    
    if quiz["question_index"] >= quiz["total_questions"]:
        finish_and_record(state)
        return state, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
    
    return state, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), *load_next_question(state)

def finish_and_record(state):
    quiz = state["quiz"]
    progress_ratio = quiz["question_index"] / max(1, quiz["total_questions"])
    try:
        save_result(conn, state["student_uuid"], quiz["subject"], quiz["score"], quiz["total_questions"], progress_ratio, quiz["weak_clusters"])
    except Exception as e:
        print(f"Could not save results to DB: {e}")
    
    quiz["started"] = False
    state["stage"] = "finished"
    return state

def display_results(state):
    quiz = state["quiz"]
    result_text = f"**Final Score:** {quiz['score']} / {quiz['total_questions']}"
    weak_areas = ""
    if quiz["weak_clusters"]:
        weak_areas += "### ⚠ Weak Areas\n"
        sorted_weak = sorted(quiz["weak_clusters"].items(), key=lambda x: -x[1])
        for cl, misses in sorted_weak:
            weak_areas += f"- {get_cluster_name(quiz['subject'], cl)} (Cluster {cl}): {misses} mistake(s)\n"
    
    return state, gr.update(visible=True), gr.update(value=result_text), gr.update(value=weak_areas), gr.update(visible=True)

def return_to_subject(state):
    state["stage"] = "subject"
    return state, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)

def quit_quiz(state):
    finish_and_record(state)
    return state, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

# ==============================
# Gradio Blocks UI
# ==============================
with gr.Blocks(title="EDULINE Adaptive Quiz") as demo:
    state = gr.State(value=initialize_state())
    
    gr.Markdown("## 🎓 EDULINE\n### The Offline AI Tutor")

    # ==============================
    # Stage 1: Registration
    # ==============================
    with gr.Group(visible=True) as register_page:
        gr.Markdown("### 👋 Welcome! Create your student profile")
        name_input = gr.Text(label="Name (optional)")
        area_radio = gr.Radio(["Urban", "Rural"], label="Where do you live?", value="Urban")
        reg_btn = gr.Button("Create Student ID")
        reg_feedback = gr.Markdown("")

    # ==============================
    # Stage 2: Subject Selection
    # ==============================
    with gr.Group(visible=False) as subject_page:
        welcome_md = gr.Markdown("")
        subject_dropdown = gr.Dropdown(SUBJECTS, label="Select subject:")
        total_q_slider = gr.Slider(3, 20, value=DEFAULT_TOTAL_Q, step=1, label="How many questions this round?")
        
        with gr.Row():
            start_btn = gr.Button("Start Adaptive Quiz")
            retry_weak_btn = gr.Button("Retry Weak Areas (if any)")
        subject_feedback = gr.Markdown("")

    # ==============================
    # Stage 3: Quiz
    # ==============================
    with gr.Group(visible=False) as quiz_page:
        gr.Markdown("### Quiz in Progress")
        quiz_subject_md = gr.Markdown("")
        quiz_info_md = gr.Markdown("")
        quiz_progress = gr.Progress(0, 1.0)
        
        with gr.Row():
            q_info = gr.Markdown("")
            score_info = gr.Markdown("")

        topic_info = gr.Markdown("")
        question_text = gr.Markdown()
        choice_radio = gr.Radio(["A", "B", "C", "D"], label="Choose an answer:", interactive=True)
        
        with gr.Row():
            submit_btn = gr.Button("Submit Answer", interactive=True)
            next_btn = gr.Button("Next Question", interactive=False, variant="primary")
            quit_btn = gr.Button("Quit Quiz")
        quiz_feedback = gr.Markdown("")

    # ==============================
    # Stage 4: Finished
    # ==============================
    with gr.Group(visible=False) as finished_page:
        gr.Markdown("### 🎓 Quiz Completed!")
        score_md = gr.Markdown()
        weak_areas_md = gr.Markdown()
        
        with gr.Row():
            retry_weak_after_finish_btn = gr.Button("Retry Weak Areas")
            choose_another_subject_btn = gr.Button("Choose Another Subject")

    # ==============================
    # Event listeners
    # ==============================
    reg_btn.click(
        fn=handle_registration,
        inputs=[name_input, area_radio, state],
        outputs=[state, subject_page, register_page, welcome_md]
    )

    start_btn.click(
        fn=start_quiz,
        inputs=[subject_dropdown, total_q_slider, state],
        outputs=[state, quiz_page, subject_page, question_text, choice_radio, topic_info, quiz_progress, q_info, score_info, gr.update(value=None), quiz_feedback]
    )
    
    retry_weak_btn.click(
        fn=start_weak_quiz,
        inputs=[subject_dropdown, total_q_slider, state],
        outputs=[state, quiz_page, subject_feedback]
    )

    submit_btn.click(
        fn=handle_submit,
        inputs=[choice_radio, state],
        outputs=[state, quiz_feedback, submit_btn, next_btn, score_info]
    )
    
    next_btn.click(
        fn=next_question,
        inputs=[state],
        outputs=[state, quiz_page, finished_page, finished_page] # update visibility of pages
    ).then(
        fn=lambda: [gr.update(interactive=True), gr.update(interactive=False)], # enable submit, disable next
        inputs=[],
        outputs=[submit_btn, next_btn]
    )

    quit_btn.click(
        fn=quit_quiz,
        inputs=[state],
        outputs=[state, quiz_page, finished_page, finished_page]
    ).then(
        fn=lambda: [gr.update(interactive=True), gr.update(interactive=False)],
        inputs=[],
        outputs=[submit_btn, next_btn]
    )

    demo.load(
        fn=lambda s: [gr.update(visible=True) if s["stage"] == "finished" else gr.update(visible=False), # finished page
                      gr.update(visible=True) if s["stage"] == "quiz" else gr.update(visible=False), # quiz page
                      gr.update(visible=True) if s["stage"] == "subject" else gr.update(visible=False), # subject page
                      gr.update(visible=True) if s["stage"] == "register" else gr.update(visible=False), # register page
                     ],
        inputs=[state],
        outputs=[finished_page, quiz_page, subject_page, register_page]
    )

    choose_another_subject_btn.click(
        fn=return_to_subject,
        inputs=[state],
        outputs=[state, finished_page, subject_page, quiz_page]
    )
    
    retry_weak_after_finish_btn.click(
        fn=start_weak_quiz,
        inputs=[subject_dropdown, total_q_slider, state],
        outputs=[state, quiz_page, subject_feedback]
    )

if __name__ == "__main__":
    demo.launch()
