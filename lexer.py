"""Lexical analyzer for ZyphraLang."""
from typing import List
from config import (KEYWORDS, OPERATORS, STATEMENT_TERMINATOR, COMMENT_PREFIX,
                    STRING_QUOTE, BOOL_TRUE, BOOL_FALSE,
                    LPAREN, RPAREN, LBRACE, RBRACE, COMMA)
from errors import LexicalError


class Token:
    def __init__(self, kind, value, line, col):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, L{self.line}:C{self.col})"


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    # --------------------------------------------------
    def _advance(self, n=1):
        for _ in range(n):
            if self.pos < len(self.src):
                if self.src[self.pos] == "\n":
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.pos += 1

    def _peek(self, k=0):
        i = self.pos + k
        return self.src[i] if i < len(self.src) else ""

    # --------------------------------------------------
    def tokenize(self) -> List[Token]:
        # longest operator first so "?<=<" beats "?<<"
        sorted_ops = sorted(OPERATORS.keys(), key=len, reverse=True)

        while self.pos < len(self.src):
            c = self._peek()

            if c in " \t\r\n":
                self._advance(); continue

            if self.src.startswith(COMMENT_PREFIX, self.pos):
                while self.pos < len(self.src) and self._peek() != "\n":
                    self._advance()
                continue

            if c == STRING_QUOTE:
                self._read_string(); continue

            if c.isdigit():
                self._read_number(); continue

            if c.isalpha() or c == "_":
                self._read_identifier(); continue

            matched = None
            for op in sorted_ops:
                if self.src.startswith(op, self.pos):
                    matched = op; break
            if matched:
                self.tokens.append(Token(OPERATORS[matched], matched,
                                         self.line, self.col))
                self._advance(len(matched))
                continue

            single = {
                STATEMENT_TERMINATOR: "SEMI",
                LPAREN: "LPAREN", RPAREN: "RPAREN",
                LBRACE: "LBRACE", RBRACE: "RBRACE",
                COMMA: "COMMA",
            }
            if c in single:
                self.tokens.append(Token(single[c], c, self.line, self.col))
                self._advance(); continue

            raise LexicalError(
                f"Unknown character {c!r}. Not part of ZyphraLang.",
                self.line, self.col, c)

        self.tokens.append(Token("EOF", None, self.line, self.col))
        return self.tokens

    # --------------------------------------------------
    def _read_string(self):
        sl, sc = self.line, self.col
        self._advance()  # open quote
        buf = []
        while self.pos < len(self.src) and self._peek() != STRING_QUOTE:
            if self._peek() == "\\" and self._peek(1) == "n":
                buf.append("\n"); self._advance(2)
            else:
                buf.append(self._peek()); self._advance()
        if self.pos >= len(self.src):
            raise LexicalError("Unterminated string literal", sl, sc)
        self._advance()  # close quote
        self.tokens.append(Token("STRING", "".join(buf), sl, sc))

    def _read_number(self):
        sl, sc = self.line, self.col
        buf = []
        while self._peek().isdigit():
            buf.append(self._peek()); self._advance()
        # float support
        if self._peek() == "." and self._peek(1).isdigit():
            buf.append("."); self._advance()
            while self._peek().isdigit():
                buf.append(self._peek()); self._advance()
            self.tokens.append(Token("FLOAT", float("".join(buf)), sl, sc))
        else:
            self.tokens.append(Token("INT", int("".join(buf)), sl, sc))

    def _read_identifier(self):
        sl, sc = self.line, self.col
        buf = []
        while self._peek().isalnum() or self._peek() == "_":
            buf.append(self._peek()); self._advance()
        word = "".join(buf)

        if word in KEYWORDS:
            self.tokens.append(Token(KEYWORDS[word], word, sl, sc))
        elif word == BOOL_TRUE:
            self.tokens.append(Token("BOOL", True, sl, sc))
        elif word == BOOL_FALSE:
            self.tokens.append(Token("BOOL", False, sl, sc))
        else:
            py_keywords = {"print","if","else","for","while","def","return",
                           "int","str","bool","True","False","elif","import",
                           "class","lambda","with","try","except","finally"}
            if word in py_keywords:
                raise LexicalError(
                    f"Unknown keyword {word!r}. This is Python syntax, not "
                    f"ZyphraLang. Use a ZyphraLang keyword instead.",
                    sl, sc, word)
            self.tokens.append(Token("ID", word, sl, sc))