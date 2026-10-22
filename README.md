# <Your product name>

> Fill this top section from your Examate project card on Day 1. Replace every line in angle brackets.

## Problem
Information-systems audit trainees at CA firms spend hours reading 100+ page annual reports and BRSRs to find breach counts, RBI KYC actions and fraud losses for fintech clients. The same PDFs contain officers’ names, emails, phone numbers and PAN-like strings, and uploaded working papers can carry hidden text that tries to hijack an AI tool. WalletWatch gives audit-ready answers with page citations, masks personal data before indexing and again before answering, and treats every document as untrusted data. Auditors can also see what was masked in each cited passage, and why.

## Who it is for
Information-systems audit trainee at a Chennai chartered accountant firm that reviews fintech companies’ IT and data-security controls

## Signature feature
Redaction log: for every cited passage, the auditor can see what was masked (email, phone, PAN-like string, name with contact details) and why. The log stores type, position and reason, never the original value.

## Hardest problem (my interview story)
My tool had to hide personal data like emails, phone numbers and officer names, and also ignore hidden instructions inside uploaded files. At first, my redaction missed some personal details, for example a name written next to a contact number in a table, and some hidden instructions got through in testing.

I found this by running my test sets: questions that try to make the tool leak personal data, and PDFs with planted attack text. I fixed it by adding more redaction rules and checking the answer once more before showing it. After that, the leaks stopped in my tests.

## Dataset
| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| One 97 Communications (Paytm) annual reports and BRSRs | <https://ir.paytm.com/annual-reports> | 4 | 1400 | Public company filings |

## 10 real questions
See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Run it
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # Windows: copy .env.example .env
uvicorn app.main:app --reload
curl localhost:8000/health
```

## Live link
<Added in Week 2>
