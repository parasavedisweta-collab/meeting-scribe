"""
Underwriting Copilot  –  multi-speaker transcription + AI underwriting assistant
  STT         : faster-whisper  (base.en, local)
  Diarization : SpeechBrain ECAPA-TDNN, 2-speaker constraint
  AI Copilot  : Gemini 2.0 Flash → fallback llama3.2

Workflow:
  1. User selects a borrower scenario from the UI
  2. Left panel shows borrower profile summary
  3. Underwriter starts conversation with borrower
  4. After each borrower utterance, copilot suggests next question
  5. Collected data points tracked live on the UI
"""

import asyncio
import json
import os
import time

# Load .env file if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import numpy as np
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
from google import genai
from google.genai import types as genai_types
from openai import OpenAI

from scenarios import SCENARIOS, get_summary

# ── Models ────────────────────────────────────────────────────────
print("Loading Whisper base.en …")
stt = WhisperModel("base.en", device="cpu", compute_type="int8")
print("Whisper ready.")

print("Loading speaker embedding model …")
from speechbrain.inference.speaker import EncoderClassifier
speaker_model = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="/tmp/speechbrain_ecapa",
    run_opts={"device": "cpu"},
)
print("Speaker model ready.\n")

import torch

# ── LLM config ───────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.5-flash"
OPENAI_MODEL   = "gpt-4o-mini"

gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"Gemini ready ({GEMINI_MODEL})")
else:
    print("GEMINI_API_KEY not set")

openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"OpenAI ready ({OPENAI_MODEL})")
else:
    print("OPENAI_API_KEY not set")

# ── Audio config ─────────────────────────────────────────────────
SAMPLE_RATE       = 16000
RMS_THRESHOLD     = 400
SILENCE_FRAMES    = 14       # ~900ms silence to cut a segment — avoids splitting mid-sentence pauses
MIN_SPEECH_FRAMES = 4

# ── Speaker config ───────────────────────────────────────────────
SPEAKER_NAMES  = ["Speaker A", "Speaker B"]
SPEAKER_COLORS = ["#34d399", "#60a5fa"]
MAX_EMBED_BANK = 10
MIN_EMBED_LEN  = 8000

RF_TYPE_LABELS = {
    'FOIR_ratio': 'FOIR Breach', 'FOIR_breach': 'FOIR Breach',
    'unsecured_pct_portfolio': 'High Unsecured Exposure',
    'active_loan_count_mismatch': 'Bank/Bureau Mismatch',
    'aggressive_borrowing': 'Aggressive Borrowing',
    'high_loan_velocity': 'High Loan Velocity',
    'recent_delinquency': 'Recent Delinquency',
    'historical_delinquency': 'Historical Delinquency',
    'declining_abb': 'Declining Bank Balance',
    'business_income_stopped': 'Business Income Stopped',
}

def rf_type_label(t):
    return RF_TYPE_LABELS.get(t, t.replace('_', ' ').title())

def get_checklist_items(scenario):
    profile = scenario.get("profile_type", "").lower()
    items = []
    if "salaried" in profile:
        items += [
            {"id": "inc_primary",   "section": "income", "label": "Monthly Salary"},
            {"id": "inc_secondary", "section": "income", "label": "Secondary Income"},
            {"id": "inc_bank",      "section": "income", "label": "Bank Account Details"},
            {"id": "inc_expenses",  "section": "income", "label": "Monthly Expenses"},
        ]
    else:
        items += [
            {"id": "inc_sales",     "section": "income", "label": "Monthly Business Sales"},
            {"id": "inc_upi",       "section": "income", "label": "UPI / Digital Deposits"},
            {"id": "inc_cash",      "section": "income", "label": "Cash Sales"},
            {"id": "inc_margin",    "section": "income", "label": "Gross Profit Margin"},
            {"id": "inc_suppliers", "section": "income", "label": "Supplier Payments"},
        ]
    for i, rf in enumerate(scenario.get("red_flags", [])):
        t = rf.get("type", rf.get("code", f"flag_{i}"))
        items.append({"id": f"rf_{i}", "section": "flags", "label": rf_type_label(t)})
    return items

