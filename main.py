import os
import json
import fitz

def get_span_score(span, max_font, page_width):
    text = span["text"].strip()
    size = span["size"]
    flags = span["flags"]
    bbox = span["bbox"]

    if not text or len(text.split()) > 15 or not text.isprintable():
        return 0

    score = 0

    if size >= max_font * 0.95:
        score += 3
    elif size >= max_font * 0.75:
        score += 2
    elif size >= max_font * 0.60:
        score += 1

    if flags & 2 or flags & 8:
        score += 1

    if text.istitle() or text.isupper():
        score += 1

    if bbox[0] > page_width * 0.25 and bbox[2] < page_width * 0.75:
        score += 1

    return score

def classify_level(score):
    if score >= 5:
        return "H1"
    elif score >= 3:
        return "H2"
    elif score >= 2:
        return "H3"
    return None

def extract_headings_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    headings = []
    max_font = 0
    title = ""

    for block in doc[0].get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                size = span["size"]
                text = span["text"].strip()
                if size > max_font and len(text) > 1:
                    max_font = size
                    title = text

    for page_number, page in enumerate(doc, 1):
        page_width = page.rect.width
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    score = get_span_score(span, max_font, page_width)
                    level = classify_level(score)
                    if level:
                        headings.append({
                            "level": level,
                            "text": span["text"].strip(),
                            "page": page_number
                        })

    return {"title": title, "outline": headings}

def process_all_pdfs(input_dir="./pdfs", output_dir="./outputs"):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            try:
                print(f"Processing {filename}...")
                pdf_path = os.path.join(input_dir, filename)
                result = extract_headings_from_pdf(pdf_path)
                json_name = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(output_dir, json_name)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")

if __name__ == "__main__":
    process_all_pdfs()
