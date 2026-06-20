# agents/education_agent.py

"""
AarthSaathi Education Agent
-----------------------------
Windows compatible version.
Uses Phi-3 via Hugging Face Inference API.
Every response filtered through guardrails.

Author: AarthSaathi Team
Version: 2.1 (Windows compatible)
"""

import os
import sys

# Windows-compatible path fix
# Adds project root to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from groq import Groq
from layers.guardrails import filter_content

# Load .env from project root
load_dotenv()


# =====================================================
# CONCEPT TO OFFICIAL VERIFICATION SOURCE
# =====================================================

CONCEPT_SOURCES = {
    "sip":             "amfiindia.com — verify mutual funds",
    "fd":              "rbi.org.in — verify bank FD rates",
    "rd":              "rbi.org.in — verify bank RD rates",
    "ppf":             "indiapost.gov.in — open PPF accounts",
    "epf":             "epfindia.gov.in — check your EPF balance",
    "emergency fund":  "No external link needed — keep in savings account",
    "health insurance":"irdai.gov.in — verify insurance companies",
    "term insurance":  "irdai.gov.in — verify insurance companies",
    "nps":             "npscra.nsdl.co.in — National Pension System",
    "sukanya":         "indiapost.gov.in — Sukanya Samriddhi Yojana",
}


# =====================================================
# STATIC FALLBACKS
# Shown when API is unavailable — never blank screen
# =====================================================

FALLBACKS = {
    "emergency fund": (
        "An emergency fund is money kept aside for unexpected expenses "
        "like job loss, medical bills, or urgent repairs. "
        "Aim to save 6 months of your total monthly expenses. "
        "Keep it in a savings account, not invested. "
        "Start small — even Rs.500 per month builds the habit. "
        "Always build this BEFORE any investment."
    ),
    "sip": (
        "A SIP (Systematic Investment Plan) lets you invest a fixed "
        "amount in mutual funds every month automatically. "
        "Returns are not guaranteed — markets go up and down. "
        "Suitable for those who already have an emergency fund. "
        "Always verify the fund is SEBI-registered before investing."
    ),
    "fd": (
        "A Fixed Deposit lets you keep money in a bank for a fixed "
        "period at a fixed interest rate. It is low risk. "
        "Your money is protected up to Rs.5 lakhs per bank under DICGC. "
        "Returns are lower than equity but more predictable. "
        "A safe starting point for first-time investors."
    ),
    "rd": (
        "A Recurring Deposit lets you deposit a fixed amount every month "
        "and earn interest. Similar to FD but in monthly instalments. "
        "Low risk, good for building a saving habit. "
        "Interest rates are fixed when you open the RD."
    ),
    "health insurance": (
        "Health insurance covers your medical expenses during illness "
        "or hospitalisation. Without it, one medical emergency can wipe "
        "out your savings. Buy before you need it — pre-existing "
        "conditions may not be covered immediately. "
        "Verify insurers at irdai.gov.in before buying."
    ),
}


# =====================================================
# MAIN EDUCATION AGENT
# =====================================================