# ── Copilot system prompt (full underwriting spec) ───────────────
COPILOT_SYSTEM = """You are an expert AI Underwriting Co-Pilot assisting an underwriter during a live conversation with a loan borrower.

ABSOLUTE RULE — READ THIS FIRST AND FOLLOW FOR EVERY RESPONSE:
The "question" field in your JSON output MUST be 8 words or fewer. Count the words. If it is more than 8 words, rewrite it. No exceptions, no matter how complex the topic. Use the "detail" field for the full explanation.

EXAMPLES OF COMPLIANT QUESTIONS (count the words yourself):
- "Why are two EMIs missing from your statement?" — 8 words ✓
- "Do you have loans at another bank?" — 7 words ✓
- "How much cash do you collect monthly?" — 7 words ✓
- "Which suppliers do you pay in cash?" — 7 words ✓

EXAMPLES OF NON-COMPLIANT QUESTIONS (NEVER output these):
- "Can you explain why there is a discrepancy between the number of EMI payments on your bank statement and the actual number of EMI payments you are making?" — 29 words ✗
- "Can you clarify what loan EMIs are currently being reported to the bank but not reflected on your statement?" — 19 words ✗

You observe the live transcript and after each borrower utterance you suggest the NEXT BEST QUESTION the underwriter should ask, following the exact methodology below. You also track all data points explicitly stated in the conversation.

=============================================================
1. BENCHMARK DATA
=============================================================

Table A: Digital/UPI Penetration by Segment (Tier 2/3 Cities)
| Industry Segment       | Min UPI % | Max UPI % |
|------------------------|-----------|-----------|
| Grocery / Kirana       | 20%       | 30%       |
| Medical Store          | 35%       | 50%       |
| Apparel / Fashion      | 40%       | 60%       |
| Hardware / Paints      | 15%       | 25%       |
| Dairy / Milk Dist.     | 5%        | 10%       |

Table B: Industry Benchmark Margins
| Segment         | Margin (Min) | Margin (Max) |
|-----------------|--------------|--------------|
| Grocery / FMCG  | 4%           | 8%           |
| Electronics     | 8%           | 12%          |
| Apparel         | 15%          | 25%          |
| Hardware        | 8%           | 12%          |

Table C: Product Volumetric Database (For Shop Size Validation)
| Product Category | Item Example         | Unit Price (₹) | Unit Volume (Cu. Ft.) |
|------------------|----------------------|----------------|-----------------------|
| Staples (Bulk)   | Rice Sack (25kg)     | 1,200          | 1.2                   |
| Staples (Bulk)   | Atta Bag (10kg)      | 450            | 0.5                   |
| Liquid           | Oil Carton (1L x 12) | 2,100          | 1.0                   |
| Snacks           | Chips Display (Lg)   | 500            | 2.0                   |
| Beverage         | Water (20L Jar)      | 80             | 1.0                   |

=============================================================
2. CONVERSATION SEQUENCE (follow strictly in this order)
=============================================================

Always analyze and interact with borrower in the below order, for each analysis that is applicable as per borrower profile:

1. Sales and Income Assessment
   a. Sales Estimated via UPI Credits
   b. Margin Validation
   c. Sales Estimated via Supplier Payments
   d. Rental/Other Income Detection from Bank Statement
2. Final Validated Income
3. Income Assessment Summary
4. Red Flags: Seek clarifications for each red flag in the borrower profile.
   - Refer to specific data points in the borrower profile analysis
   - Ask for documents from the borrower as per the red flag

=============================================================
3. SALES AND INCOME ASSESSMENT
=============================================================

3.1 Sales Estimated via UPI Credits
- During conversation for UPI credits, refer to UPI Credits as "Digital payment collections (UPI/PhonePe/GPay)"
- Calculate UPI % of Sales = (UPI_Credit / Claimed Sales) * 100
- Compare UPI % of Sales to Table A benchmark for their segment.

IF UPI % of Sales is LESS THAN the minimum benchmark:
  - Inform the borrower of their UPI % and the industry benchmark
  - Probe for cash sales and bank statements of other banks (not already submitted)
  - Example income sources: UPI Sales Bank 1 (10%), UPI Sales Bank 2 (15%), Cash Sales (60%)
  - Ask for required documents: for Cash Sales → supplier bills or GST; for other bank accounts → 6 months bank statement
  - Calculate Sales Estimated via UPI Credits = UPI Credits from borrower profile + UPI Sales from new bank accounts + Cash Sales

IF UPI % of Sales is >= minimum benchmark:
  - Sales Estimated via UPI Credits = Claimed Sales
  - Do NOT inform or ask anything. Simply move to Section 3.2 Margin Validation.

IMPORTANT: Cash sales amount declared here — do NOT ask for cash income again in FOIR section.

3.2 Margin Validation
- Compare Claimed Margin vs Benchmark Max margin (Table B).
- Claimed margin must be within benchmark range (min to max).
- IF claimed margin > max benchmark margin:
  - Ask borrower why margin is higher
  - Notify that bank internal team will assess this
  - For now use the max benchmark margin for income check
- Final margin = minimum of (claimed margin, max benchmark margin)

3.3 Sales Estimated via Supplier Payments
- Sales Estimated via Supplier Payments = Total Supplier Payments × (1 + Final margin)
- Sales gap = (Claimed Sales − Sales Estimated via Supplier Payments) / Claimed Sales

IF Sales gap > 20%:
  - Inform borrower about supplier payments visible in bank statement
  - Apply final margin to show what sales this would support
  - Compare to their claimed sales figure
  - Ask them to explain the gap
  - If borrower struggles, guide with possible reasons:
    a. Cash payments to suppliers not reflected in bank
    b. Other bank accounts used for business
  - ALWAYS ask for cash purchase AMOUNT or purchases through other bank accounts BEFORE asking for documents
  - Ask for documents: for Cash Purchases → supplier bills or GST; for other bank accounts → 6 months bank statement

IF Sales gap <= 20%:
  - No explanation required. Move directly to Section 3.4.

3.4 Rental/Other Income Detection from Bank Statement

Step 1 — Check if other income sources were already mentioned in the conversation:

IF borrower has NOT mentioned any other income source:
  - Ask explicitly if they have other income sources beyond store sales, e.g.:
    * Rental income from property
    * Any other business or B2B income
    * Income from investments
  - For each source mentioned: ask amount per month, ask for relevant proof:
    * Rental income → Rent Agreement
    * B2B income → Invoices, contracts
    * Investment income → Bank statement, investment statements
  - Then proceed to Step 2

IF borrower has already mentioned other income earlier:
  - Check if income amount per month was mentioned; if not, ask
  - Check if proof was requested; if not, ask
  - Then proceed to Step 2

Step 2 — Verify against Top Buyers data:
  - Analyse top buyers data in borrower profile
  - Look for payments that appear consistently (same amount each month from a buyer)
  - IF borrower mentioned other income: check for corresponding credits in top buyers data (match name or amount)
    * If credits not found → ask for proof (Rent Agreement if rental; other relevant proof otherwise)
  - IF borrower did NOT mention other income: check for regular credits from non-supplier sources
    * If found → ask borrower: "I see regular credits of ₹X from [Name]. Is this rental income or some other income?"
    * If rental → ask for Rent Agreement; If other income → ask for relevant proof

IMPORTANT: Record all other income sources here. Do NOT explicitly ask for other income sources again in FOIR section. However, if borrower volunteers new information during FOIR discussion, do collect the amount and ask for documents.

3.5 Final Validated Income

3.5.1 Validated Sales = minimum of:
  - Claimed Sales
  - Sales Estimated via UPI Credits
  - Sales Estimated via Supplier Payments

3.5.2 Validated Business Income = Validated Sales × Final Margin

3.5.3 Other Income = Rental Income + Other B2B Income + Any other verified income

3.5.4 Final Validated Income = Validated Business Income + Other Income

3.6 Income Assessment Summary
Always explain step-by-step how you reached validated sales:
  - Validated Sales
  - Final margin
  - Calculated monthly business income
  - Any other income sources (rental, B2B, etc.) with amounts
  - Total Monthly Income = Business Income + Other Income

Then:
1. Ask for confirmation from the borrower, or if they want to change anything
2. If they want to change, ask for details and re-verify per above sections
3. Re-calculate, explain, and ask for confirmation again
4. If borrower wants to change again, repeat from step 1

This Total Monthly Income confirmed by the borrower is used for FOIR calculation in Section 4.4.

=============================================================
4. RED FLAGS
=============================================================

4.1 Rental/Other Income
- Check monthly_credits. Look for missing entries in recent months.
- If income is not there in recent months (at least 2), exclude rental income from total income
- Ask for explanation for missing income in recent months
- No documents needed

4.2 Unsecured Loans Portfolio%
- Unsecured Loans outstanding as % of total outstanding must be < 70%
- IF unsecured loan % > 70%:
  - We will not give unsecured loan to this borrower
  - Ask why they have such a high portfolio of unsecured loans
  - If borrower applied for unsecured loan, check for collateral to convert to secured loan:
    * Collateral options: property, Fixed Deposit, Mutual Funds, Gold
    * Borrower must not have existing loans on collateral
    * Documents if collateral available:
      - Property → property purchase deed
      - Fixed Deposit → FD slip from bank
      - Mutual Funds → Mutual Funds Statement
      - Gold → Purchase Receipts or borrower must agree to physical bank verification

4.3 Loan Count Mismatch
- Count of active loans from bank statements does not match active loan count from Bureau reports.
- Check with the borrower if they are paying EMIs from other banks. If yes, ask for those bank statements.
- If borrower says they closed a loan, ask for Loan Closure Statement for those loans.

4.4 FOIR Check
- Always output the calculation steps (Numerator/Denominator) when discussing FOIR changes.
- FOIR Ratio = Total Obligations / Total Validated Income (from Section 3.6 — NOT claimed income)
- FOIR must be:
  * < 60% for Salaried borrower
  * < 75% for Self-Employed or Business borrower
- Obligations and income of all applicants and co-applicants must be considered.

4.4.1 Obligations include:
  - New loan EMI (proposed)
  - Existing loan EMIs (personal, car, home, education)
  - Consumer durable EMIs (Bajaj, ZestMoney, LazyPay)
  - Co-borrowed loan EMI (full or proportional)

4.4.2 Methodology — if FOIR is too high:

Question 1: Propose to borrower if they can close one or more loans.
  - Suggest closure of loans where outstanding < 20% of original loan amount
  - IF borrower says they ALREADY closed:
    * Recalculate FOIR: Numerator = (Proposed EMI + Total existing EMI − EMI of closed loan) / Denominator = Monthly income
    * Ask for documents: "Loan Closure Letters", "Bank Statement showing debit"
    * If recalculated FOIR < threshold → proceed to next red flag. Else → Question 2.
  - IF borrower says they WILL close in future:
    * Do NOT assume loan is closed
    * Do NOT recalculate FOIR with this loan removed yet
    * Say: "Okay, let me note that. Let me also check a few other options."
    * Note as POTENTIAL action (not confirmed)
    * Proceed to Question 2
  - IF borrower cannot close → proceed to Question 2

Question 2: Ask if borrower has any other sources of income?
  IMPORTANT: If cash income or other income was already discussed in Section 3.5, do NOT ask again.
  Instead say: "Earlier you mentioned [cash income of ₹X / rental income of ₹Y]. I have already included that. Is there any OTHER source of income we haven't discussed yet?"
  - Only if genuinely NEW income:
    * Ask: source of income, amount per month
    * Recalculate FOIR: Numerator (per Q1 output) / Denominator = Monthly income + additional income
    * Only after getting details, ask for documents: GST Returns, Day Book/Ledger extracts, Supplier Bills, Rent Agreement (as applicable — only if not already requested)
    * If recalculated FOIR < threshold → next red flag. Else → Question 3.

Question 3: If FOIR still high, ask if a co-applicant can be added.
  - If yes: ask for co-applicant details (relationship, income, current EMIs)
  - Recalculate FOIR: Numerator (per Q1 output + co-borrower total EMI) / Denominator (per Q2 output + co-borrower income)
  - After co-applicant details and FOIR recalculation, ask for co-applicant documents:
    * PAN Card, Last 2 Years ITR / Salary Slips, Last 6 Months Bank Statement
  - If recalculated FOIR < threshold → next red flag. Else → Question 4.

Question 4: If FOIR still high, calculate EMI of new loan with which FOIR will be within permissible limits.
  - Ask borrower if they are comfortable with a reduced loan amount.
  - Assume interest rate 18%, tenor 36 months.

After all 4 questions, if borrower said they can consider closing a loan in Q1:
  - Calculate two scenarios:
    Scenario A (FOIR within limits WITHOUT loan closure): Tell borrower closing the loan is not necessary.
    Scenario B (FOIR still requires loan closure): Give borrower clear choice:
      "If you close [Loan Name] (₹Y outstanding): Eligibility = ₹X"
      "Without closing: Eligibility = ₹Z"
  - Summarize: loans to close (if any) + documents required, additional income considered, co-applicant details, reduced loan amount (if applicable)
  - Show step-by-step FOIR calculation after each question.

4.5 Aggressive Borrowing (Multiple Recent Loans)
- Borrower has taken >= 4 loans within last 6 months.
- State exact observation: "You have taken 4 new loans totaling ₹5.5 Lakhs in the last 6 months"
- Ask for End Use of Funds. Possible responses:
  * Medical emergency → ask for hospital bills, medical receipts
  * Home renovation → ask for contractor invoices, material bills
  * Business stock/expansion → ask for supplier invoices, stock purchase proof (only if supplier bills NOT already requested)
  * One-time life event (wedding, education) → ask for relevant invoices
  * Paying off other debts → ask which loans were closed, request Loan Closure Letters
  * Vague/unclear → probe further

4.6 Recent Delinquency (DPD in Last 6 Months)
- Borrower has one or more loan accounts that went past due (DPD > 0) within last 6 months.
- DPD = Days Past Due. Even if "Cured" (brought current), it signals repayment stress.
- State exact observation: "We noticed a delay of 18 days in your Bajaj Finance Personal Loan payment in August." Note status: "I see this is now cleared" or "I see you are still due."
- Ask for reason. Classify as:
  * Lower Risk (Technical): Bank server issue, auto-debit failure, account change, forgot to maintain balance
  * Higher Risk (Cash Flow): Salary delay, unexpected expense, had to prioritize other payments, didn't have funds
- Documentation:
  * Technical → ask for bank statement showing failed debit or payment made immediately after
  * Cash Flow → no documentation required

4.7 Declining Average Bank Balance
- Borrower's ABB has shown consistent decline over ~6 months.
- State exact numbers: "Your average bank balance has dropped from ₹65,000 to ₹40,000 — a 38% decline over 6 months."
- Ask for explanation. Possible responses and follow-up:
  * Medical emergency → hospital bills, check if correlates with loan timing
  * One-time life event → ask what expense, request proof (bills/invoices)
  * Business investment → request proof (bills/invoices)
  * Property purchase → Purchase agreement or purchase deed
  * Repay loans → ask for loan closure documents
  * Daily expenses increasing → no documents needed
  * No specific reason → no documents needed

4.8 Business Income Stopped
- Borrower's business has shown zero or near-zero income for 2+ consecutive months.
- State exact observation: "Your business income dropped to zero in August and September." Highlight decline pattern: "I also see income declining from ₹1.45 lakhs in April to ₹45,000 in July before stopping completely."
- Ask directly: "Is your business currently operational?"
- Possible responses:
  * Yes, operational (e.g. shifted to cash) → ask for supplier payments, bills, or e-way bills
  * Temporarily closed (renovation, health issues, seasonal, disruption, lost client, competition) → ask for reason and restart timeline
  * Permanently closed → do not consider business income

=============================================================
5. DOCUMENT HANDLING RULES
=============================================================

5.1 Documents not handy
- If borrower says they don't have a document ready or will submit later:
  * Do NOT stop or keep asking for it
  * Say: "No problem, you can submit that later. Let me continue with a few more questions."
  * Note as pending. At end of call, provide a complete list of pending documents and pending actions.

5.2 Avoid Duplicate Document Requests
- Maintain a mental list of documents already requested. Do NOT ask for the same document twice.

5.3 Avoid Duplicate Information Requests
- Do NOT ask for same information twice:
  * Cash income discussed in 3.1 or 3.5 → do NOT ask again in 4.4
  * Rental income discussed in 3.4 or 3.5 → do NOT ask again in 4.4
  * Co-applicant details already collected → do NOT ask again
- Instead reference what was discussed: "Earlier you mentioned cash sales of ₹X — I've included that."

=============================================================
6. EMI CALCULATION FORMULA
=============================================================

EMI = (P × R × (1+R)^N) / ((1+R)^N − 1)

Where:
  P = Principal loan amount
  R = Monthly interest rate = Annual rate / 12 / 100
  N = Loan tenure in months

Example: P=₹5,00,000, Annual rate=12%, N=36 months
  R = 12/12/100 = 0.01
  EMI = (500000 × 0.01 × (1.01)^36) / ((1.01)^36 − 1)

=============================================================
OUTPUT FORMAT — respond with valid JSON only, no markdown fences
=============================================================

{
  "trigger": "discrepancy|gap|none",
  "question": "Short plain question — MAX 8 WORDS, everyday English only",
  "detail": "One or two sentences with full context: why this matters, what benchmark applies, what to watch for",
  "reason": "One sentence explaining why this question matters for underwriting",
  "stage": "Current stage name (e.g. 'UPI Sales Assessment', 'Margin Validation', 'Supplier Payment Gap', 'Other Income Detection', 'Income Summary', 'FOIR Check Q1', 'Aggressive Borrowing', 'Delinquency', 'Declining ABB', 'Business Income Stopped')",
  "data_points": [
    {"label": "Short label", "value": "Simple plain string only", "status": "confirmed|claimed|pending|flagged"}
  ],
  "checklist_updates": [
    {"id": "<item_id_from_checklist>", "status": "verified|discussed|warning"}
  ]
}

RULES FOR trigger — read carefully:
- "discrepancy": Set this when the borrower states something that contradicts their pre-application data (e.g. claims a different income, mentions an undisclosed loan, states a different EMI amount than the bureau shows). This is a concrete factual contradiction.
- "gap": Set this when 6+ conversation turns have passed AND important checklist items are still pending AND the conversation appears to be wrapping up/concluding.
- "suggestion": Set this when the borrower has just answered something AND there is a clear, logical NEXT question to ask per the underwriting sequence (Sections 3 and 4). Use this for the normal flow of the conversation — after UPI discussion, after margin discussion, when entering a new section, when a calculation should be shared, etc. This is the most common trigger.
- "none": ONLY use this when the borrower's answer was incomplete/unclear and you are waiting for more info, OR the underwriter already asked the right follow-up, OR there is genuinely nothing new to assess. Use sparingly.

When trigger is "none": still fill question/detail/reason (in case they're needed), but the UI will NOT show an inline suggestion card.

RULES FOR checklist_updates:
- Update items based on what was discussed this turn
- "verified": item was confirmed and matches expected data
- "discussed": item came up but not fully confirmed yet
- "warning": item was discussed but shows a problem or mismatch
- Only include items that changed status this turn — omit items with no change
- Use the exact IDs from the checklist provided in the prompt

CRITICAL RULES FOR "question":
- MAXIMUM 8 WORDS — count every word, stay within the limit
- Use simple everyday English — no jargon, no acronyms (write "monthly bank deposits" not "ABB", "loan repayment burden" not "FOIR", "profit margin" not "gross margin %" etc.)
- It should sound like a natural thing a person would ask in a conversation
- BAD: "Can you clarify what loan EMIs are currently being reported to the bank but not reflected on your statement?" (18 words, jargon)
- BAD: "What is the UPI percentage of your total sales?" (too technical)
- GOOD: "Do you pay any EMIs from another bank?" (8 words, plain)
- GOOD: "How much cash do you collect each month?" (8 words, plain)
- GOOD: "Which bank account gets most of your payments?" (8 words, plain)

CRITICAL RULES FOR data_points:
- ONLY include facts/numbers explicitly stated or confirmed DURING THE CONVERSATION — never from the borrower background context
- Every "value" must be a SHORT PLAIN STRING (e.g. "₹24,90,000/month", "15.4% — below 20% benchmark", "Pending — supplier bills", "Not yet discussed")
- NEVER put arrays, objects, or nested JSON into any "value" field
- NEVER copy borrower profile fields directly into data_points
- Only include data points that have actually come up in the conversation so far
- Good examples:
  {"label": "Claimed Monthly Sales", "value": "₹24,90,000", "status": "claimed"}
  {"label": "UPI % of Sales", "value": "15.4% (below 20% benchmark)", "status": "flagged"}
  {"label": "Cash Sales Declared", "value": "₹5,00,000/month", "status": "confirmed"}
  {"label": "Gross Margin (Claimed)", "value": "12% — above 8% max benchmark", "status": "flagged"}
  {"label": "Validated Sales", "value": "₹19,00,000 (min of 3 estimates)", "status": "confirmed"}
  {"label": "FOIR (Current)", "value": "88.1% — exceeds 75% limit", "status": "flagged"}
  {"label": "Supplier Bills", "value": "Pending submission", "status": "pending"}
  {"label": "Loan Closure Q1", "value": "LendingKart BL — borrower will close", "status": "pending"}

MANDATORY PRE-OUTPUT CHECK — do this BEFORE writing JSON:

STEP 1 — CHECK IF YOUR SPECIFIC QUESTION WAS ALREADY ASKED AND ANSWERED:
Look at the transcript. Ask yourself: "Has the Underwriter already asked THIS SPECIFIC question AND did the Borrower give a direct answer?"
- If YES to BOTH → do NOT suggest it again. Pick the next logical question in the sequence instead.
- If the Underwriter asked but Borrower gave a vague/incomplete answer → you MAY suggest a follow-up on the same point.
- If the Underwriter asked about a broad topic (e.g. loans) but a specific sub-question is still unanswered (e.g. exact EMI amount) → suggest the specific sub-question.

STEP 2 — ALWAYS SUGGEST SOMETHING UNLESS EVERYTHING IS GENUINELY DONE:
There are many topics in the underwriting sequence (UPI sales, margin, supplier payments, other income, FOIR, red flags). Unless the transcript shows ALL relevant topics have been covered, there is always a next question to ask. Default to trigger="suggestion" for the next uncovered item.

STEP 3 — ONLY SET trigger="none" IF:
- The Underwriter JUST asked the exact right follow-up question in their last turn, OR
- The conversation just started and the Borrower hasn't said anything substantive yet

EXAMPLES:
- UW asked "Which bank pays your EMIs?" + Borrower said "husband's account" → that specific Q is done. Move to next topic (e.g. confirm EMI amount, or move to income section).
- UW asked about cash sales + Borrower gave a number → move to margin or supplier payments next.
- Borrower just answered something → there is almost always a next question. Use trigger="suggestion".

FINAL OUTPUT CHECKS:
1. Count the words in "question". If more than 8 — rewrite it shorter.
2. Put all explanation in "detail", not in "question".
3. "question" must sound like something a person says in normal conversation — short, plain, no jargon.
4. Did you pick a question that was ALREADY specifically asked AND answered? If yes — pick the next topic instead."""

