import os
import fitz
import re
from collections import Counter
# import spacy
# nlp = spacy.load("en_core_web_sm")
import pdfplumber

import re

def is_invalid_text(text):
    text = text.strip()
    
    # Reject headings that start with "Figure", "Fig", "Table" (case-insensitive)
    if re.match(r'^(Figure|Fig|TABLE|Table|TABLES|Tables)\b', text, re.IGNORECASE):
        return True

    # Reject if only digits
    if re.fullmatch(r'\d+', text):
        return True
    
    if re.match(r'^[{(\[]', text):
        return True
    
    if re.match(r'^[a-z]', text):
        return True


    # Reject random alphanumeric codes like T1, AB12, X7, etc. (1–4 letters + digits)
    if re.fullmatch(r'[A-Za-z]{1,4}\d{1,4}', text):
        return True

    # # Reject if mostly symbols or garbage-looking (alphanumeric + special chars, no spaces)
    # if re.fullmatch(r'[A-Za-z0-9@#$%^&*()_+=!~`|\\/:;\'",.<>?-]{6,}', text) and ' ' not in text:
    #     return True

    # Reject overly short (1–2 characters)
    if len(text) <= 2:
        return True

    return False

    
def is_heading_pattern(text):  
    words = text.strip().split()
    if words:
        capitalized = sum(1 for w in words if w.isupper() or (len(w) > 1 and w[0].isupper()))
        capital_ratio = capitalized / len(words)
    else:
        return False  # No words at all
    
    patterns = [
        r'^[A-Z][A-Z\s]{3,}$',
        r'^(Chapter|CHAPTER|Unit|UNIT|Lesson|LESSON)\s+\d+',
        r'^\d+(\.\d+)*\s+.+$',
        r'^[IVXLC]+\.\s+.+$',
        r'^[A-Z]\.\s+.+$',
        r'^(Abstract|Literature|Dataset|Proposed work|Introduction|Conclusion|References|Methology)$',
    ]
    return any(re.match(p, text) for p in patterns) or capital_ratio >= 0.5

def is_strictly_centered(x0, x1, page_width, margin_ratio=0.01):
    block_center = (x0 + x1) / 2
    page_center = page_width / 2
    margin = page_width * margin_ratio
    return abs(block_center - page_center) <= margin


# 👇 NEW: Get table bounding boxes using pdfplumber
def get_table_bounding_boxes(pdf_path):
    table_bboxes_by_page = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            table_bboxes_by_page[page_num] = []
            tables = page.find_tables()
            for table in tables:
                if table.bbox:  # (x0, top, x1, bottom)
                    table_bboxes_by_page[page_num].append(table.bbox)
    return table_bboxes_by_page

# 👇 Helper: Check if line bbox overlaps with any table bbox
def overlaps_with_table(line_bbox, table_bboxes):
    x0, y0, x1, y1 = line_bbox
    for tx0, ty0, tx1, ty1 in table_bboxes:
        # Check vertical and horizontal overlap
        if not (x1 < tx0 or x0 > tx1 or y1 < ty0 or y0 > ty1):
            return True
    return False

def is_mostly_uppercase(text, threshold=0.7):
    words = text.strip().split()
    if not words:
        return False
    
    count = 0
    for w in words:
        if w.isupper() or (w[0].isupper() and w[1:].islower()):
            count += 1
    
    return count / len(words) >= threshold


# def is_title_cased_or_uppercase(text, threshold=0.9):
#     doc = nlp(text)
#     nouns = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN")]
    
#     if not nouns:
#         return False

#     capitalized_nouns = [w for w in nouns if w.isupper() or (w[0].isupper() and w[1:].islower())]
    
#     return len(capitalized_nouns) / len(nouns) >= threshold

def ends_with_valid_punctuation(text):
    text = text.strip()
    return not text.endswith(('.', ',', ';'))

def is_span_bold(span):
    return "bold" in span["font"].lower()

from collections import Counter

