import re


_DONE_PATTERNS = (
    r"\bya\s+(?:lo\s+)?(?:hice|hice|arregle|repare|solucione|termine|finalice|resolvi)\b",
    r"\b(?:quedo|esta)\s+(?:arreglado|resuelto|solucionado|listo)\b",
)

_REQUESTER_PATTERNS = (
    r"\blo pidio\s+([^.!,]+)",
    r"\blo pidió\s+([^.!,]+)",
    r"\bsolicitante\s*[:\-]\s*([^.!,]+)",
    r"\bla jueza\s+([^.!,]+)",
    r"\bel juez\s+([^.!,]+)",
    r"\bla dra\.?\s+([^.!,]+)",
    r"\bel dr\.?\s+([^.!,]+)",
)


def parse_voice_command_locally(text_command: str) -> dict:
    text = (text_command or "").strip()
    lowered = text.lower()

    is_done = any(re.search(pattern, lowered, re.IGNORECASE) for pattern in _DONE_PATTERNS)

    solicitante = ""
    for pattern in _REQUESTER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            solicitante = match.group(1).strip(" .,:;")
            break

    descripcion = text
    for prefix in ("ya arregle", "ya arreglé", "ya repare", "ya reparé", "ya solucione", "ya solucioné", "lo pidio", "lo pidió"):
        if lowered.startswith(prefix):
            descripcion = text[len(prefix):].strip(" .,:;-")
            break

    return {
        "descripcion": descripcion or text,
        "solicitante": solicitante,
        "is_done": is_done,
        "solucion": text if is_done else "",
        "mode": "local",
    }
