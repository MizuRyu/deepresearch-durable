def truncate_text(text: str, length: int = 400) -> str:
    if not isinstance(text, str):
        return text
    return text if len(text) <= length else text[:length] + "..."