import imaplib
import email
from email.header import decode_header


def _decode_str(value) -> str:
    """
    Decode an email header value into a plain string.

    Email headers are often encoded like: =?UTF-8?B?SGVsbG8=?=
    This function decodes them into readable text.
    """
    if value is None:
        return ""

    decoded_parts = decode_header(value)
    result = []

    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            # Decode bytes using the detected charset, fall back to utf-8
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)

    return " ".join(result)


def _get_body(msg) -> str:
    """
    Extract the plain text body from an email message.

    Emails can be:
    - Simple (single part): just grab the payload
    - Multipart (mixed/alternative): walk through parts and find text/plain
    We skip attachments — we only want the readable text body.
    """
    body = ""

    if msg.is_multipart():
        # Walk through every part of the email
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            # We want text/plain parts that are not file attachments
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
    else:
        # Single-part email
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")

    return body.strip()


def fetch_emails(
    host: str,
    port: int,
    username: str,
    password: str,
    folder: str = "INBOX",
    max_emails: int = 50,
) -> str:
    """
    Connect to an IMAP server and fetch the most recent emails.

    IMAP (Internet Message Access Protocol) is a standard protocol for reading
    emails from a server without downloading them permanently. Gmail, Outlook,
    and most email providers support it.

    Returns all emails concatenated as a single text string ready for chunking.
    Credentials are used only for this request and never stored.
    """

    # Connect to the IMAP server over SSL (port 993 is the standard for SSL)
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(username, password)

    # Select the mailbox folder (INBOX by default)
    conn.select(folder)

    # Search for all email IDs in the folder
    _, message_ids = conn.search(None, "ALL")
    ids = message_ids[0].split()

    if not ids:
        conn.logout()
        return ""

    # Limit to the most recent N emails
    ids = ids[-max_emails:]

    texts = []

    # Fetch newest first (reverse the list)
    for msg_id in reversed(ids):
        # RFC822 = fetch the full raw email
        _, msg_data = conn.fetch(msg_id, "(RFC822)")
        raw_email = msg_data[0][1]

        # Parse the raw bytes into a structured email object
        msg = email.message_from_bytes(raw_email)

        subject = _decode_str(msg.get("Subject", ""))
        sender = _decode_str(msg.get("From", ""))
        date = msg.get("Date", "")
        body = _get_body(msg)

        # Only include emails that have a readable text body
        if body:
            email_text = (
                f"De : {sender}\n" f"Date : {date}\n" f"Sujet : {subject}\n\n" f"{body}"
            )
            texts.append(email_text)

    conn.logout()

    # Join all emails with a clear separator so the chunker can work naturally
    return "\n\n---\n\n".join(texts)