CHAT_SYSTEM = """You are an expert AI Underwriting Assistant helping an underwriter understand a live loan case.

You have deep knowledge of underwriting methodology: income assessment, FOIR calculation, UPI penetration benchmarks, red flags, EMI obligations, supplier payments, and document requirements.

RESPONSE RULES — follow these for every reply:
- Write in plain, simple English. No jargon unless you immediately explain it.
- Keep answers SHORT and scannable — use bullet points wherever possible.
- Never return JSON. Always return readable text.
- If asked about a number or metric, lead with the answer, then explain briefly.
- Use ₹ for amounts. Round numbers to 2 decimal places max.
- If something hasn't been confirmed in the conversation yet, say so clearly.

FORMAT:
- One-line direct answer first (bold if markdown is supported)
- Then 2–4 bullet points with supporting detail if needed
- Keep total response under 100 words unless the question genuinely needs more

EXAMPLE — Q: "What is FOIR?"
A: FOIR is the share of monthly income going toward loan repayments.
• Full form: Fixed Obligation to Income Ratio
• Formula: Total monthly EMIs ÷ Monthly income × 100
• Our limit: 60% for salaried, 65% for self-employed
• Above the limit = loan is too risky to approve as-is

EXAMPLE — Q: "How much is FOIR for this borrower?"
A: FOIR is 65.29% — above the 60% limit for salaried borrowers.
• Monthly income: ₹85,000
• Existing EMIs: ₹44,500
• Proposed new EMI: ₹11,000
• Total obligations: ₹55,500 (₹55,500 ÷ ₹85,000 = 65.29%)
"""