def classify_heading_levels(font_stats):
    # Round font sizes
    rounded_stats = [(font, round(size, 1), color) for font, size, color in font_stats]
    
    # Count occurrences of (font, size, color)
    font_counter = Counter(rounded_stats)

    # Get the most common font tuple (body text)
    most_common_font = font_counter.most_common(1)[0][0]
    body_font_size = most_common_font[1]  # the size of most common font

    # Filter only font sizes >= body text size
    filtered_sizes = set()
    for font, size, color in font_counter:
        if size >= body_font_size:
            filtered_sizes.add(size)

    if len(filtered_sizes) < 3:
        print("Not enough heading font sizes found.")
        return {}

    # Sort heading font sizes in descending order
    sorted_sizes = sorted(filtered_sizes, reverse=True)

    # Divide into H1, H2, H3
    num_sizes = len(sorted_sizes)
    group_size = num_sizes // 3
    remainder = num_sizes % 3

    h1_sizes = sorted_sizes[:group_size + (1 if remainder > 0 else 0)]
    h2_sizes = sorted_sizes[len(h1_sizes):len(h1_sizes)+group_size + (1 if remainder > 1 else 0)]
    h3_sizes = sorted_sizes[len(h1_sizes)+len(h2_sizes):]

    # Map sizes to heading levels
    size_to_level = {}
    for s in h1_sizes:
        size_to_level[s] = "H1"
    for s in h2_sizes:
        size_to_level[s] = "H2"
    for s in h3_sizes:
        size_to_level[s] = "H3"

    return size_to_level

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)
    table_bboxes_by_page = get_table_bounding_boxes(pdf_path)
    print(f"📄 Analyzing '{pdf_path}' for heading-like lines scoring 3+...\n")

    # font_sizes = []
    font_stats = []
    headings = []

    # Pass 1: Gather all font sizes to find most-used and max
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    # font_sizes.append(round(span["size"], 1))  # round for stability
                    font_stats.append((span["font"], round(span["size"], 1), span["color"]))

    # if not font_sizes:
    if not font_stats:
        print("No text found.")
        return

    font_counts = Counter(font_stats)
    most_common_font_stat = font_counts.most_common(1)[0][0]
    max_font_size = max(font_stats)

    size_to_level = classify_heading_levels(font_stats)
    
    # Pass 2: Evaluate lines
    for page_num, page in enumerate(doc, start=1):
        # if page_num <24:  # Skip pages 1-23 and 26+
        #     continue
        # if page_num > 1:
        #     break
        page_width = page.rect.width
        table_bboxes = table_bboxes_by_page.get(page_num - 1, [])
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"][:2]:
            # for line in block["lines"]:
                text = "".join([span["text"] for span in line["spans"]]).strip()
                if not text:
                    continue
                
                if is_invalid_text(text) or not ends_with_valid_punctuation(text): 
                    # print(text)
                    # print()
                    continue

                # Get bounding box
                x0s = [span["bbox"][0] for span in line["spans"]]
                y0s = [span["bbox"][1] for span in line["spans"]]
                x1s = [span["bbox"][2] for span in line["spans"]]
                y1s = [span["bbox"][3] for span in line["spans"]]

                line_bbox = (min(x0s), min(y0s), max(x1s), max(y1s))

                # ✅ Skip if inside table
                if overlaps_with_table(line_bbox, table_bboxes):
                    continue
                
                # Gather font sizes, bold flags, fonts, colors
                font_sizes_line = [round(span["size"], 1) for span in line["spans"]]
                bold_flags = [is_span_bold(span) for span in line["spans"]]
                fonts = [span["font"] for span in line["spans"]]
                colors = [span["color"] for span in line["spans"]]

                min_x0 = min(x0s)
                max_x1 = max(x1s)
                avg_font = sum(font_sizes_line) / len(font_sizes_line)
                font_diff = most_common_font_stat[0] not in fonts
                color_diff = most_common_font_stat[2] not in colors
                # Score based on criteria
                score = 0.0
                
                # 5) Heading pattern or 70% uppercase                
                if is_heading_pattern(text): #or is_mostly_uppercase(text):
                    score += 1.0
                # else:
                #     continue  # Skip if not a heading pattern

                # 1) Font size: greater than most-used but not max
                if avg_font > most_common_font_stat[1]+0.5:
                    score += 1.0

                # 2) Centered
                if is_strictly_centered(min_x0, max_x1, page_width):
                    score += 1.0

                # 3) Bold
                if all(bold_flags):
                    score += 1.0

                # 4) Valid punctuation
                if ends_with_valid_punctuation(text):
                    score += 1.0
                    
                if font_diff: score += 0.5
                if color_diff: score += 0.5
                
                # Later, when processing:
                rounded_size = round(span["size"], 1)
                level = "H3"  # Default level
                if rounded_size in size_to_level:
                    level = size_to_level[rounded_size]

                # # Print if 3 or more criteria are satisfied
                if score >= 2.5:
                    rounded_size = round(font_sizes_line[0], 1)
                    level = size_to_level.get(rounded_size, "H3")
                    headings.append({
                        "text": text,
                        "score": score,
                        "level": level,
                        "page_number": page_num,
                        "font_size": avg_font,
                        "document": os.path.basename(pdf_path)
                    })
                    # print(f"✅ Page {page_num}: Scored {score}/5")
                    # print(f"    Text: {text} , Level:{level}")
                    # print(f"    Avg Font: {avg_font:.1f}, Most Common Font: {most_common_font_stat[0]}, Size: {most_common_font_stat[1]}, Max Size: {max_font_size}, Color: {most_common_font_stat[2]}")
                    # print(f"    Bold: {all(bold_flags)}, Centered: {is_strictly_centered(min_x0, max_x1, page_width)}")
                    # print(f"    Ends valid: {ends_with_valid_punctuation(text)}")
                    # print(f"    Heading pattern: {is_heading_pattern(text)}, 70% uppercase: {is_mostly_uppercase(text)}\n")
    return headings



# Run the analysis
# find_heading_like_lines(r"Challenge_1a/sample_pdfs/pdfs/South of France - Cities.pdf")