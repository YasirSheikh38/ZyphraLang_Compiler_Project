"""AST node definitions for ZyphraLang."""
from dataclasses import dataclass, field
from typing import Any, List, Optional


class Node:
    line: int = 0
    col: int = 0


# ---------- Expressions ----------
@dataclass
class Literal(Node):
    value: Any
    lit_type: str          # 'int' | 'string' | 'bool'

@dataclass
class Variable(Node):
    name: str

@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class Call(Node):
    name: str
    args: List[Node]

# ---------- Statements ----------
@dataclass
class VarDecl(Node):
    var_type: str
    name: str
    value: Optional[Node]

@dataclass
class Assign(Node):
    name: str
    value: Node

@dataclass
class Print(Node):
    expr: Node

@dataclass
class If(Node):
    condition: Node
    then_block: List[Node]
    else_block: List[Node]

@dataclass
class While(Node):
    condition: Node
    body: List[Node]

@dataclass
class For(Node):
    init: Optional[Node]
    condition: Optional[Node]
    step: Optional[Node]
    body: List[Node]

@dataclass
class FuncDef(Node):
    name: str
    params: List[str]
    body: List[Node]

@dataclass
class Return(Node):
    value: Optional[Node]

@dataclass
class EndProgram(Node):
    pass

@dataclass
class Program(Node):
    body: List[Node] = field(default_factory=list)