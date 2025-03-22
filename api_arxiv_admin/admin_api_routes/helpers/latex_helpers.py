import re

# Mapping of LaTeX accent commands to UTF-8 characters
LATEX_ACCENTS = {
    r"\\'a": "á", r"\\'e": "é", r"\\'i": "í", r"\\'o": "ó", r"\\'u": "ú",
    r"\\'A": "Á", r"\\'E": "É", r"\\'I": "Í", r"\\'O": "Ó", r"\\'U": "Ú",
    r"\\`a": "à", r"\\`e": "è", r"\\`i": "ì", r"\\`o": "ò", r"\\`u": "ù",
    r"\\^a": "â", r"\\^e": "ê", r"\\^i": "î", r"\\^o": "ô", r"\\^u": "û",
    r'\\"a': "ä", r'\\"e': "ë", r'\\"i': "ï", r'\\"o': "ö", r'\\"u': "ü",
    r'\\"A': "Ä", r'\\"E': "Ë", r'\\"I': "Ï", r'\\"O': "Ö", r'\\"U': "Ü",
    r"\\~n": "ñ", r"\\~N": "Ñ",
    r"\\c{c}": "ç", r"\\c{C}": "Ç",
    r"\\={a}": "ā", r"\\={A}": "Ā",
    r"\\.{i}": "ı̇",  # dot above lowercase i
    r"\\v{c}": "č", r"\\v{C}": "Č",
    r"\\H{o}": "ő", r"\\H{O}": "Ő",
    r"\\u{g}": "ğ", r"\\u{G}": "Ğ",
}

def convert_latex_accents(text: str) -> str:
    for latex, utf8 in LATEX_ACCENTS.items():
        text = re.sub(latex, utf8, text)
    return text
