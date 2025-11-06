from __future__ import annotations  

import random
import time
import tkinter as tk
from tkinter import messagebox
from typing import Tuple

DIFFICULTY_BOUNDS = {1: ("Easy", 1, 9), 2: ("Moderate", 10, 99), 3: ("Advanced", 1000, 9999)}
TOTAL_QUESTIONS = 10
PTS_FIRST, PTS_SECOND = 10, 5
BG_COLOR = "#000000"
FG_COLOR = "#FFFFFF"
ENTRY_BG = "#111111"
BUTTON_BG = BG_COLOR
SELECT_COLOR = "#242424"


# =============================================================================
# Helper functions
# -----------------------------------------------------------------------------
def rank_from_percentage(pct: int) -> str:
    """Map percentage to letter grade (criterion-referenced thresholding)."""
    if pct >= 90:
        return "A+"
    if pct >= 80:
        return "A"
    if pct >= 70:
        return "B"
    if pct >= 60:
        return "C"
    if pct >= 50:
        return "D"
    return "F"


def compute(a: int, op: str, b: int) -> int:
    """Evaluate a binary operation (+ or −) on integers; constant time."""
    return a + b if op == "+" else a - b


# =============================================================================
# Required interface functions 
# -----------------------------------------------------------------------------
# These functions separate UI orchestration from core logic
# =============================================================================
def displayMenu(app: "QuizApp") -> None:
    """Show the difficulty menu frame at the start of each play."""
    app.show_menu()


def randomInt(level: int) -> Tuple[int, int]:
    """Generate two ints constrained by difficulty level (content validity)."""
    _, lo, hi = DIFFICULTY_BOUNDS[level]
    return random.randint(lo, hi), random.randint(lo, hi)


def decideOperation() -> str:
    """Randomly pick '+' or '-' (ensures item variety)."""
    return random.choice(["+", "-"])


def displayProblem(app: "QuizApp", a: int, op: str, b: int, *, clear_feedback: bool = True) -> None:
    """Render the current item, reset input focus; avoids stale feedback."""
    app.var_question.set(f"{a} {op} {b} =")
    if clear_feedback:
        app.var_feedback.set("")
    app.entry.delete(0, tk.END)
    app.entry.focus_set()


def isCorrect(a: int, op: str, b: int, user_answer: int, app: "QuizApp") -> bool:
    """
    Compare response to key; update formative feedback.
    Returns True on mastery for this item, False otherwise.
    """
    correct = compute(a, op, b)
    if user_answer == correct:
        app.var_feedback.set("✅ Correct!")
        return True
    if app.attempt == 1:
        app.var_feedback.set("Wrong ❌ : Try again!")
    else:
        app.var_feedback.set(f"Wrong ❌ : The answer was {correct}.")
    return False


def displayResults(app: "QuizApp") -> None:
    """
    Summative report: raw score, percent, letter grade, attempt breakdown,
    and elapsed time. Offers immediate retest to support spaced practice.
    """
    total_possible = TOTAL_QUESTIONS * PTS_FIRST
    pct = round((app.score / total_possible) * 100)
    grade = rank_from_percentage(pct)
    elapsed = time.perf_counter() - app.start_time if app.start_time else 0.0
    msg = (
        f"Difficulty: {DIFFICULTY_BOUNDS[app.level][0]}\n"
        f"Score: {app.score}/{total_possible}  ({pct}%)\n"
        f"Grade: {grade}\n"
        f"First-try correct: {app.first_try_correct}/{TOTAL_QUESTIONS}\n"
        f"Second-try correct: {app.second_try_correct}/{TOTAL_QUESTIONS}\n"
        f"Time: {elapsed:.1f}s"
    )
    again = messagebox.askyesno("Results", msg + "\n\nPlay again?")
    if again:
        app.reset_for_new_play()
        displayMenu(app)
    else:
        app.root.destroy()


