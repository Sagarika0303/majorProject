import spacy
from spacy.matcher import Matcher

def extract_name(nlp_text, matcher=None):
    """
    Improved name extraction function that matches full names with two or three consecutive capitalized words.
    """
    if matcher is None:
        matcher = Matcher(nlp_text.vocab)

    # Pattern to match two or three consecutive capitalized words (e.g., "John Doe", "Mary Ann Smith")
    pattern = [
        {"IS_TITLE": True, "OP": "+"},
        {"IS_TITLE": True, "OP": "+"},
        {"IS_TITLE": True, "OP": "?"},
    ]

    matcher.add("NAME", [pattern])

    matches = matcher(nlp_text)
    for _, start, end in matches:
        span = nlp_text[start:end]
        span_text = span.text.strip()
        # Basic validation: exclude spans containing digits or common unwanted words
        if any(char.isdigit() for char in span_text):
            continue
        lower_span = span_text.lower()
        unwanted_words = {"name", "email", "phone", "contact", "address", "education", "experience", "skills"}
        if any(word in lower_span for word in unwanted_words):
            continue
        # Return the first valid match
        return span_text

    # Fallback: return None if no valid name found
    return None
