from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# -------------------------- paths --------------------------
def data_path() -> Path:
    base = Path(__file__).resolve().parent if "__file__" in globals() else Path().resolve()
    return base / "studentMarks.txt"

# -------------------------- model --------------------------
@dataclass
class Student:
    code: int; name: str; cw1: int; cw2: int; cw3: int; exam: int
    @property
    def cw_total(self) -> int: return self.cw1 + self.cw2 + self.cw3                 # /60
    @property
    def total(self) -> int: return self.cw_total + self.exam                          # /160
    @property
    def percent(self) -> float: return (self.total / 160) * 100.0
    @property
    def grade(self) -> str:
        p = self.percent
        return "A" if p >= 70 else "B" if p >= 60 else "C" if p >= 50 else "D" if p >= 40 else "F"

# -------------------------- file I/O -----------------------
def load_students() -> List[Student]:
    p = data_path()
    if not p.exists():
        messagebox.showerror("File Missing", f"Could not find {p.name} in the script folder.")
        return []
    rows: List[Student] = []
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines()):
        line = line.strip()
        if not line: continue
        if i == 0 and line.isdigit() and "," not in line:  # leading count line
            continue
        parts = [x.strip() for x in line.split(",")]
        if len(parts) != 6: continue
        try:
            code = int(parts[0]); name = parts[1]
            c1, c2, c3, ex = map(int, parts[2:])
        except ValueError:
            continue
        rows.append(Student(code, name, c1, c2, c3, ex))
    return rows

def save_students(students: List[Student]) -> None:
    """Persist to file and include the leading count line as per brief."""
    p = data_path()
    lines = [str(len(students))] + [f"{s.code},{s.name},{s.cw1},{s.cw2},{s.cw3},{s.exam}" for s in students]
    p.write_text("\n".join(lines), encoding="utf-8")

# -------------------------- utils -------------------------
def fmt_percent(p: float) -> str: return f"{p:.1f}%"
def student_to_row(s: Student) -> Tuple: return (s.name, s.code, s.cw_total, s.exam, fmt_percent(s.percent), s.grade)
def average_percent(students: List[Student]) -> float: return sum(s.percent for s in students)/len(students) if students else 0.0

