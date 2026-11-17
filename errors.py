"""Custom error classes for ZyphraLang compiler phases."""

class ZyphraError(Exception):
    phase = "Error"

    def __init__(self, message, line=0, col=0, token=""):
        self.message = message
        self.line = line
        self.col = col
        self.token = token
        super().__init__(self.format())

    def format(self):
        loc = f"Line {self.line}, Col {self.col}" if self.line else ""
        tok = f"\n  Token: {self.token!r}" if self.token else ""
        return f"[{self.phase}] {loc}\n  {self.message}{tok}"


class LexicalError(ZyphraError):    phase = "LexicalError"
class SyntaxErrorZy(ZyphraError):   phase = "SyntaxError"
class SemanticError(ZyphraError):   phase = "SemanticError"
class RuntimeErrorZy(ZyphraError):  phase = "RuntimeError"