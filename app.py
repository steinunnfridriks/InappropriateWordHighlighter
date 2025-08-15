import html
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import re
from nltk.tokenize import sent_tokenize

# Use HuggingFace Hub model identifier
MODEL_ID = "steinunnfridriks/IceBERTBias"

# Load tokenizer and model from HuggingFace Hub
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForTokenClassification.from_pretrained(MODEL_ID)

# Initialize pipeline after model and tokenizer are loaded
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Map model labels (e.g., B-WOMEN) to CSS class names
LABEL_MAP = {
    "ADDICTION": "addiction",
    "DISABILITY": "disability",
    "ORIGIN": "origin",
    "GENERAL": "general",
    "LGBTQIA": "lgbtqia",
    "LOOKS": "looks",
    "PERSONAL": "personal",
    "PROFANITY": "profanity",
    "RELIGION": "religion",
    "SEXUAL": "sexual",
    "SOCIAL_STATUS": "social",
    "STUPIDITY": "stupidity",
    "VULGAR": "vulgar",
    "WOMEN": "women",
}

CATEGORY_DISPLAY_NAMES = {
    "addiction": "Addiction",
    "disability": "Disability",
    "origin": "Origin",
    "general": "General",
    "lgbtqia": "LGBTQIA+",
    "looks": "Looks",
    "personal": "Personal traits",
    "profanity": "Profanity",
    "religion": "Religion",
    "sexual": "Sexual",
    "social": "Social status",
    "stupidity": "Stupidity",
    "vulgar": "Vulgar",
    "women": "Misogyny"
}

def classify_text(text):
    """Classify spans sentence by sentence for better NER accuracy."""
    sentences = sent_tokenize(text)
    labeled_spans = []

    offset = 0  # Track character position shift for each sentence
    for sent in sentences:
        entities = ner_pipeline(sent)
        for ent in entities:
            label = ent["entity_group"]
            if label == "O":
                continue
            category = LABEL_MAP.get(label)
            if category:
                labeled_spans.append({
                    "start": ent["start"] + offset,
                    "end": ent["end"] + offset,
                    "category": category
                })
        offset += len(sent) + 1  # account for removed period or whitespace

    # Tokenize the input text into words using whitespace
    word_matches = list(re.finditer(r"\S+", text))
    html = []
    last_idx = 0

    for match in word_matches:
        start, end = match.start(), match.end()
        word = text[start:end]

        # Append any whitespace between last word and this one
        if last_idx < start:
            html.append(text[last_idx:start])

        matched_category = None
        for span in labeled_spans:
            if not (end <= span["start"] or start >= span["end"]):
                matched_category = span["category"]
                break

        if matched_category:
            display_name = CATEGORY_DISPLAY_NAMES.get(matched_category, matched_category)
            html.append(f'<span class="highlight {matched_category}" title="{display_name}" data-label="{display_name}">{word}</span>')
        else:
            html.append(word)

        last_idx = end

    if last_idx < len(text):
        html.append(text[last_idx:])

    return "".join(html)



class RequestHandler(SimpleHTTPRequestHandler):
    def _set_headers_json(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_POST(self):
        if self.path == "/process":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                text = data.get("text", "")
                html = classify_text(text)
                self._set_headers_json()
                self.wfile.write(json.dumps({"html": html}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Server error: {str(e)}")

    def do_GET(self):
        if self.path == "/":
            self.path = "/templates/index.html"
        elif self.path.startswith("/static/") or self.path.startswith("/templates/"):
            self.path = self.path.lstrip("/")
        elif not os.path.exists(self.path.lstrip("/")):
            self.send_error(404, "File not found")
            return
        return super().do_GET()


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    print("🔧 Running server at: http://localhost:8000")
    server_address = ("localhost", 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()
