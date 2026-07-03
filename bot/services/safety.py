from __future__ import annotations

import re


SENSITIVE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(password|passcode|secret|token|api[_\s-]?key|private[_\s-]?key)\b",
        r"\b(seed phrase|recovery phrase|mnemonic)\b",
        r"\b(card number|cvv|cvc|iban|swift)\b",
        r"\b(passport|ssn|social security)\b",
        r"\b(парол[ья]|секрет|токен|ключ api|api ключ|приватн\w*\s+ключ)\b",
        r"\b(банковск[аяуюие]+ карт[ауы]|номер карт[ы]|паспорт)\b",
    )
]


def is_sensitive_memory(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)
