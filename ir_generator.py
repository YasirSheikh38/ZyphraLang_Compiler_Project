"""Three-address-code IR generator for ZyphraLang."""
from typing import List
from ast_nodes import *
from errors import SemanticError


class IRGenerator:
    def __init__(self):
        self.instructions: List[str] = []
        self.temp_count = 0
        self.label_count = 0

    def _new_temp(self):
        self.temp_count += 1; return f"t{self.temp_count}"

    def _new_label(self):
        self.label_count += 1; return f"L{self.label_count}"

    def _emit(self, line): self.instructions.append(line)

    def generate(self, program: Program) -> List[str]:
        self._block(program.body)
        return self.instructions

    def _block(self, stmts):
        for s in stmts: self._stmt(s)

    def _stmt(self, node):
        if isinstance(node, VarDecl):
            if node.value:
                place = self._expr(node.value)
                self._emit(f"{node.name} := {place}")
            else:
                self._emit(f"{node.name} := 0")

        elif isinstance(node, Assign):
            place = self._expr(node.value)
            self._emit(f"{node.name} := {place}")

        elif isinstance(node, Print):
            place = self._expr(node.expr)
            self._emit(f"PRINT {place}")

        elif isinstance(node, If):
            cond = self._expr(node.condition)
            l_else, l_end = self._new_label(), self._new_label()
            self._emit(f"IF_FALSE {cond} GOTO {l_else}")
            self._block(node.then_block)
            self._emit(f"GOTO {l_end}")
            self._emit(f"{l_else}:")
            self._block(node.else_block)
            self._emit(f"{l_end}:")

        elif isinstance(node, While):
            l_start, l_end = self._new_label(), self._new_label()
            self._emit(f"{l_start}:")
            cond = self._expr(node.condition)
            self._emit(f"IF_FALSE {cond} GOTO {l_end}")
            self._block(node.body)
            self._emit(f"GOTO {l_start}")
            self._emit(f"{l_end}:")

        elif isinstance(node, For):
            if node.init: self._stmt(node.init)
            l_start, l_end = self._new_label(), self._new_label()
            self._emit(f"{l_start}:")
            if node.condition:
                cond = self._expr(node.condition)
                self._emit(f"IF_FALSE {cond} GOTO {l_end}")
            self._block(node.body)
            if node.step: self._stmt(node.step)
            self._emit(f"GOTO {l_start}")
            self._emit(f"{l_end}:")

        elif isinstance(node, FuncDef):
            self._emit(f"\nFUNC {node.name}({', '.join(node.params)}):")
            self._block(node.body)
            self._emit(f"END_FUNC {node.name}\n")

        elif isinstance(node, Return):
            if node.value:
                place = self._expr(node.value)
                self._emit(f"RETURN {place}")
            else:
                self._emit("RETURN")

        elif isinstance(node, EndProgram):
            self._emit("HALT")

    def _expr(self, node) -> str:
        if isinstance(node, Literal):
            if node.lit_type == "string":
                return f'"{node.value}"'
            if node.lit_type == "bool":
                return "rightOn" if node.value else "nope"
            return str(node.value)
        if isinstance(node, Variable):
            return node.name
        if isinstance(node, Call):
            args = ", ".join(self._expr(a) for a in node.args)
            t = self._new_temp()
            self._emit(f"{t} := CALL {node.name}({args})")
            return t
        if isinstance(node, UnaryOp):
            v = self._expr(node.operand)
            t = self._new_temp()
            self._emit(f"{t} := -{v}")
            return t
        if isinstance(node, BinaryOp):
            left = self._expr(node.left)
            right = self._expr(node.right)
            op_map = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/",
                      "MOD": "%", "POW": "**",
                      "GT": ">", "LT": "<", "EQ": "==", "NEQ": "!=",
                      "LEQ": "<=", "GEQ": ">="}
            t = self._new_temp()
            self._emit(f"{t} := {left} {op_map[node.op]} {right}")
            return t
        raise SemanticError("Unknown IR expression", node.line, node.col)