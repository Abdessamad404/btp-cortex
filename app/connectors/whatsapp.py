import re


def parse_whatsapp(filepath: str) -> str:
    """
    Parse a WhatsApp exported .txt file into clean conversation text.

    WhatsApp exports look like:
        12/03/2024, 14:32 - Youssef: Les fondations sont terminées
        12/03/2024, 14:35 - Ahmed: Ok, on commence demain

    We strip timestamps and keep "Sender: message" format.
    Handles both 24h and 12h (AM/PM) timestamp formats.
    Multi-line messages (continuation lines without a timestamp) are appended
    to the previous message.
    """

    # Matches lines that start with a WhatsApp timestamp
    # Supports: DD/MM/YYYY or D/M/YY with 24h or 12h AM/PM time
    message_pattern = re.compile(
        r"^\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?:\s?(?:AM|PM))?\s?-\s(.+?):\s(.+)$"
    )

    # Lines that carry no useful information
    SKIP_PATTERNS = [
        "<Media omitted>",
        "Messages and calls are end-to-end encrypted",
        "You deleted this message",
        "This message was deleted",
        "image omitted",
        "video omitted",
        "audio omitted",
        "document omitted",
        "Contact card omitted",
    ]

    lines = []

    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            # Skip media and system messages
            if any(pattern in line for pattern in SKIP_PATTERNS):
                continue

            match = message_pattern.match(line)
            if match:
                sender = match.group(1).strip()
                message = match.group(2).strip()
                lines.append(f"{sender}: {message}")
            elif lines and not re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}", line):
                # This line has no timestamp — it's a continuation of the previous message
                lines[-1] += f" {line}"

    return "\n".join(lines)
