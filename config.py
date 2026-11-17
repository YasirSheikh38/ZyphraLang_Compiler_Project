"""
ZyphraLang language configuration.
Edit this file to extend the language — nothing else needs to change.
"""

LANGUAGE_NAME = "ZyphraLang"

# ============================================================
# KEYWORDS (custom → internal token kind)
# ============================================================
KEYWORDS = {
    "whenever":    "WHILE",
    "echoOut":     "PRINT",
    "whenTrue":    "IF",
    "elseWay":     "ELSE",
    "spin":        "FOR",
    "stopZy":      "END",
    "craft":       "FUNC",
    "giveBack":    "RETURN",
    "alfaz":       "STR_TYPE",
    "decision":    "BOOL_TYPE",
    "wholenumber": "INT_TYPE",
}

# ============================================================
# OPERATORS — ordered longest-first inside the lexer
# ============================================================
OPERATORS = {
    ":= >".replace(" ", ""):  "ASSIGN",   # :=>   assignment
    "~+~":   "ADD",
    "~-~":   "SUB",
    "~x~":   "MUL",
    "~%~":   "DIV",
    "~#~":   "MOD",
    "~^^~":  "POW",
    ">>?":   "GT",
    "?<<":   "LT",
    "==?":   "EQ",
    "<>?":   "NEQ",
    "?<=<":  "LEQ",
    ">=?>":  "GEQ",
}

# ============================================================
# LITERALS / PUNCTUATION
# ============================================================
STATEMENT_TERMINATOR = ";"
COMMENT_PREFIX       = "##"
STRING_QUOTE         = '"'
BOOL_TRUE            = "rightOn"     # custom boolean literals
BOOL_FALSE           = "nope"
LPAREN = "("
RPAREN = ")"
LBRACE = "{"
RBRACE = "}"
COMMA  = ","

# ============================================================
# SAFE BUILTINS exposed to executed programs
# ============================================================
SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len":   len,
    "int":   int,
    "str":   str,
    "bool":  bool,
    "pow":   pow,
}