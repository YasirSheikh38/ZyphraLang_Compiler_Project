"""Semantic analyzer for ZyphraLang — symbol table + type checking."""
from typing import Dict, List, Optional
from ast_nodes import *
from errors import SemanticError


class Symbol:
    def __init__(self, name, sym_type, value=None):
        self.name = name
        self.sym_type = sym_type
        self.value = value


class Scope:
    def __init__(self, parent: Optional["Scope"] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, sym: Symbol, line=0, col=0):
        if sym.name in self.symbols:
            raise SemanticError(
                f"Symbol {sym.name!r} already defined in this scope",
                line, col, sym.name)
        self.symbols[sym.name] = sym

    def lookup(self, name) -> Optional[Symbol]:
        if name in self.symbols: return self.symbols[name]
        return self.parent.lookup(name) if self.parent else None


class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = Scope()
        self.current = self.global_scope
        self.functions: Dict[str, FuncDef] = {}
        self.report: List[str] = []

    def analyze(self, program: Program) -> List[str]:
        for stmt in program.body:
            self._stmt(stmt)
        self.report.append("\n=== Global Symbol Table ===")
        for name, sym in self.global_scope.symbols.items():
            self.report.append(f"  {name:<15} type={sym.sym_type}")
        return self.report

    def _stmt(self, node):
        if isinstance(node, VarDecl):
            if node.value is not None:
                etype = self._expr(node.value)
                if etype != node.var_type:
                    raise SemanticError(
                        f"Type mismatch: cannot assign {etype} to "
                        f"{node.var_type} variable {node.name!r}",
                        node.line, node.col, node.name)
            self.current.define(Symbol(node.name, node.var_type),
                                node.line, node.col)
            self.report.append(f"  Declared {node.var_type} {node.name}")

        elif isinstance(node, Assign):
            sym = self.current.lookup(node.name)
            if sym is None:
                raise SemanticError(
                    f"Variable {node.name!r} is used before assignment",
                    node.line, node.col, node.name)
            etype = self._expr(node.value)
            if etype != sym.sym_type:
                raise SemanticError(
                    f"Type mismatch: cannot assign {etype} to {sym.sym_type} "
                    f"variable {node.name!r}",
                    node.line, node.col, node.name)
            self.report.append(f"  Assigned to {node.name} ({sym.sym_type})")

        elif isinstance(node, Print):
            self._expr(node.expr)

        elif isinstance(node, If):
            self._expr(node.condition)
            self._block(node.then_block)
            self._block(node.else_block)

        elif isinstance(node, While):
            self._expr(node.condition)
            self._block(node.body)

        elif isinstance(node, For):
            if node.init: self._stmt(node.init)
            if node.condition: self._expr(node.condition)
            if node.step: self._stmt(node.step)
            self._block(node.body)

        elif isinstance(node, FuncDef):
            if node.name in self.functions:
                raise SemanticError(f"Function {node.name!r} already defined",
                                    node.line, node.col, node.name)
            self.functions[node.name] = node
            self.global_scope.define(Symbol(node.name, "func"),
                                     node.line, node.col)
            self.report.append(
                f"  Defined function {node.name}({', '.join(node.params)})")
            saved = self.current
            self.current = Scope(self.global_scope)
            for p in node.params:
                self.current.define(Symbol(p, "int"))
            self._block(node.body)
            self.current = saved

        elif isinstance(node, Return):
            if node.value: self._expr(node.value)

        elif isinstance(node, EndProgram):
            self.report.append("  stopZy encountered — program end")

    def _block(self, stmts):
        saved = self.current
        self.current = Scope(self.current)
        for s in stmts: self._stmt(s)
        self.current = saved

    def _expr(self, node) -> str:
        if isinstance(node, Literal):
            return node.lit_type
        if isinstance(node, Variable):
            sym = self.current.lookup(node.name)
            if sym is None:
                raise SemanticError(
                    f"Variable {node.name!r} is used before assignment",
                    node.line, node.col, node.name)
            return sym.sym_type
        if isinstance(node, Call):
            fn = self.functions.get(node.name)
            if fn is None:
                raise SemanticError(f"Unknown function {node.name!r}",
                                    node.line, node.col, node.name)
            for a in node.args: self._expr(a)
            return "int"
        if isinstance(node, UnaryOp):
            t = self._expr(node.operand)
            if node.op == "SUB" and t != "int":
                raise SemanticError("Unary '~-~' requires numeric operand",
                                    node.line, node.col)
            return t
        if isinstance(node, BinaryOp):
            lt = self._expr(node.left)
            rt = self._expr(node.right)
            if node.op in ("ADD", "SUB", "MUL", "DIV", "MOD", "POW"):
                if lt != "int" or rt != "int":
                    raise SemanticError(
                        f"Operator {node.op} requires two int operands; "
                        f"received {lt} and {rt}",
                        node.line, node.col)
                return "int"
            if node.op in ("GT", "LT", "EQ", "NEQ", "LEQ", "GEQ"):
                return "bool"
        raise SemanticError("Unknown expression node", node.line, node.col)