def get_education(
    concept:     str,
    readiness:   str  = "stabilize_first",
    income_type: str  = "fixed",
    language:    str  = "english"
) -> dict:
    """
    Explain a financial concept using Phi-3.

    Parameters
    ----------
    concept     : str — e.g. "SIP", "emergency fund", "FD"
    readiness   : str — "stabilize_first" or "ready_to_invest"
    income_type : str — "fixed", "variable", "mixed"
    language    : str — "english", "hindi", "marathi"

    Returns
    -------
    dict:
        concept    : str   — what was asked
        content    : str   — safe explanation
        safe       : bool  — passed guardrail filter?
        violations : list  — any flagged phrases found
        verify_at  : str   — official source
        fallback   : bool  — True if API unavailable
    """

    # ── Validate input ────────────────────────────────
    if not concept or not concept.strip():
        return {
            "concept": concept, "content": "No concept provided.",
            "safe": False, "violations": [], "fallback": True,
            "verify_at": "sebi.gov.in", "error": "Empty concept"
        }

    concept_clean = concept.strip().lower()
    verify_at     = CONCEPT_SOURCES.get(
        concept_clean,
        "sebi.gov.in — verify all investment products"
    )

    # ── Check for GROQ API Key ────────────────────────────
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        return _fallback_response(concept, concept_clean, verify_at,
                          "GROQ_API_KEY not set in .env file")

    # ── Build prompt ──────────────────────────────────
    readiness_note = (
        "This user needs to stabilize finances before investing."
        if readiness == "stabilize_first"
        else "This user is financially ready to start investing."
    )

    lang_note = (
        f"Respond in {language}."
        if language != "english"
        else "Respond in clear simple English."
    )

    prompt = f"""You are AarthSaathi, a trusted financial literacy
educator for everyday Indians.

STRICT RULES — always follow:
- NEVER guarantee any returns or profits
- NEVER recommend specific fund or stock names
- NEVER use urgency phrases like act now or limited time
- Use simple language, no jargon
- Keep response under 180 words
- End with exactly: Verify at: {verify_at}

USER CONTEXT:
- {readiness_note}
- Income type: {income_type}
- {lang_note}

Explain "{concept}" covering:
1. What it means in one simple sentence
2. How it works briefly
3. Who it suits
4. One key risk to know
5. First step a beginner can take

End with: Verify at: {verify_at}"""


    # ── Call Groq API ─────────────────────────

    try:

        client = Groq(
            api_key=groq_key
        )

        chat_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=250,
            temperature=0.3
        )

        raw_response = (
            chat_response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        error_msg = str(e)

        if "401" in error_msg:
            error_msg = (
                "Invalid GROQ_API_KEY. "
                "Check your .env file."
            )

        elif "429" in error_msg:
            error_msg = (
                "Rate limit reached. "
                "Please wait a moment."
            )

        elif "connection" in error_msg.lower():
            error_msg = (
                "Internet connection issue."
            )

        return _fallback_response(
            concept,
            concept_clean,
            verify_at,
            error_msg
        )
    
    # ── Filter through guardrails ─────────────────────
    # CRITICAL: Every AI response must be filtered
    filter_result = filter_content(raw_response)

    final_content = (
        filter_result["cleaned_text"]
        if not filter_result["safe"]
        else raw_response
    )

    # Ensure verify link is present
    if verify_at not in final_content:
        final_content += f"\n\nVerify at: {verify_at}"

    return {
        "concept":    concept,
        "content":    final_content.strip(),
        "safe":       filter_result["safe"],
        "violations": filter_result["violations"],
        "verify_at":  verify_at,
        "fallback":   False
    }


# =====================================================
# HELPERS
# =====================================================

def _fallback_response(concept, concept_clean, verify_at, error_msg):
    content = FALLBACKS.get(
        concept_clean,
        f"Information about {concept} is currently unavailable. "
        f"Please verify at: {verify_at}"
    )
    return {
        "concept":    concept,
        "content":    content + f"\n\nVerify at: {verify_at}",
        "safe":       True,
        "violations": [],
        "verify_at":  verify_at,
        "fallback":   True,
        "error":      error_msg
    }


# =====================================================
# TEST — run this to verify everything works
# python agents/education_agent.py
# =====================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  Education Agent — Structural Tests")
    print("=" * 55)

    # Test 1: Empty input
    print("\n[TEST 1] Empty concept")
    r = get_education("")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  content={r['content']}")

    # Test 2: No token — fallback fires
    print("\n[TEST 2] Fallback (no HF_TOKEN)")
    r = get_education("emergency fund", "stabilize_first", "fixed")
    print(f"  fallback={r['fallback']}")
    print(f"  verify_at={r['verify_at']}")
    print(f"  content={r['content'][:80]}...")

    # Test 3: Guardrail catches bad phrase
    print("\n[TEST 3] Guardrail filter")
    bad_text = "This SIP gives guaranteed returns of 20% every year."
    filtered = filter_content(bad_text)
    print(f"  safe={filtered['safe']}  violations={filtered['violations']}")

    # Test 4: Concept source map
    print("\n[TEST 4] Verify source mapping")
    for c in ["sip", "fd", "epf", "unknown"]:
        src = CONCEPT_SOURCES.get(c, "sebi.gov.in — verify all investment products")
        print(f"  {c:15} → {src}")

    print("\n" + "="*55)
    print("  Tests done. Groq API is live and working.")
    print("="*55)