# -------------------------- app ---------------------------
class StudentManagerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root; self.root.title("Student Manager — Coursework + Exam (out of 160)")
        self.students: List[Student] = load_students()
        root.geometry("900x520"); root.minsize(820, 480)

        # Left menu / Right content
        self.left = tk.Frame(root, padx=10, pady=10); self.left.pack(side="left", fill="y")
        self.right = tk.Frame(root, padx=10, pady=10); self.right.pack(side="right", fill="both", expand=True)

        tk.Label(self.left, text="MENU", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 6))
        tk.Label(self.right, text="Student Records", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(self.right, text=f"Data file: {data_path().name}", fg="#555").pack(anchor="w", pady=(0, 6))

        self._add_button("1. View all student records", self.view_all)
        self._add_button("2. View individual student record", self.view_individual)
        self._add_button("3. Show student with highest total", self.show_highest)
        self._add_button("4. Show student with lowest total", self.show_lowest)
        tk.Label(self.left, text="— Extension —", fg="#555").pack(anchor="w", pady=(10,4))
        self._add_button("5. Sort student records", self.sort_records)
        self._add_button("6. Add a student record", self.add_student)
        self._add_button("7. Delete a student record", self.delete_student)
        self._add_button("8. Update a student's record", self.update_student)
        tk.Button(self.left, text="Quit", width=26, command=root.destroy).pack(anchor="w", pady=(10,0))

        # Table
        self.tree = ttk.Treeview(self.right, columns=("Name","Number","CW Total","Exam","%","Grade"), show="headings")
        for col, w in [("Name",260),("Number",90),("CW Total",90),("Exam",80),("%",80),("Grade",70)]:
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Status (summary line) — will display "count + class average" after View All
        self.status = tk.Label(self.right, fg="#FFFFFF")
        self.status.pack(anchor="w", pady=(4,0))

        # Do NOT auto-populate. Show instruction until user clicks "View all".
        self._set_status("Click 'View all student records' to display the list.")

    # ---------- menu actions ----------
    def view_all(self) -> None:
        self._fill_table(self.students)
        n = len(self.students); avg = average_percent(self.students)
        self._set_status(f"Students: {n} · Class average: {fmt_percent(avg)}")

    def view_individual(self) -> None:
        if not self.students: return messagebox.showinfo("No Data", "No student records loaded.")
        query = simpledialog.askstring("Find Student", "Enter student code or part of name:")
        if not query: return
        query = query.strip().lower(); found = []
        for s in self.students:
            if query.isdigit() and int(query) == s.code: found=[s]; break
            if query in s.name.lower(): found.append(s)
        if not found: return messagebox.showinfo("Not Found", "No matching student.")
        s = found[0] if len(found)==1 else self._choose_from_list(found, "Select Student")
        if not s: return
        self._fill_table([s]); self._set_status(self._student_summary(s))

    def show_highest(self) -> None:
        if not self.students: return
        s = max(self.students, key=lambda x: x.total)
        self._fill_table([s]); self._set_status("Highest total · " + self._student_summary(s))

    def show_lowest(self) -> None:
        if not self.students: return
        s = min(self.students, key=lambda x: x.total)
        self._fill_table([s]); self._set_status("Lowest total · " + self._student_summary(s))

    def sort_records(self) -> None:
        if not self.students: return
        asc = messagebox.askyesno("Sort", "Sort by overall % ascending?\n(Yes=Ascending, No=Descending)")
        self.students.sort(key=lambda s: s.percent, reverse=not asc)
        self.view_all()

    def add_student(self) -> None:
        s = self._edit_dialog(title="Add Student")
        if not s: return
        if any(st.code == s.code for st in self.students):
            return messagebox.showerror("Duplicate", f"Student code {s.code} already exists.")
        self.students.append(s); save_students(self.students)
        messagebox.showinfo("Added", f"Added {s.name} ({s.code}).")
        self.view_all()

    def delete_student(self) -> None:
        if not self.students: return
        s = self._choose_from_list(self.students, "Delete Student")
        if not s: return
        if not messagebox.askyesno("Confirm Delete", f"Delete {s.name} ({s.code})?"): return
        self.students = [x for x in self.students if x.code != s.code]; save_students(self.students)
        messagebox.showinfo("Deleted", f"Deleted {s.name} ({s.code}).")
        self.view_all()

    def update_student(self) -> None:
        if not self.students: return
        s0 = self._choose_from_list(self.students, "Update Student")
        if not s0: return
        s = self._edit_dialog(s0, "Update Student")
        if not s: return
        if s.code != s0.code and any(st.code == s.code for st in self.students):
            return messagebox.showerror("Duplicate", f"Student code {s.code} already exists.")
        for i, st in enumerate(self.students):
            if st.code == s0.code: self.students[i] = s; break
        save_students(self.students)
        messagebox.showinfo("Updated", f"Updated {s.name} ({s.code}).")
        self.view_all()

    # ---------- helpers ----------
    def _add_button(self, text, cmd): tk.Button(self.left, text=text, width=26, command=cmd).pack(anchor="w", pady=2)

    def _fill_table(self, records: List[Student]) -> None:
        for row in self.tree.get_children(): self.tree.delete(row)
        for s in records: self.tree.insert("", "end", values=student_to_row(s))

    def _set_status(self, text: str) -> None: self.status.config(text=text)

    def _student_summary(self, s: Student) -> str:
        return (f"Name: {s.name} · Number: {s.code} · CW: {s.cw_total}/60 · "
                f"Exam: {s.exam}/100 · Overall: {fmt_percent(s.percent)} · Grade: {s.grade}")

    def _choose_from_list(self, options: List[Student], title: str) -> Optional[Student]:
        win = tk.Toplevel(self.root); win.title(title); win.transient(self.root); win.grab_set()
        tk.Label(win, text=title, font=("Segoe UI", 11, "bold")).pack(padx=10, pady=(10,6))
        lb = tk.Listbox(win, width=48, height=10)
        for s in options: lb.insert("end", f"{s.name}  ({s.code}) — {fmt_percent(s.percent)}")
        lb.pack(padx=10, pady=6); sel = [None]
        def ok():
            i = lb.curselection()
            if not i: return
            sel[0] = options[i[0]]; win.destroy()
        def cancel(): sel[0] = None; win.destroy()
        btns = tk.Frame(win); btns.pack(pady=8)
        tk.Button(btns, text="OK", width=10, command=ok).pack(side="left", padx=5)
        tk.Button(btns, text="Cancel", width=10, command=cancel).pack(side="left", padx=5)
        win.wait_window(); return sel[0]

    def _edit_dialog(self, s: Optional[Student]=None, title="Edit Student") -> Optional[Student]:
        win = tk.Toplevel(self.root); win.title(title); win.transient(self.root); win.grab_set()
        fields = [("Code (1000-9999)", "code"), ("Name", "name"),
                  ("Coursework 1 (0-20)", "cw1"), ("Coursework 2 (0-20)", "cw2"),
                  ("Coursework 3 (0-20)", "cw3"), ("Exam (0-100)", "exam")]
        entries = {}
        tk.Label(win, text=title, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(10,6), padx=10, sticky="w")
        for i,(lab,key) in enumerate(fields, start=1):
            tk.Label(win, text=lab).grid(row=i, column=0, sticky="e", padx=(10,6), pady=3)
            e = tk.Entry(win, width=28); e.grid(row=i, column=1, padx=(0,10), pady=3); entries[key]=e
        if s:
            entries["code"].insert(0, str(s.code)); entries["name"].insert(0, s.name)
            entries["cw1"].insert(0, str(s.cw1)); entries["cw2"].insert(0, str(s.cw2))
            entries["cw3"].insert(0, str(s.cw3)); entries["exam"].insert(0, str(s.exam))
        out = [None]
        def submit():
            try:
                code=int(entries["code"].get().strip()); name=entries["name"].get().strip()
                c1=int(entries["cw1"].get().strip()); c2=int(entries["cw2"].get().strip())
                c3=int(entries["cw3"].get().strip()); ex=int(entries["exam"].get().strip())
            except ValueError: return messagebox.showerror("Invalid", "Please enter integer values.")
            if not (1000<=code<=9999): return messagebox.showerror("Invalid","Code must be 1000-9999.")
            if not name: return messagebox.showerror("Invalid","Name cannot be empty.")
            for v,lo,hi,label in [(c1,0,20,"CW1"),(c2,0,20,"CW2"),(c3,0,20,"CW3"),(ex,0,100,"Exam")]:
                if not (lo<=v<=hi): return messagebox.showerror("Invalid", f"{label} must be {lo}-{hi}.")
            out[0]=Student(code,name,c1,c2,c3,ex); win.destroy()
        def cancel(): out[0]=None; win.destroy()
        btns=tk.Frame(win); btns.grid(row=len(fields)+1, column=0, columnspan=2, pady=8)
        tk.Button(btns, text="Save", width=10, command=submit).pack(side="left", padx=5)
        tk.Button(btns, text="Cancel", width=10, command=cancel).pack(side="left", padx=5)
        entries["code"].focus_set(); win.wait_window(); return out[0]

# -------------------------- entry -------------------------
def main(): 
    root = tk.Tk(); StudentManagerApp(root); root.mainloop()

if __name__ == "__main__": 
    main()
