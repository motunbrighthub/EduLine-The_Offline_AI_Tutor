import gradio as gr
import pandas as pd
import sqlite3
import random

# ====================================================
# Database Setup
# ====================================================
DB_FILE = "quiz_progress.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user TEXT,
            subject TEXT,
            cluster INTEGER,
            score INTEGER,
            total INTEGER
        )
    """)
    conn.commit()
    conn.close()


init_db()

# ====================================================
# Load Questions Dataset
# ====================================================
df = pd.read_csv("questions_clus8.csv")

# ====================================================
# Cluster Topics Mapping
# ====================================================
cluster_topics = {
    0: {"English": "Verb Tenses, Sentence Completion",
        "Mathematics": "Basic Arithmetic, Word Problems"},
    1: {"English": "Spelling, Vocabulary",
        "Mathematics": "Number Properties"},
    2: {"English": "Grammar (Sentence Structure)",
        "Mathematics": "Equations, Expressions"},
    3: {"English": "Parts of Speech (Adjectives, Nouns)",
        "Mathematics": "Geometry Basics"},
    4: {"English": "Synonyms, Antonyms, Vocabulary",
        "Mathematics": "Basic Operations"},
    5: {"English": "Passive Voice, Opposites",
        "Mathematics": "Simple Calculations"},
    6: {"English": "Prepositions, Conjunctions",
        "Mathematics": "Fractions, Decimals"},
    7: {"English": "Minor Grammar",
        "Mathematics": "Ratios, Word Problems"},
    8: {"Mathematics": "Algebra, Fractions, Equations"}
}

# ====================================================
# Quiz State
# ====================================================
quiz = {
    "user": None,
    "subject": None,
    "questions": [],
    "question_index": 0,
    "score": 0,
    "total_questions": 0,
    "weak_clusters": []
}


# ====================================================
# Functions
# ====================================================

def save_progress(user, subject, cluster, score, total):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO progress VALUES (?, ?, ?, ?, ?)",
              (user, subject, cluster, score, total))
    conn.commit()
    conn.close()


def get_question_options(row):
    return [row["OptionA"], row["OptionB"], row["OptionC"], row["OptionD"]]


def start_quiz(user, subject):
    if subject not in ["English", "Mathematics"]:
        return gr.update(visible=False), "Please select a valid subject."

    quiz["user"] = user.strip()
    quiz["subject"] = subject
    subject_df = df[df["Subject"] == subject]

    if subject_df.empty:
        return gr.update(visible=False), f"No questions available for {subject}."

    sampled = subject_df.groupby("Cluster").apply(
        lambda x: x.sample(min(len(x), 3))
    ).reset_index(drop=True)

    quiz["questions"] = sampled.to_dict(orient="records")
    quiz["question_index"] = 0
    quiz["score"] = 0
    quiz["total_questions"] = len(quiz["questions"])
    quiz["weak_clusters"] = []

    return gr.update(visible=True), f"Starting {subject} quiz with {quiz['total_questions']} questions!"


def load_next_question():
    if quiz["question_index"] >= quiz["total_questions"]:
        # Save final score once
        save_progress(quiz["user"], quiz["subject"], -1, quiz["score"], quiz["total_questions"])
        return (
            "🎉 Quiz Complete!",
            [],
            gr.update(interactive=False),
            gr.update(interactive=False),
            f"Your score: {quiz['score']} / {quiz['total_questions']}",
            gr.update(value=1.0),
            gr.update(visible=False),
            gr.update(visible=True)
        )

    q = quiz["questions"][quiz["question_index"]]
    options = get_question_options(q)
    progress_val = quiz["question_index"] / quiz["total_questions"]

    return (
        q["Question"],
        gr.update(choices=options, value=None),
        gr.update(interactive=True),
        gr.update(interactive=False),
        "",
        gr.update(value=progress_val),
        gr.update(visible=True),
        gr.update(visible=False)
    )


def submit_answer(answer):
    q = quiz["questions"][quiz["question_index"]]
    correct = q["Answer"]

    if answer == correct:
        quiz["score"] += 1
        feedback = "✅ Correct!"
    else:
        feedback = f"❌ Incorrect. Correct answer: {correct}"

    return (
        feedback,
        gr.update(interactive=False),
        gr.update(interactive=True)
    )


def next_question():
    quiz["question_index"] += 1
    return load_next_question()


def quit_quiz():
    # Save progress if quit early
    save_progress(quiz["user"], quiz["subject"], -1, quiz["score"], quiz["total_questions"])
    return (
        "🚪 Quiz Ended.",
        [],
        gr.update(interactive=False),
        gr.update(interactive=False),
        f"Your score: {quiz['score']} / {quiz['total_questions']}",
        gr.update(value=1.0),
        gr.update(visible=False),
        gr.update(visible=True)
    )


def review_weak_clusters():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT cluster, score, total FROM progress WHERE user=? AND subject=?",
              (quiz["user"], quiz["subject"]))
    rows = c.fetchall()
    conn.close()

    weak = []
    for cl, sc, total in rows:
        if cl >= 0 and total > 0 and sc / total < 0.5:
            weak.append(cl)

    quiz["weak_clusters"] = list(set(weak))

    if quiz["weak_clusters"]:
        topics = []
        for cl in quiz["weak_clusters"]:
            if quiz["subject"] in cluster_topics.get(cl, {}):
                topics.append(f"Cluster {cl}: {cluster_topics[cl][quiz['subject']]}")
        if topics:
            return "⚠️ You need to review these areas:\n" + "\n".join(topics)
        else:
            return "No weak clusters identified for your subject."
    else:
        return "🎉 No weak clusters! Great job."


# ====================================================
# Gradio UI
# ====================================================
with gr.Blocks() as demo:
    gr.Markdown("## 📝 Eduline Adaptive Quiz")

    with gr.Tab("Start Quiz"):
        user = gr.Textbox(label="Enter your name")
        subject = gr.Dropdown(["English", "Mathematics"], label="Select Subject")
        start_btn = gr.Button("Start Quiz")
        start_info = gr.Markdown("")

    with gr.Group(visible=False) as quiz_page:
        gr.Markdown("### Quiz in Progress")
        quiz_progress = gr.Slider(
            minimum=0, maximum=1.0, value=0, step=0.01,
            label="Progress", interactive=False
        )
        question_text = gr.Markdown()
        choice_radio = gr.Radio([], label="Choose an answer:", interactive=True)
        submit_btn = gr.Button("Submit Answer", interactive=True)
        next_btn = gr.Button("Next Question", interactive=False, variant="primary")
        quit_btn = gr.Button("Quit Quiz")
        quiz_feedback = gr.Markdown("")
        score_info = gr.Markdown("")

    with gr.Group(visible=False) as review_page:
        review_btn = gr.Button("Review Weak Clusters")
        review_info = gr.Markdown("")

    # Button wiring
    start_btn.click(
        start_quiz,
        inputs=[user, subject],
        outputs=[quiz_page, start_info]
    ).then(
        load_next_question,
        outputs=[question_text, choice_radio, submit_btn, next_btn,
                 quiz_feedback, quiz_progress, quiz_page, review_page]
    )

    submit_btn.click(
        submit_answer,
        inputs=[choice_radio],
        outputs=[quiz_feedback, submit_btn, next_btn]
    )

    next_btn.click(
        next_question,
        outputs=[question_text, choice_radio, submit_btn, next_btn,
                 quiz_feedback, quiz_progress, quiz_page, review_page]
    )

    quit_btn.click(
        quit_quiz,
        outputs=[question_text, choice_radio, submit_btn, next_btn,
                 quiz_feedback, quiz_progress, quiz_page, review_page]
    )

    review_btn.click(
        review_weak_clusters,
        outputs=[review_info]
    )

# ====================================================
# Launch App
# ====================================================
if __name__ == "__main__":
    demo.launch()