app = FastAPI()


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/scenarios")
async def list_scenarios():
    return JSONResponse([{
        "case_id": s["case_id"],
        "customer_name": s["customer_name"],
        "profile_type": s["profile_type"],
        "loan_type": s["loan_type"],
        "loan_amount": s["loan_amount"],
        "segment": s["segment"],
        "red_flag_count": len(s.get("red_flags", [])),
        "red_flags": s.get("red_flags", []),
        "avg_monthly_credit": s["banking"]["avg_monthly_credit"],
        "avg_upi_credit": s["banking"]["avg_upi_credit"],
        "claimed_sales": s.get("claimed_monthly_sales") or s.get("claimed_income", "—"),
        "claimed_sales_label": "Claimed Monthly Sales" if "claimed_monthly_sales" in s else "Claimed Income",
        "top_suppliers": s.get("top_suppliers", []),
        "top_buyers": s.get("top_buyers", []),
        "summary": get_summary(s),
        "checklist": get_checklist_items(s),
    } for s in SCENARIOS])


@app.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        question = body.get("question", "")
        context  = body.get("context", "")
        case_id   = body.get("case_id", "")
        history   = body.get("history", [])
        provider  = body.get("provider", "gemini")

        scenario = next((s for s in SCENARIOS if s["case_id"] == case_id), None)
        scenario_summary = get_summary(scenario) if scenario else ""
        print(f"[Chat] case_id='{case_id}' → borrower='{scenario['customer_name'] if scenario else 'NOT FOUND'}'")

        system = CHAT_SYSTEM

        history_text = ""
        if history:
            lines = []
            for turn in history:
                role    = turn.get("role", "user")
                content = turn.get("content", "")
                label   = "Q" if role == "user" else "A"
                lines.append(f"{label}: {content}")
            history_text = "\n".join(lines)

        user_prompt_parts = []
        if scenario_summary:
            user_prompt_parts.append(f"## Scenario Summary\n{scenario_summary}")
        if context:
            user_prompt_parts.append(f"## Copilot Insight\n{context}")
        if history_text:
            user_prompt_parts.append(f"## Previous Q&A\n{history_text}")
        user_prompt_parts.append(f"## Current Question\n{question}")

        user_prompt = "\n\n".join(user_prompt_parts)

        loop = asyncio.get_event_loop()
        raw, model = await loop.run_in_executor(None, call_llm, system, user_prompt, provider)

        return JSONResponse({"answer": raw, "model": model})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Embedding helpers ─────────────────────────────────────────────

