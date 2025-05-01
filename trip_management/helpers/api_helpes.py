import re
import html



def plain_text_from_html(raw_html_text):
    """
    Removes HTML tags and returns plain text from a string containing HTML.
    """
    clean_text = re.sub(r'<[^>]+>', '', raw_html_text)
    clean_text = html.unescape(clean_text)
    clean_text = clean_text.strip()
    return clean_text


def format_decimal(value):
    return float(f"{float(value):.2f}") if value is not None else 0.00