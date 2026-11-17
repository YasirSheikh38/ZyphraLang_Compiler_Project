"""Transpile ZyphraLang AST into Python and execute it."""
from typing import List
from ast_nodes import *
from config import SAFE_BUILTINS
from errors import RuntimeErrorZy


class CodeGenerator:
    def __init__(self):
        self.indent = 0
        self.lines: List[str] = []
        self.function_defs: List[FuncDef] = []

    def _emit(self, line):
        self.lines.append("    " * self.indent + line)

    def _indent(self): self.indent += 1
    def _dedent(self): self.indent -= 1

    # --------------------------------------------------
    def generate(self, program: Program) -> str:
        for stmt in program.body:
            self._stmt(stmt)
        return "\n".join(self.lines)

    def execute(self, program: Program) -> str:
        captured: List[str] = []

        def safe_print(*args, **kwargs):
            captured.append(" ".join(str(a) for a in args))

        env = dict(SAFE_BUILTINS)
        env["print"] = safe_print

        # Functions must be pre-declared before use
        py_code = self.generate(program)
        try:
            exec(py_code, env)
        except Exception as e:
            raise RuntimeErrorZy(f"Runtime failure: {e}")
        return "\n".join(captured) if captured else "(no output)"

    # --------------------------------------------------
    def _stmt(self, node):
        if isinstance(node, VarDecl):
            if node.value:
                val = self._expr(node.value)
            else:
                val = {"int": "0", "string": '""', "bool": "False"}[node.var_type]
            self._emit(f"{node.name} = {val}")

        elif isinstance(node, Assign):
            self._emit(f"{node.name} = {self._expr(node.value)}")

        elif isinstance(node, Print):
            self._emit(f"print({self._expr(node.expr)})")

        elif isinstance(node, If):
            self._emit(f"if {self._expr(node.condition)}:")
            self._indent()
            if not node.then_block: self._emit("pass")
            for s in node.then_block: self._stmt(s)
            self._dedent()
            if node.else_block:
                self._emit("else:")
                self._indent()
                for s in node.else_block: self._stmt(s)
                self._dedent()

        elif isinstance(node, While):
            self._emit(f"while {self._expr(node.condition)}:")
            self._indent()
            if not node.body: self._emit("pass")
            for s in node.body: self._stmt(s)
            self._dedent()

        elif isinstance(node, For):
            if node.init: self._stmt(node.init)
            self._emit("while True:")
            self._indent()
            if node.condition:
                self._emit(f"if not ({self._expr(node.condition)}): break")
            if not node.body and not node.step:
                self._emit("pass")
            for s in node.body: self._stmt(s)
            if node.step: self._stmt(node.step)
            self._dedent()

        elif isinstance(node, FuncDef):
            self._emit(f"def {node.name}({', '.join(node.params)}):")
            self._indent()
            if not node.body: self._emit("pass")
            for s in node.body: self._stmt(s)
            self._dedent()

        elif isinstance(node, Return):
            if node.value:
                self._emit(f"return {self._expr(node.value)}")
            else:
                self._emit("return")

        elif isinstance(node, EndProgram):
            self._emit("raise SystemExit")

    # --------------------------------------------------
    def _expr(self, node) -> str:
        if isinstance(node, Literal):
            if node.lit_type == "string":
                return repr(node.value)
            if node.lit_type == "bool":
                return "True" if node.value else "False"
            return str(node.value)

        if isinstance(node, Variable):
            return node.name

        if isinstance(node, Call):
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{node.name}({args})"

        if isinstance(node, UnaryOp):
            return f"(-{self._expr(node.operand)})"

        if isinstance(node, BinaryOp):
            op_map = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/",
                      "MOD": "%", "POW": "**",
                      "GT": ">", "LT": "<", "EQ": "==", "NEQ": "!=",
                      "LEQ": "<=", "GEQ": ">="}
            return f"({self._expr(node.left)} {op_map[node.op]} " \
                   f"{self._expr(node.right)})"

        raise RuntimeErrorZy("Unknown expression in codegen")