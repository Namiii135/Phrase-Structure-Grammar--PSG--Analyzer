import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

# ─────────────────────────────────────────────
#  CORE LOGIC
# ─────────────────────────────────────────────

def parse_productions(prod_str):
    """Parse 'S->AB, A->ab, B->bb' into list of (lhs, rhs) tuples."""
    rules = []
    for part in prod_str.split(","):
        part = part.strip()
        if "->" not in part:
            continue
        lhs, rhs = part.split("->", 1)
        rules.append((lhs.strip(), rhs.strip()))
    return rules


def validate_grammar(vocab_set, terminal_set, start, productions):
    """Basic validation: start in vocab, terminals subset of vocab, LHS has at least one NT."""
    non_terminals = vocab_set - terminal_set
    if start not in non_terminals:
        return False, f"Start symbol '{start}' must be a non-terminal in Vocabulary."
    if not terminal_set.issubset(vocab_set):
        return False, "Terminal symbols must all be in Vocabulary."
    for lhs, rhs in productions:
        # Check LHS contains at least one non-terminal
        has_nt = any(ch in non_terminals for ch in lhs) or any(
            sym in non_terminals for sym in lhs.split()
        )
        if not has_nt:
            return False, f"LHS of rule '{lhs}->{rhs}' must contain at least one non-terminal."
    return True, "OK"


def classify_rule(lhs, rhs, non_terminals):
    """
    Classify a single production rule per Chomsky hierarchy.
    Returns the LOWEST type (least restrictive) this rule satisfies.

    Type 3: LHS is single NT, RHS is single terminal OR terminal+NT
    Type 2: LHS is single NT (any RHS)
    Type 1: |LHS| <= |RHS|  OR  RHS == lambda/epsilon
    Type 0: everything else
    """
    epsilon = {"", "lambda", "epsilon", "ε"}

    # Helper: is a symbol a non-terminal?
    def is_nt(sym):
        return sym in non_terminals or sym.isupper()

    # Helper: is a symbol a terminal (single lowercase / digit / symbol)?
    def is_term(sym):
        return len(sym) == 1 and not sym.isupper()

    lhs_len = len(lhs)
    rhs_len = 0 if rhs in epsilon else len(rhs)

    # ── Type 3 check ──────────────────────────────────────────────
    # LHS must be a single non-terminal
    # RHS must be: single terminal  OR  terminal followed by one NT
    if lhs_len == 1 and is_nt(lhs):
        if rhs in epsilon:
            return 3  # X -> ε is allowed in Type 3
        if len(rhs) == 1 and is_term(rhs):
            return 3  # X -> a
        if len(rhs) == 2 and is_term(rhs[0]) and is_nt(rhs[1]):
            return 3  # X -> aY
        # Falls through to Type 2 check

    # ── Type 2 check ──────────────────────────────────────────────
    # LHS is a single non-terminal (any RHS allowed)
    if lhs_len == 1 and is_nt(lhs):
        return 2

    # ── Type 1 check ──────────────────────────────────────────────
    # |LHS| <= |RHS|  OR  RHS == lambda (only S -> lambda allowed strictly,
    # but we apply leniently here as per lecture)
    if rhs in epsilon or lhs_len <= rhs_len:
        return 1

    # ── Type 0 ────────────────────────────────────────────────────
    return 0


def determine_grammar_type(productions, non_terminals):
    """
    Classify each rule, then the overall grammar type is the LOWEST
    (least restrictive) type found across all rules.
    """
    rule_types = []
    for lhs, rhs in productions:
        t = classify_rule(lhs, rhs, non_terminals)
        rule_types.append((lhs, rhs, t))
    overall = min(t for _, _, t in rule_types) if rule_types else 0
    return overall, rule_types


TYPE_NAMES = {
    3: "Type 3 — Regular Grammar",
    2: "Type 2 — Context-Free Grammar",
    1: "Type 1 — Context-Sensitive Grammar",
    0: "Type 0 — Unrestricted (Phrase-Structure) Grammar",
}


# ── String acceptance via BFS derivation ──────────────────────────

