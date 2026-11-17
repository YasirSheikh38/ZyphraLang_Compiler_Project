"""Recursive-descent parser for ZyphraLang."""
from typing import List
from lexer import Token
from ast_nodes import *
from errors import SyntaxErrorZy


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # -------- helpers --------
    def _cur(self): return self.tokens[self.pos]
    def _check(self, kind): return self._cur().kind == kind

    def _match(self, *kinds):
        if self._cur().kind in kinds:
            tok = self._cur(); self.pos += 1; return tok
        expected = " or ".join(kinds)
        raise SyntaxErrorZy(
            f"Expected {expected} but found {self._cur().kind} "
            f"({self._cur().value!r})",
            self._cur().line, self._cur().col, self._cur().value)

    # -------- program --------
    def parse(self) -> Program:
        body = []
        while not self._check("EOF"):
            body.append(self._statement())
        return Program(body=body)

    # -------- statements --------
    def _statement(self) -> Node:
        t = self._cur()
        if t.kind == "PRINT":      return self._print_stmt()
        if t.kind == "INT_TYPE":   return self._var_decl("int")
        if t.kind == "STR_TYPE":   return self._var_decl("string")
        if t.kind == "BOOL_TYPE":  return self._var_decl("bool")
        if t.kind == "IF":         return self._if_stmt()
        if t.kind == "WHILE":      return self._while_stmt()
        if t.kind == "FOR":        return self._for_stmt()
        if t.kind == "FUNC":       return self._func_def()
        if t.kind == "RETURN":     return self._return_stmt()
        if t.kind == "END":        return self._end_stmt()
        if t.kind == "ID":         return self._assign_stmt()
        raise SyntaxErrorZy(
            f"Unexpected token {t.kind} ({t.value!r}) at start of statement",
            t.line, t.col, t.value)

    def _print_stmt(self):
        tok = self._match("PRINT")
        self._match("LPAREN")
        expr = self._expr()
        self._match("RPAREN")
        self._match("SEMI")
        n = Print(expr=expr); n.line, n.col = tok.line, tok.col; return n

    def _var_decl(self, vtype):
        tok = self._cur(); self.pos += 1
        name_tok = self._match("ID")
        value = None
        if self._check("ASSIGN"):
            self.pos += 1
            value = self._expr()
        self._match("SEMI")
        n = VarDecl(var_type=vtype, name=name_tok.value, value=value)
        n.line, n.col = tok.line, tok.col; return n

    def _assign_stmt(self):
        name_tok = self._match("ID")
        self._match("ASSIGN")
        value = self._expr()
        self._match("SEMI")
        n = Assign(name=name_tok.value, value=value)
        n.line, n.col = name_tok.line, name_tok.col; return n

    def _if_stmt(self):
        tok = self._match("IF")
        self._match("LPAREN")
        cond = self._expr()
        self._match("RPAREN")
        then_block = self._block()
        else_block = []
        if self._check("ELSE"):
            self.pos += 1
            else_block = self._block()
        n = If(condition=cond, then_block=then_block, else_block=else_block)
        n.line, n.col = tok.line, tok.col; return n

    def _while_stmt(self):
        tok = self._match("WHILE")
        self._match("LPAREN")
        cond = self._expr()
        self._match("RPAREN")
        body = self._block()
        n = While(condition=cond, body=body); n.line, n.col = tok.line, tok.col; return n

    def _for_stmt(self):
        tok = self._match("FOR")
        self._match("LPAREN")
        if self._check("SEMI"):
            self.pos += 1; init = None
        elif self._check("INT_TYPE") or self._check("STR_TYPE") or self._check("BOOL_TYPE"):
            init = self._var_decl("int")
        else:
            init = self._assign_stmt()
        cond = None if self._check("SEMI") else self._expr()
        self._match("SEMI")
        step = None if self._check("RPAREN") else self._assign_stmt_no_semi()
        self._match("RPAREN")
        body = self._block()
        n = For(init=init, condition=cond, step=step, body=body)
        n.line, n.col = tok.line, tok.col; return n

    def _assign_stmt_no_semi(self):
        name_tok = self._match("ID")
        self._match("ASSIGN")
        value = self._expr()
        n = Assign(name=name_tok.value, value=value)
        n.line, n.col = name_tok.line, name_tok.col; return n

    def _func_def(self):
        tok = self._match("FUNC")
        name_tok = self._match("ID")
        self._match("LPAREN")
        params = []
        if not self._check("RPAREN"):
            params.append(self._match("ID").value)
            while self._check("COMMA"):
                self.pos += 1
                params.append(self._match("ID").value)
        self._match("RPAREN")
        body = self._block()
        n = FuncDef(name=name_tok.value, params=params, body=body)
        n.line, n.col = tok.line, tok.col; return n

    def _return_stmt(self):
        tok = self._match("RETURN")
        value = None if self._check("SEMI") else self._expr()
        self._match("SEMI")
        n = Return(value=value); n.line, n.col = tok.line, tok.col; return n

    def _end_stmt(self):
        tok = self._match("END"); self._match("SEMI")
        n = EndProgram(); n.line, n.col = tok.line, tok.col; return n

    def _block(self):
        self._match("LBRACE")
        stmts = []
        while not self._check("RBRACE") and not self._check("EOF"):
            stmts.append(self._statement())
        self._match("RBRACE")
        return stmts

    # -------- expressions (precedence climbing) --------
    _PRECEDENCE = {
        "EQ": 1, "NEQ": 1, "GT": 1, "LT": 1, "LEQ": 1, "GEQ": 1,
        "ADD": 2, "SUB": 2,
        "MUL": 3, "DIV": 3, "MOD": 3,
        "POW": 4,                              # right-associative handled below
    }

    def _expr(self): return self._binary(0)

    def _binary(self, min_prec):
        left = self._unary()
        while self._cur().kind in self._PRECEDENCE:
            prec = self._PRECEDENCE[self._cur().kind]
            if prec < min_prec: break
            op_tok = self._cur(); self.pos += 1
            # right-assoc for POW
            right = self._binary(prec + 1 if op_tok.kind != "POW" else prec)
            n = BinaryOp(op=op_tok.kind, left=left, right=right)
            n.line, n.col = op_tok.line, op_tok.col
            left = n
        return left

    def _unary(self):
        if self._check("SUB"):
            tok = self._cur(); self.pos += 1
            operand = self._unary()
            n = UnaryOp(op="SUB", operand=operand)
            n.line, n.col = tok.line, tok.col; return n
        return self._primary()

    def _primary(self):
        t = self._cur()
        if t.kind in ("INT", "FLOAT"):
            self.pos += 1
            n = Literal(value=t.value, lit_type="int"); n.line, n.col = t.line, t.col
            return n
        if t.kind == "STRING":
            self.pos += 1
            n = Literal(value=t.value, lit_type="string"); n.line, n.col = t.line, t.col
            return n
        if t.kind == "BOOL":
            self.pos += 1
            n = Literal(value=t.value, lit_type="bool"); n.line, n.col = t.line, t.col
            return n
        if t.kind == "ID":
            self.pos += 1
            if self._check("LPAREN"):
                self.pos += 1
                args = []
                if not self._check("RPAREN"):
                    args.append(self._expr())
                    while self._check("COMMA"):
                        self.pos += 1; args.append(self._expr())
                self._match("RPAREN")
                n = Call(name=t.value, args=args); n.line, n.col = t.line, t.col
                return n
            n = Variable(name=t.value); n.line, n.col = t.line, t.col
            return n
        if t.kind == "LPAREN":
            self.pos += 1
            e = self._expr(); self._match("RPAREN"); return e
        raise SyntaxErrorZy(
            f"Expected an expression but found {t.kind} ({t.value!r})",
            t.line, t.col, t.value)