# =============================================================================
# Application class (stateful controller for the GUI)
# -----------------------------------------------------------------------------
# Encapsulates state (level, score, attempt counters) and view bindings.
# Methods implement the quiz finite-state flow: menu -> run -> results.
# =============================================================================
class QuizApp:
    """Small Tkinter app that orchestrates the quiz flow."""

    def __init__(self, root: tk.Tk) -> None:
        # ---- Root window and theme ----
        self.root = root
        self.root.title("Maths Quiz — Advanced Python")
        self.root.configure(bg=BG_COLOR)

        # ---- Assessment state (invariants reset between plays) ----
        self.level = 1
        self.q_index = 0
        self.score = 0
        self.attempt = 1
        self.first_try_correct = 0
        self.second_try_correct = 0
        self.start_time = 0.0  # perf_counter baseline for simple RT metric
        self.a = 0
        self.b = 0
        self.op = "+"

        # ---- Observable UI variables (data binding to labels/entries) ----
        self.var_question = tk.StringVar(value="")
        self.var_feedback = tk.StringVar(value="")
        self.var_progress = tk.StringVar(value="")
        self.var_score = tk.StringVar(value="Score: 0")
        self.var_level = tk.IntVar(value=1)

        # ---- Menu frame (selection of difficulty) ----
        self.menu = tk.Frame(root, padx=12, pady=12, bg=BG_COLOR)
        tk.Label(self.menu, text="DIFFICULTY LEVEL", font=("Segoe UI", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(0, 6))
        for val, text in [(1, "1. Easy"), (2, "2. Moderate"), (3, "3. Advanced")]:
            tk.Radiobutton(
                self.menu,
                text=text,
                variable=self.var_level,
                value=val,
                anchor="w",
                bg=BG_COLOR,
                fg=FG_COLOR,
                selectcolor=SELECT_COLOR,
                activebackground=BG_COLOR,
                activeforeground=FG_COLOR,
                highlightbackground=BG_COLOR,
            ).pack(fill="x")
        tk.Button(
            self.menu,
            text="Start Quiz",
            command=self.start_quiz,
            bg=FG_COLOR,
            fg=BG_COLOR,
            activebackground="#d0d0d0",
            activeforeground=BG_COLOR,
            highlightbackground=BG_COLOR,
        ).pack(pady=(8, 0))

        # ---- Quiz frame (progress, item stem, response, feedback) ----
        self.quiz = tk.Frame(root, padx=12, pady=12, bg=BG_COLOR)
        top = tk.Frame(self.quiz, bg=BG_COLOR)
        top.pack(fill="x")
        tk.Label(top, textvariable=self.var_progress, font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
        tk.Label(top, textvariable=self.var_score, font=("Segoe UI", 10), bg=BG_COLOR, fg=FG_COLOR).pack(side="right")

        tk.Label(self.quiz, textvariable=self.var_question, font=("Consolas", 16, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(14, 8))
        entry_row = tk.Frame(self.quiz, bg=BG_COLOR)
        entry_row.pack()
        self.entry = tk.Entry(
            entry_row,
            width=12,
            font=("Consolas", 14),
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,  # makes cursor visible on dark bg
            highlightbackground=BG_COLOR,
            highlightcolor=FG_COLOR,
        )
        self.entry.pack(side="left")
        tk.Button(
            entry_row,
            text="Submit",
            command=self.submit_answer,
            bg=BUTTON_BG,
            fg=FG_COLOR,
            activebackground=SELECT_COLOR,
            activeforeground=FG_COLOR,
            highlightbackground=BG_COLOR,
        ).pack(side="left", padx=6)
        tk.Label(self.quiz, textvariable=self.var_feedback, bg=BG_COLOR, fg=FG_COLOR).pack(pady=(8, 0))

        # ---- Key binding (accessibility: Enter submits) ----
        self.root.bind("<Return>", lambda e: self.submit_answer())

        displayMenu(self)  # initial state: show menu

    # --------- UI transitions and flow (state machine) ----------
    def show_menu(self) -> None:
        """Activate menu view; hide quiz view (single-view visible at once)."""
        self.quiz.pack_forget()
        self.menu.pack(fill="both", expand=True)

    def start_quiz(self) -> None:
        """Initialize a run: set level, reset state, timestamp, then pose Q1."""
        self.level = int(self.var_level.get())
        self.reset_for_new_play()
        self.menu.pack_forget()
        self.quiz.pack(fill="both", expand=True)
        self.start_time = time.perf_counter()
        self.next_question()

    def reset_for_new_play(self) -> None:
        """Reestablish invariants between sessions (prevents score leakage)."""
        self.q_index = 0
        self.score = 0
        self.attempt = 1
        self.first_try_correct = 0
        self.second_try_correct = 0
        self.var_score.set("Score: 0")
        self.var_feedback.set("")
        self.var_question.set("")
        self.var_progress.set("")

    def next_question(self) -> None:
        """
        Advance the item index, generate a new problem, and render it.
        For Easy/Moderate, disallow negative results to maintain approachability.
        """
        self.q_index += 1
        if self.q_index > TOTAL_QUESTIONS:
            displayResults(self)
            return

        a, b = randomInt(self.level)
        op = decideOperation()

        # Keep early levels approachable: prevent negatives for Easy/Moderate
        if op == "-" and self.level != 3 and a < b:
            a, b = b, a

        self.a, self.b, self.op = a, b, op
        self.attempt = 1
        self.var_progress.set(f"Q{self.q_index}/{TOTAL_QUESTIONS}")
        displayProblem(self, a, op, b)

    def submit_answer(self) -> None:
        """
        Validate input (robustness), check correctness, and update score.
        Two-attempt policy: 1st try (higher credit), 2nd try (partial credit).
        """
        txt = self.entry.get().strip()
        if not txt:
            self.var_feedback.set("Please enter a whole number.")
            return
        try:
            ans = int(txt)
        except ValueError:
            self.var_feedback.set("Please enter a valid whole number (e.g., 42).")
            return

        if isCorrect(self.a, self.op, self.b, ans, self):
            # Scoring based on attempt (simple mastery-based grading rule)
            if self.attempt == 1:
                self.score += PTS_FIRST
                self.first_try_correct += 1
            else:
                self.score += PTS_SECOND
                self.second_try_correct += 1
            self.var_score.set(f"Score: {self.score}")
            self.next_question()
            return

        # Wrong answer: allow second attempt, otherwise move on
        if self.attempt == 1:
            self.attempt = 2
            displayProblem(self, self.a, self.op, self.b, clear_feedback=False)
        else:
            # Show final feedback already set in isCorrect; proceed to next
            self.next_question()


# =============================================================================
# Entrypoint
# -----------------------------------------------------------------------------
# Seeding random ensures varied items each run. Tk mainloop hands control to
# the event dispatcher; program exits when root window is destroyed.
# =============================================================================
def main() -> None:
    random.seed()  # full randomness per run
    root = tk.Tk()
    root.geometry("380x260")
    app = QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