def is_accepted(start, productions, target, max_depth=12):
    """
    BFS from start symbol; apply productions; check if target string
    (all terminals) is reachable within max_depth steps.
    Returns (accepted: bool, steps: list of strings showing derivation).
    """
    epsilon_set = {"", "lambda", "epsilon", "ε"}
    # Normalise target
    target_norm = "" if target.lower() in {"lambda", "epsilon", "ε", ""} else target

    visited = set()
    # queue: (current_string, path_so_far)
    queue = deque([(start, [start])])
    visited.add(start)

    while queue:
        current, path = queue.popleft()
        if len(path) > max_depth + 1:
            continue

        # Normalise epsilon representations
        current_norm = "" if current in epsilon_set else current

        if current_norm == target_norm:
            return True, path

        # Try every production on every position in current string
        for lhs, rhs in productions:
            rhs_actual = "" if rhs in epsilon_set else rhs
            # Find all occurrences of lhs in current
            start_idx = 0
            while True:
                idx = current.find(lhs, start_idx)
                if idx == -1:
                    break
                new_str = current[:idx] + rhs_actual + current[idx + len(lhs):]
                if new_str not in visited:
                    visited.add(new_str)
                    queue.append((new_str, path + [new_str if new_str else "ε"]))
                start_idx = idx + 1

    return False, []


def generate_accepted_strings(start, productions, non_terminals, max_depth=8):
    """
    BFS to generate all terminal strings (accepted strings) reachable from start.
    Returns list of accepted strings sorted by length.
    """
    epsilon_set = {"", "lambda", "epsilon", "ε"}
    accepted = set()
    visited = set()

    queue = deque([(start, 0)])
    visited.add((start, 0))

    while queue:
        current, depth = queue.popleft()

        # Check if all characters are terminals (no non-terminals left)
        is_terminal = all(ch not in non_terminals for ch in current)
        if is_terminal:
            norm = "" if current in epsilon_set else current
            accepted.add(norm)

        if depth >= max_depth:
            continue

        # Try every production on every position
        for lhs, rhs in productions:
            rhs_actual = "" if rhs in epsilon_set else rhs
            start_idx = 0
            while True:
                idx = current.find(lhs, start_idx)
                if idx == -1:
                    break
                new_str = current[:idx] + rhs_actual + current[idx + len(lhs):]
                state = (new_str, depth + 1)
                if state not in visited:
                    visited.add(state)
                    queue.append(state)
                start_idx = idx + 1

    # Sort by length, then alphabetically
    return sorted(accepted, key=lambda s: (len(s), s))


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

class PSGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PSG Analyzer — CSC510")
        self.geometry("820x750")
        self.resizable(True, True)
        self.configure(bg="#0f172a")

        self._build_styles()
        self._build_ui()

    # ── Styles ────────────────────────────────
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Card.TFrame", background="#1e293b", relief="flat")
        style.configure("Inner.TFrame", background="#1e293b")

        style.configure("TLabel",
                        background="#1e293b",
                        foreground="#e2e8f0",
                        font=("Consolas", 10))

        style.configure("Header.TLabel",
                        background="#0f172a",
                        foreground="#38bdf8",
                        font=("Consolas", 16, "bold"))

        style.configure("Sub.TLabel",
                        background="#0f172a",
                        foreground="#94a3b8",
                        font=("Consolas", 9))

        style.configure("Section.TLabel",
                        background="#1e293b",
                        foreground="#7dd3fc",
                        font=("Consolas", 9, "bold"))

        style.configure("Result.TLabel",
                        background="#1e293b",
                        foreground="#4ade80",
                        font=("Consolas", 11, "bold"))

        style.configure("Error.TLabel",
                        background="#1e293b",
                        foreground="#f87171",
                        font=("Consolas", 10, "bold"))

        style.configure("Run.TButton",
                        background="#0ea5e9",
                        foreground="#0f172a",
                        font=("Consolas", 10, "bold"),
                        borderwidth=0,
                        padding=(14, 8))

        style.map("Run.TButton",
                  background=[("active", "#38bdf8")])

        style.configure("Check.TButton",
                        background="#6366f1",
                        foreground="#ffffff",
                        font=("Consolas", 10, "bold"),
                        borderwidth=0,
                        padding=(14, 8))

        style.map("Check.TButton",
                  background=[("active", "#818cf8")])

        style.configure("Clear.TButton",
                        background="#334155",
                        foreground="#94a3b8",
                        font=("Consolas", 9),
                        borderwidth=0,
                        padding=(10, 6))

        style.map("Clear.TButton",
                  background=[("active", "#475569")])

    # ── UI Layout ─────────────────────────────
    def _build_ui(self):
        # ── Header ──────────────────────────
        hdr = tk.Frame(self, bg="#0f172a", pady=16)
        hdr.pack(fill="x", padx=24)

        ttk.Label(hdr, text=" PSG Analyzer", style="Header.TLabel").pack(anchor="w")
        ttk.Label(hdr, text="Phrase-Structure Grammar · Chomsky Hierarchy · CSC510",
                  style="Sub.TLabel").pack(anchor="w")

        sep = tk.Frame(self, bg="#1e40af", height=2)
        sep.pack(fill="x", padx=24, pady=(0, 16))

        # ── Main scrollable body ─────────────
        body = tk.Frame(self, bg="#0f172a")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # LEFT — Input card
        left = tk.Frame(body, bg="#1e293b", bd=0, padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._build_input_card(left)

        # RIGHT — Output card
        right = tk.Frame(body, bg="#1e293b", bd=0, padx=18, pady=18)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        self._build_output_card(right)

        body.rowconfigure(0, weight=1)

    def _field(self, parent, label, example, var_name):
        """Create a labelled entry field."""
        ttk.Label(parent, text=label, style="Section.TLabel").pack(anchor="w", pady=(8, 2))
        entry = tk.Entry(parent,
                         bg="#0f172a", fg="#e2e8f0",
                         insertbackground="#38bdf8",
                         font=("Consolas", 10),
                         relief="flat",
                         bd=6)
        entry.pack(fill="x", pady=(0, 2))
        ttk.Label(parent, text=f"e.g.  {example}",
                  background="#1e293b", foreground="#475569",
                  font=("Consolas", 8)).pack(anchor="w")
        setattr(self, var_name, entry)

    def _build_input_card(self, parent):
        ttk.Label(parent, text="GRAMMAR INPUT",
                  background="#1e293b", foreground="#38bdf8",
                  font=("Consolas", 10, "bold")).pack(anchor="w", pady=(0, 6))

        self._field(parent, "Vocabulary (V)", "S, A, B, a, b", "ent_vocab")
        self._field(parent, "Terminal Symbols (T)", "a, b", "ent_terminal")
        self._field(parent, "Start Symbol (S)", "S", "ent_start")

        ttk.Label(parent, text="Production Rules (P)", style="Section.TLabel").pack(anchor="w", pady=(10, 2))
        self.ent_prod = tk.Text(parent,
                                height=4,
                                bg="#0f172a", fg="#e2e8f0",
                                insertbackground="#38bdf8",
                                font=("Consolas", 10),
                                relief="flat", bd=6,
                                wrap="word")
        self.ent_prod.pack(fill="x")
        ttk.Label(parent, text="e.g.  S->AB, A->ab, B->bb",
                  background="#1e293b", foreground="#475569",
                  font=("Consolas", 8)).pack(anchor="w")

        btn_row = tk.Frame(parent, bg="#1e293b")
        btn_row.pack(fill="x", pady=(14, 0))
        ttk.Button(btn_row, text="▶  Analyze Grammar",
                   style="Run.TButton",
                   command=self._analyze).pack(side="left")
        ttk.Button(btn_row, text="Clear",
                   style="Clear.TButton",
                   command=self._clear).pack(side="left", padx=(8, 0))

    def _build_output_card(self, parent):
        ttk.Label(parent, text="ANALYSIS RESULT",
                  background="#1e293b", foreground="#38bdf8",
                  font=("Consolas", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Type result box
        type_box = tk.Frame(parent, bg="#0f172a", padx=12, pady=12)
        type_box.pack(fill="x", pady=(0, 10))

        ttk.Label(type_box, text="Grammar Type",
                  background="#0f172a", foreground="#94a3b8",
                  font=("Consolas", 8, "bold")).pack(anchor="w")
        self.lbl_type = tk.Label(type_box, text="—",
                                 bg="#0f172a", fg="#4ade80",
                                 font=("Consolas", 13, "bold"),
                                 anchor="w", justify="left",
                                 wraplength=280)
        self.lbl_type.pack(anchor="w", pady=(4, 0))

        # Rule breakdown
        ttk.Label(parent, text="RULE BREAKDOWN",
                  background="#1e293b", foreground="#7dd3fc",
                  font=("Consolas", 8, "bold")).pack(anchor="w", pady=(6, 4))

        self.rule_frame = tk.Frame(parent, bg="#1e293b")
        self.rule_frame.pack(fill="both", expand=True, pady=(0, 8))

        # Scrollable text for rules
        self.txt_rules = tk.Text(self.rule_frame,
                                 height=5,
                                 bg="#0f172a", fg="#cbd5e1",
                                 font=("Consolas", 9),
                                 relief="flat", bd=6,
                                 state="disabled",
                                 wrap="word")
        scroll = ttk.Scrollbar(self.rule_frame, command=self.txt_rules.yview)
        self.txt_rules.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.txt_rules.pack(fill="both", expand=True)

        # Color tags
        self.txt_rules.tag_configure("t3", foreground="#4ade80")
        self.txt_rules.tag_configure("t2", foreground="#a78bfa")
        self.txt_rules.tag_configure("t1", foreground="#fbbf24")
        self.txt_rules.tag_configure("t0", foreground="#f87171")
        self.txt_rules.tag_configure("label", foreground="#64748b")

        # Accepted strings section
        ttk.Label(parent, text="ACCEPTED STRINGS",
                  background="#1e293b", foreground="#7dd3fc",
                  font=("Consolas", 8, "bold")).pack(anchor="w", pady=(0, 4))

        self.strings_frame = tk.Frame(parent, bg="#1e293b")
        self.strings_frame.pack(fill="both", expand=True)

        self.txt_strings = tk.Text(self.strings_frame,
                                   height=4,
                                   bg="#0f172a", fg="#4ade80",
                                   font=("Consolas", 9),
                                   relief="flat", bd=6,
                                   state="disabled",
                                   wrap="word")
        scroll2 = ttk.Scrollbar(self.strings_frame, command=self.txt_strings.yview)
        self.txt_strings.configure(yscrollcommand=scroll2.set)
        scroll2.pack(side="right", fill="y")
        self.txt_strings.pack(fill="both", expand=True)

    # ── Actions ────────────────────────────────

    def _get_inputs(self):
        vocab = {v.strip() for v in self.ent_vocab.get().split(",") if v.strip()}
        terminal = {t.strip() for t in self.ent_terminal.get().split(",") if t.strip()}
        start = self.ent_start.get().strip()
        prod_text = self.ent_prod.get("1.0", "end").strip()
        productions = parse_productions(prod_text)
        return vocab, terminal, start, productions

    def _analyze(self):
        vocab, terminal, start, productions = self._get_inputs()

        # ── Validate ─────────────────────────
        if not vocab or not terminal or not start or not productions:
            self._show_error("Invalid Grammar Input\nPlease fill in all fields.")
            return

        non_terminals = vocab - terminal

        valid, msg = validate_grammar(vocab, terminal, start, productions)
        if not valid:
            self._show_error(f"Invalid Grammar Input\n{msg}")
            return

        # ── Classify ─────────────────────────
        overall, rule_types = determine_grammar_type(productions, non_terminals)

        # Store for string check
        self._productions = productions
        self._start = start
        self._non_terminals = non_terminals

        # ── Display result ───────────────────
        self.lbl_type.config(text=TYPE_NAMES[overall], fg="#4ade80")

        # Rule breakdown
        self.txt_rules.config(state="normal")
        self.txt_rules.delete("1.0", "end")

        tag_map = {3: "t3", 2: "t2", 1: "t1", 0: "t0"}
        badge = {3: "[Type 3]", 2: "[Type 2]", 1: "[Type 1]", 0: "[Type 0]"}

        for lhs, rhs, t in rule_types:
            rule_str = f"  {lhs} → {rhs if rhs else 'ε'}"
            self.txt_rules.insert("end", rule_str)
            self.txt_rules.insert("end", f"   {badge[t]}\n", tag_map[t])

        self.txt_rules.insert("end", "\n")
        self.txt_rules.insert("end", f"  Overall: {TYPE_NAMES[overall]}\n", tag_map[overall])
        self.txt_rules.config(state="disabled")

        # ── Generate and display accepted strings ──
        accepted_strings = generate_accepted_strings(start, productions, non_terminals)
        self.txt_strings.config(state="normal")
        self.txt_strings.delete("1.0", "end")

        if accepted_strings:
            strings_display = ", ".join([f'"{s if s else "ε"}"' for s in accepted_strings])
            self.txt_strings.insert("end", strings_display)
        else:
            self.txt_strings.insert("end", "No accepted strings found within search depth.")
            self.txt_strings.config(fg="#f87171")

        self.txt_strings.config(state="disabled")

    def _show_error(self, msg):
        self.lbl_type.config(text=msg, fg="#f87171")
        self.txt_rules.config(state="normal")
        self.txt_rules.delete("1.0", "end")
        self.txt_rules.config(state="disabled")

    def _clear(self):
        self.ent_vocab.delete(0, "end")
        self.ent_terminal.delete(0, "end")
        self.ent_start.delete(0, "end")
        self.ent_prod.delete("1.0", "end")
        self.lbl_type.config(text="—", fg="#4ade80")
        self.txt_rules.config(state="normal")
        self.txt_rules.delete("1.0", "end")
        self.txt_rules.config(state="disabled")
        self.txt_strings.config(state="normal", fg="#4ade80")
        self.txt_strings.delete("1.0", "end")
        self.txt_strings.config(state="disabled")
        if hasattr(self, "_productions"):
            del self._productions


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = PSGApp()
    app.mainloop()