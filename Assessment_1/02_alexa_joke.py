import tkinter as tk, random
from pathlib import Path

PHRASE = "alexa tell me a joke"               # The exact phrase the user must type (we compare in lowercase)

def load_jokes():
    base = Path(__file__).resolve().parent if "__file__" in globals() else Path().resolve()
    p = base / "randomJokes.txt"              # Expects the dataset file in the same folder as this script
    jokes = []
    if p.exists():
        # Read file line by line; each line should be "setup?Punchline"
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or "?" not in line:
                continue
            s, pl = line.split("?", 1)
            jokes.append((s.strip() + "?", pl.strip()))
    if jokes:
        return jokes
    # Fallback joke so the app still runs even if the file is missing
    return [("Why did the chicken cross the road?", "To get to the other side.")]

class App:
    def __init__(self, root):
        # App state: list of jokes, current joke, and simple stage machine
        self.jokes, self.cur, self.stage = load_jokes(), None, "idle"

        # ----- Window & static UI -----
        root.title("Random Jokes"); root.geometry("600x300")
        tk.Label(root, text="Random Jokes", font=("Segoe UI", 16, "bold")).pack(pady=(10, 2))
        tk.Label(root, text="Type: Alexa tell me a joke to get started", fg="#555").pack()

        # Input line and Start button (Enter key also triggers Start)
        self.entry = tk.Entry(root, font=("Segoe UI", 12)); self.entry.pack(fill="x", padx=12, pady=8)
        self.btn = tk.Button(root, text="Start", command=self.on_start); self.btn.pack(pady=(0, 8))

        # Dynamic labels for setup, punchline, and status tips
        self.setup = tk.Label(root, font=("Consolas", 16, "bold"), wraplength=560)
        self.punch = tk.Label(root, font=("Consolas", 14), fg="green", wraplength=560)
        self.status = tk.Label(root, fg="#444"); self.status.pack(pady=(2, 4))
        self.setup.pack(pady=(8, 2)); self.punch.pack(pady=(2, 8))

        # Bind keys: Enter to start/reveal; 'q' to quit
        root.bind("<Return>", lambda e: self.on_start())
        root.bind("q", lambda e: root.destroy())

    def on_start(self):
        # If a setup is already shown, the next Enter/Start reveals the punchline
        if self.stage == "setup_shown":
            self.show_punch(); return

        # If idle or after punchline, require the exact phrase to get a new setup
        if self.stage in ("idle", "punchline_shown"):
            if self.entry.get().strip().lower() == PHRASE:
                self.new_joke(); return
            self.status.config(text="Please type exactly: Alexa tell me a joke"); return

    def new_joke(self):
        # Pick a random (setup, punchline) pair and display the setup
        self.cur = random.choice(self.jokes)
        self.setup.config(text=self.cur[0]); self.punch.config(text="")
        self.status.config(text="Press Enter or click reveal punchline to reveal punchline · Q to quit")
        self.stage = "setup_shown"
        self.btn.config(text="Reveal Punchline")
        self.entry.selection_range(0, tk.END)  # Select input text for easy retyping

    def show_punch(self):
        # Show punchline and switch back to post-joke state
        if not self.cur:
            return
        self.punch.config(text=self.cur[1])
        self.status.config(text="Type the phrase again, then press Enter/Start for a new joke")
        self.stage = "punchline_shown"
        self.btn.config(text="Start")

def main():
    # Standard Tkinter bootstrap: create window, build app, start event loop
    root = tk.Tk(); App(root); root.mainloop()

if __name__ == "__main__":
    main()