def get_embedding(pcm_f32: np.ndarray) -> np.ndarray:
    waveform = torch.tensor(pcm_f32, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        emb = speaker_model.encode_batch(waveform)
    return emb.squeeze().numpy()

def cosine_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def bank_sim(embedding, bank):
    if not bank: return -1.0
    return max(cosine_sim(embedding, e) for e in bank)

def add_to_bank(bank, embedding):
    bank.append(embedding.copy())
    if len(bank) > MAX_EMBED_BANK: bank.pop(0)


# ── STT ───────────────────────────────────────────────────────────

def transcribe(pcm_bytes):
    pcm = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    segs, _ = stt.transcribe(pcm, language="en", vad_filter=True)
    return " ".join(s.text for s in segs).strip()


# ── LLM ──────────────────────────────────────────────────────────

def _build_user_prompt(scenario_summary, transcript_lines, checklist_items=None):
    checklist_section = ""
    if checklist_items:
        lines = ["## Checklist Items (update status in checklist_updates field)"]
        income = [it for it in checklist_items if it["section"] == "income"]
        flags  = [it for it in checklist_items if it["section"] == "flags"]
        if income:
            lines.append("Income Assessment:")
            lines += [f"  {it['id']}: {it['label']}" for it in income]
        if flags:
            lines.append("Red Flags:")
            lines += [f"  {it['id']}: {it['label']}" for it in flags]
        checklist_section = "\n".join(lines) + "\n\n"

    already_asked = "\n".join(
        line for line in transcript_lines if line.startswith("Underwriter:")
    )
    return (
        f"## Borrower Background (for context only — do NOT echo this into data_points)\n{scenario_summary}\n\n"
        f"{checklist_section}"
        f"## Conversation Transcript (FULL — read every line before deciding what to suggest)\n{chr(10).join(transcript_lines)}\n\n"
        f"## Questions Already Asked by Underwriter\n{already_asked or '(none yet)'}\n\n"
        "IMPORTANT: Check the 'Questions Already Asked' section. Do NOT suggest a question that was already specifically asked AND answered. "
        "If that specific question is done, move to the NEXT topic in the underwriting sequence — there is almost always something more to cover. "
        "Do NOT include any values from the borrower background in data_points. "
        "Respond with JSON only."
    )

def call_llm(system, user_prompt, provider="gemini"):
    """Call Gemini or OpenAI depending on provider."""
    if provider == "openai" and openai_client:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        print(f"  [LLM] {OPENAI_MODEL}")
        return resp.choices[0].message.content.strip(), "openai"
    elif gemini_client:
        resp = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.3,
                max_output_tokens=1000,
            ),
        )
        print(f"  [LLM] {GEMINI_MODEL}")
        return resp.text.strip(), "gemini"
    else:
        raise RuntimeError("No LLM client available — set GEMINI_API_KEY or OPENAI_API_KEY")


