import re

import pymupdf

SRC = "data/raw/paytm/paytm_ar_fy2026.pdf"
OUT = "data/sample/paytm_fy2026_sample.pdf"
KEYWORDS = ("data breach", "cyber", "kyc", "complaint")
PII = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+"  # email
    r"|(?:\+91[\s-]?)?\d{10}"  # 10-digit phone
    r"|\b\d{3,5}[\s-]\d{6,8}\b"  # phone with std code
    r"|[A-Z]{5}[0-9]{4}[A-Z]"  # PAN-like
)

src = pymupdf.open(SRC)
picked = []
for i, page in enumerate(src):
    text = page.get_text()
    if any(k in text.lower() for k in KEYWORDS) and not PII.search(text):
        picked.append(i)
    if len(picked) == 5:
        break

out = pymupdf.open()
for i in picked:
    out.insert_pdf(src, from_page=i, to_page=i)
out.save(OUT)
print("source pages (1-based):", [i + 1 for i in picked])
