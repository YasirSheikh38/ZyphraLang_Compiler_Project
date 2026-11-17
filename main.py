"""ZyphraLang compiler — Tkinter GUI driver."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import LANGUAGE_NAME
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from ir_generator import IRGenerator
from codegen import CodeGenerator
from errors import ZyphraError


PHASES = [
    "Lexical Analysis",
    "Syntax Analysis",
    "Semantic Analysis",
    "Intermediate Code",
]


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        root.title(f"{LANGUAGE_NAME} Compiler")
        root.geometry("1100x700")

        # ---------- Toolbar ----------
        toolbar = ttk.Frame(root, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="Phase:").pack(side=tk.LEFT, padx=(0, 4))
        self.phase_var = tk.StringVar(value=PHASES[0])
        self.phase_combo = ttk.Combobox(
            toolbar, textvariable=self.phase_var, values=PHASES,
            state="readonly", width=20)
        self.phase_combo.pack(side=tk.LEFT, padx=4)
        self.phase_combo.bind("<<ComboboxSelected>>", self._on_phase_change)

        ttk.Button(toolbar, text="Run", command=self.run_program).pack(
            side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Analyze Phase",
                   command=self.analyze_phase).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Load Sample",
                   command=self.load_sample).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Open File",
                   command=self.open_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Clear",
                   command=self.clear_all).pack(side=tk.LEFT, padx=4)

        # ---------- Split panes ----------
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # left: editor
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        ttk.Label(left, text="Source code (.zyp)").pack(anchor="w")
        self.editor = tk.Text(left, wrap="none", font=("Consolas", 11),
                              undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.insert("1.0", DEFAULT_SAMPLE)

        # right: output
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        ttk.Label(right, text="Output").pack(anchor="w")
        self.output = tk.Text(right, wrap="none", font=("Consolas", 11),
                              state="disabled", bg="#111", fg="#eee")
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.tag_configure("err", foreground="#ff6b6b")
        self.output.tag_configure("ok", foreground="#7cff7c")

    # ---------- helpers ----------
    def _set_output(self, text, tag=None):
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        if tag: self.output.insert(tk.END, text, tag)
        else:   self.output.insert(tk.END, text)
        self.output.config(state="disabled")

    def _source(self) -> str:
        return self.editor.get("1.0", tk.END)

    # ---------- phase selection ----------
    def _on_phase_change(self, *_):
        self.analyze_phase()

    def analyze_phase(self):
        phase = self.phase_var.get()
        try:
            tokens = Lexer(self._source()).tokenize()

            if phase == "Lexical Analysis":
                self._set_output(self._render_tokens(tokens), "ok")
                return

            ast = Parser(tokens).parse()

            if phase == "Syntax Analysis":
                self._set_output(self._render_ast(ast), "ok")
                return

            sem = SemanticAnalyzer()
            report = sem.analyze(ast)

            if phase == "Semantic Analysis":
                self._set_output("\n".join(report), "ok")
                return

            if phase == "Intermediate Code":
                ir = IRGenerator().generate(ast)
                self._set_output("\n".join(ir), "ok")
                return
        except ZyphraError as e:
            self._set_output(e.format(), "err")

    # ---------- run program ----------
    def run_program(self):
        try:
            tokens = Lexer(self._source()).tokenize()
            ast = Parser(tokens).parse()
            SemanticAnalyzer().analyze(ast)
            out = CodeGenerator().execute(ast)
            self._set_output(f"=== Program Output ===\n{out}", "ok")
        except ZyphraError as e:
            self._set_output(e.format(), "err")

    # ---------- rendering helpers ----------
    def _render_tokens(self, tokens):
        lines = [f"{'KIND':<14}{'VALUE':<22}{'LINE':<6}{'COL'}"]
        lines.append("-" * 60)
        for t in tokens:
            lines.append(f"{t.kind:<14}{str(t.value):<22}{t.line:<6}{t.col}")
        return "\n".join(lines)

    def _render_ast(self, node, indent=0):
        pad = "  " * indent
        name = node.__class__.__name__
        # simple pretty printer
        from ast_nodes import Program
        if isinstance(node, Program):
            out = [f"{pad}Program"]
            for s in node.body:
                out.append(self._render_ast(s, indent + 1))
            return "\n".join(out)
        parts = [f"{pad}{name}"]
        for k, v in vars(node).items():
            if k in ("line", "col"): continue
            if isinstance(v, list):
                parts.append(f"{pad}  {k}:")
                for item in v:
                    if hasattr(item, "line"):
                        parts.append(self._render_ast(item, indent + 2))
                    else:
                        parts.append(f"{pad}    {item!r}")
            elif hasattr(v, "line"):
                parts.append(f"{pad}  {k}:")
                parts.append(self._render_ast(v, indent + 2))
            else:
                parts.append(f"{pad}  {k}: {v!r}")
        return "\n".join(parts)

    # ---------- file ops ----------
    def load_sample(self):
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", DEFAULT_SAMPLE)

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("ZyphraLang", "*.zyp"), ("All files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", f.read())

    def clear_all(self):
        self.editor.delete("1.0", tk.END)
        self._set_output("")


# ============================================================
# A default demo program written in ZyphraLang
# ============================================================
DEFAULT_SAMPLE = '''## ZyphraLang demo
wholenumber x :=> 10;
wholenumber y :=> 3;
wholenumber z :=> x ~+~ y;
echoOut(z);
echoOut("Hello from ZyphraLang!");

whenTrue (x >>? y) {
    echoOut("x is greater than y");
} elseWay {
    echoOut("x is NOT greater than y");
}

spin (wholenumber i :=> 0; i ?<< 5; i :=> i ~+~ 1) {
    echoOut(i);
}

wholenumber p :=> 2 ~^^~ 8;
echoOut(p);

whenTrue (x ==? 10) {
    echoOut("x equals ten");
}
'''


def main():
    root = tk.Tk()
    CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()