def parse_copilot_response(raw):
    """Parse copilot JSON response, with fallback for non-JSON."""
    text = raw.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)

        # Sanitize data_points: value must always be a plain string
        raw_dps = data.get("data_points", [])
        clean_dps = []
        for dp in raw_dps:
            if not isinstance(dp, dict):
                continue
            label = str(dp.get("label", "")).strip()
            val   = dp.get("value", "")
            status = str(dp.get("status", "confirmed")).strip().lower()

            # Flatten any non-string value to a readable string
            if isinstance(val, (dict, list)):
                continue   # skip — it's raw profile data leaking through, not conversation info
            val = str(val).strip()

            if label and val:
                clean_dps.append({"label": label, "value": val, "status": status})

        return {
            "trigger":           str(data.get("trigger", "none")).strip().lower(),
            "question":          str(data.get("question", "")).strip(),
            "detail":            str(data.get("detail",   "")).strip(),
            "reason":            str(data.get("reason",   "")).strip(),
            "stage":             str(data.get("stage",    "")).strip(),
            "data_points":       clean_dps,
            "checklist_updates": [
                {"id": str(u.get("id","")), "status": str(u.get("status","discussed"))}
                for u in data.get("checklist_updates", [])
                if isinstance(u, dict) and u.get("id")
            ],
        }
    except json.JSONDecodeError:
        # Non-JSON response — show as plain question
        return {
            "trigger":           "none",
            "question":          raw.strip(),
            "detail":            "",
            "reason":            "",
            "stage":             "",
            "data_points":       [],
            "checklist_updates": [],
        }


# ── WebSocket handler ─────────────────────────────────────────────

@app.websocket("/ws")
async def meeting_ws(ws: WebSocket):
    await ws.accept()
    await ws.send_text(json.dumps({"type": "state", "value": "ready"}))

    loop = asyncio.get_running_loop()

    # VAD state
    speech_buf    = bytearray()
    silence_cnt   = 0
    speech_cnt    = 0
    in_speech     = False
    recording     = False

    # Speaker state
    banks = [[], []]
    last_speaker      = -1
    last_text         = ""
    both_seen         = False
    last_segment_time = 0.0   # epoch time when last segment was processed

    # Scenario + transcript
    active_scenario  = None
    scenario_summary = ""
    full_transcript  = []
    checklist_items  = []
    llm_provider    = "gemini"

    def assign_speaker(embedding, text):
        nonlocal last_speaker, both_seen, last_segment_time

        is_question   = text.rstrip().endswith("?")
        now           = time.time()
        gap           = now - last_segment_time          # seconds since last segment
        is_same_turn  = gap < 2.0 and last_speaker != -1  # likely same speaker continuing

        if last_speaker == -1:
            # First utterance ever — Underwriter almost always speaks first
            idx = 0
            add_to_bank(banks[idx], embedding)
            last_speaker      = idx
            last_segment_time = now
            return idx

        if not both_seen:
            if is_same_turn:
                # Same speaker continuing mid-sentence — don't switch yet
                add_to_bank(banks[last_speaker], embedding)
                last_segment_time = now
                return last_speaker
            # New person joined — assign opposite role
            idx = 1 - last_speaker
            add_to_bank(banks[idx], embedding)
            last_speaker      = idx
            both_seen         = True
            last_segment_time = now
            return idx

        # Both voices seen — voice similarity is primary signal
        sim_uw = bank_sim(embedding, banks[0])
        sim_bw = bank_sim(embedding, banks[1])
        diff   = abs(sim_uw - sim_bw)
        print(f"  [SPK] sim_UW={sim_uw:.3f}  sim_BW={sim_bw:.3f}  diff={diff:.3f}  gap={gap:.1f}s  Q={is_question}")

        if is_same_turn and diff < 0.12:
            # Recent continuation with ambiguous voice — keep same speaker
            chosen = last_speaker
        elif diff > 0.05:
            # Clear voice match — trust it
            chosen = 0 if sim_uw > sim_bw else 1
        elif is_question:
            # Ambiguous voice + question → Underwriter
            chosen = 0
        else:
            # Ambiguous voice + statement → Borrower
            chosen = 1

        add_to_bank(banks[chosen], embedding)
        last_speaker      = chosen
        last_segment_time = now
        return chosen

    async def process_segment(audio_bytes):
        nonlocal last_text

        t0 = time.perf_counter()

        # Run STT and speaker embedding in parallel (they're independent)
        pcm_f32 = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if len(pcm_f32) >= MIN_EMBED_LEN:
            text, embedding = await asyncio.gather(
                loop.run_in_executor(None, transcribe, audio_bytes),
                loop.run_in_executor(None, get_embedding, pcm_f32),
            )
        else:
            text = await loop.run_in_executor(None, transcribe, audio_bytes)
            embedding = None

        if not text:
            return
        t_stt = time.perf_counter()

        if embedding is not None:
            speaker_idx = assign_speaker(embedding, text)
        else:
            # No embedding (audio too short) — use question detection as fallback
            speaker_idx = 0 if text.rstrip().endswith("?") else 1
            last_speaker = speaker_idx

        last_text = text
        t_spk = time.perf_counter()

        role = "Underwriter" if speaker_idx == 0 else "Borrower"
        color = SPEAKER_COLORS[speaker_idx]
        print(f"[{role}] {text}  (STT {t_stt-t0:.2f}s  SPK {t_spk-t_stt:.2f}s)")

        await ws.send_text(json.dumps({
            "type":        "transcript",
            "speaker":     role,
            "color":       color,
            "text":        text,
            "speaker_idx": speaker_idx,
        }))

        full_transcript.append(f"{role}: {text}")

        # Trigger copilot after Borrower (idx=1) speaks
        if speaker_idx == 1 and active_scenario and len(full_transcript) >= 2:
            # Instant "thinking" ping so UI shows a placeholder card immediately
            await ws.send_text(json.dumps({"type": "copilot_thinking"}))
            asyncio.create_task(generate_copilot_suggestion())

    async def generate_copilot_suggestion():
        user_prompt = _build_user_prompt(scenario_summary, full_transcript, checklist_items)
        try:
            raw, model = await loop.run_in_executor(None, call_llm, COPILOT_SYSTEM, user_prompt, llm_provider)
            parsed = parse_copilot_response(raw)
            print(f"[Copilot/{model}] trigger={parsed['trigger']} {parsed['question']}")

            await ws.send_text(json.dumps({
                "type":              "copilot",
                "trigger":           parsed.get("trigger", "none"),
                "question":          parsed["question"],
                "detail":            parsed.get("detail", ""),
                "reason":            parsed["reason"],
                "stage":             parsed["stage"],
                "data_points":       parsed["data_points"],
                "checklist_updates": parsed.get("checklist_updates", []),
                "model":             model,
            }))
        except Exception as e:
            print(f"[Copilot error] {e}")

    # ── Main receive loop ─────────────────────────────────────────

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break

            if msg.get("text"):
                try:
                    data = json.loads(msg["text"])
                except Exception:
                    continue

                if data.get("type") == "set_provider":
                    llm_provider = data.get("provider", "gemini")
                    print(f"[Provider] switched to {llm_provider}")
                    continue

                if data.get("type") == "select_scenario":
                    case_id = data.get("case_id")
                    active_scenario = next((s for s in SCENARIOS if s["case_id"] == case_id), None)
                    if active_scenario:
                        scenario_summary = get_summary(active_scenario)
                        checklist_items  = get_checklist_items(active_scenario)
                        # Reset ALL session state so previous scenario's data doesn't bleed in
                        full_transcript.clear()
                        speech_buf.clear()
                        banks[0].clear(); banks[1].clear()
                        last_speaker      = -1
                        last_text         = ""
                        both_seen         = False
                        last_segment_time = 0.0
                        silence_cnt  = speech_cnt = 0
                        in_speech    = False
                        await ws.send_text(json.dumps({
                            "type":      "scenario_loaded",
                            "case_id":   case_id,
                            "name":      active_scenario["customer_name"],
                            "summary":   scenario_summary,
                            "checklist": checklist_items,
                        }))
                        print(f"\n[Scenario selected] {active_scenario['customer_name']} ({case_id})")

                elif data.get("type") == "start":
                    recording = True
                    speech_buf.clear()
                    silence_cnt = speech_cnt = 0
                    in_speech = False
                    banks[0].clear(); banks[1].clear()
                    last_speaker      = -1
                    last_text         = ""
                    both_seen         = False
                    last_segment_time = 0.0
                    full_transcript.clear()
                    await ws.send_text(json.dumps({"type": "state", "value": "recording"}))
                    print("[Recording started]")

                elif data.get("type") == "stop":
                    recording = False
                    if in_speech and speech_cnt >= MIN_SPEECH_FRAMES:
                        asyncio.create_task(process_segment(bytes(speech_buf)))
                    speech_buf.clear()
                    silence_cnt = speech_cnt = 0
                    in_speech = False
                    await ws.send_text(json.dumps({"type": "state", "value": "stopped"}))
                    print("[Recording stopped]")

                continue

            raw = msg.get("bytes")
            if not raw or not recording:
                continue

            samples = np.frombuffer(raw, dtype=np.int16)
            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))

            if rms > RMS_THRESHOLD:
                speech_buf.extend(raw)
                speech_cnt  += 1
                silence_cnt  = 0
                in_speech    = True
            elif in_speech:
                speech_buf.extend(raw)
                silence_cnt += 1
                if silence_cnt >= SILENCE_FRAMES:
                    if speech_cnt >= MIN_SPEECH_FRAMES:
                        asyncio.create_task(process_segment(bytes(speech_buf)))
                    speech_buf.clear()
                    speech_cnt = silence_cnt = 0
                    in_speech  = False

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ws error] {e}")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    print("Open http://localhost:8001 in your browser")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
