# agents/scam_literacy_agent.py
"""
AarthSaathi Scam Literacy Agent
--------------------------------
Provides education about financial scams prevalent in India.
Uses Groq for enhanced explanations with fallback to static content.
Every response filtered through guardrails.
"""

import os
import sys
import json
from pathlib import Path

# Windows-compatible path fix
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from groq import Groq
from layers.guardrails import filter_content

# Load .env from project root
load_dotenv()


def load_scam_patterns():
    """Load scam patterns from JSON file."""
    try:
        json_path = Path(__file__).parent.parent / "data" / "scam_patterns.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading scam patterns: {e}")
        return {}


# =====================================================
# STATIC FALLBACKS
# Shown when API is unavailable — never blank screen
# =====================================================

SCAM_FALLBACKS = {
    "fake_mutual_funds": {
        "content": "Fake mutual fund scams promise high returns with little risk through unregistered schemes. Always verify any investment with SEBI before investing. Remember: if returns seem too good to be true, they probably are.",
        "verify_at": "sebi.gov.in — verify mutual fund registration"
    },
    "predatory_loan_apps": {
        "content": "Predatory loan apps offer instant loans with minimal documentation but charge exorbitant interest rates and use harassment for recovery. Always check if a lending app is RBI-registered before borrowing.",
        "verify_at": "rbi.org.in — check NBFC registration"
    },
    "ponzi_schemes": {
        "content": "Ponzi schemes pay returns to earlier investors using money from new investors, not from legitimate profits. They collapse when new investments stop. Avoid schemes that emphasize recruiting others over actual investment.",
        "verify_at": "sebi.gov.in — verify investment schemes"
    },
    "whatsapp_investment_tips": {
        "content": "Unsolicited investment tips via WhatsApp or Telegram are often scams to manipulate stock prices. Never act on tips from unknown sources. Always do your own research from verified sources.",
        "verify_at": "sebi.gov.in — investor education resources"
    },
    "fake_govt_schemes": {
        "content": "Scammers create fake government schemes to steal money or personal information. Legitimate government schemes never ask for processing fees or bank OTPs to release benefits.",
        "verify_at": "india.gov.in — official government portal"
    },
    "chit_fund_fraud": {
        "content": "While legitimate chit funds exist under state regulations, fraudulent operators run unregistered chit funds that disappear with investors' money. Always verify registration before joining any chit fund.",
        "verify_at": "mca.gov.in — check company registration"
    },
    "upi_scam": {
        "content": "UPI scams trick users into sharing PINs or OTPs, or use fake QR codes to steal money. Never share your UPI PIN or OTP with anyone, not even someone claiming to be from your bank.",
        "verify_at": "npci.org.in — UPI safety guidelines"
    }
}


# =====================================================
# MAIN SCAM LITERACY AGENT
# =====================================================

def get_scam_education(scam_type: str, user_profile: dict = None, groq_key: str = None) -> dict:
    """
    Educate about a specific financial scam type.

    Parameters
    ----------
    scam_type     : str — e.g. "fake_mutual_funds", "upi_scam"
    user_profile  : dict — contains user info like income, location, etc. (optional)
    groq_key      : str — Groq API key (optional, will try to load from .env)

    Returns
    -------
    dict:
        content    : str   — scam education explanation
        safe       : bool  — passed guardrail filter?
        violations : list  — any flagged phrases found
        helpline   : str   — relevant helpline number
        verify_at  : str   — official source for verification
        fallback   : bool  — True if API unavailable
    """

    # Load scam patterns data
    scam_patterns = load_scam_patterns()

    # Validate scam_type
    if scam_type not in scam_patterns:
        return {
            "content": f"Scam type '{scam_type}' not found in database.",
            "safe": False,
            "violations": [],
            "helpline": "1930 — National Cyber Crime Helpline",
            "verify_at": "https://www.npci.org.in/",
            "fallback": True,
            "error": "Invalid scam type"
        }

    scam_info = scam_patterns[scam_type]

    # ── Validate input ────────────────────────────────
    if not scam_type or not scam_type.strip():
        return {
            "content": "No scam type specified.",
            "safe": False,
            "violations": [],
            "helpline": "1930 — National Cyber Crime Helpline",
            "verify_at": "https://www.npci.org.in/",
            "fallback": True,
            "error": "Empty scam type"
        }

    # ── Check for GROQ API Key ────────────────────────────
    if not groq_key:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()

    use_groq = bool(groq_key and groq_key.strip())

    if not use_groq:
        # Return static fallback
        fallback_data = SCAM_FALLBACKS.get(scam_type, {
            "content": f"Information about {scam_type} is currently unavailable. Please verify at official sources.",
            "verify_at": "https://www.indi.gov.in/"
        })

        return {
            "concept": scam_type,
            "content": fallback_data["content"],
            "safe": True,
            "violations": [],
            "helpline": scam_info.get("helpline", "1930"),
            "verify_at": fallback_data.get("verify_at", scam_info.get("verification_link", "https://www.indi.gov.in")),
            "fallback": True
        }

    # ── Build prompt ──────────────────────────────────
    user_context = ""
    if user_profile:
        user_context = f"""
    USER PROFILE:
    - Location: {user_profile.get('location', 'India')}
    - Age group: {user_profile.get('age_group', 'Not specified')}
    - Primary concerns: {user_profile.get('concerns', 'General financial safety')}
    """

    prompt = f"""You are AarthSaathi, a trusted financial literacy educator for everyday Indians.
    Your specialization is scam awareness and prevention.

    STRICT RULES — always follow:
    - NEVER guarantee any returns or profits (this is scam education, not investment advice)
    - NEVER recommend specific financial products or services
    - NEVER use urgency or fear tactics
    - Use simple language that anyone can understand
    - Keep response under 200 words
    - END with exactly: Verify at: {scam_info.get('verification_link', 'https://www.indi.gov.in')}
    - Include the helpline number: {scam_info.get('helpline', '1930')} in your response

    {user_context}

    Explain the "{scam_info['scam_type']}" scam covering:
    1. What it is in 2-3 simple sentences
    2. How it works (the scam mechanism)
    3. Who typically gets targeted
    4. One key red flag to watch for
    5. What to do if you suspect this scam
    6. Where to report it

    End with: Verify at: {scam_info.get('verification_link', 'https://www.indi.gov.in')}
    Also mention: Helpline: {scam_info.get('helpline', '1930')}"""

    # ── Call Groq API ─────────────────────────
    try:
        client = Groq(api_key=groq_key)

        chat_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=300,
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
            error_msg = "Invalid GROQ_API_KEY. Check your .env file."
        elif "429" in error_msg:
            error_msg = "Rate limit reached. Please wait a moment."
        elif "connection" in error_msg.lower():
            error_msg = "Internet connection issue."
        else:
            error_msg = f"API error: {error_msg}"

        # Return static fallback on API error
        fallback_data = SCAM_FALLBACKS.get(scam_type, {
            "content": f"Information about {scam_type} is currently unavailable. Please verify at official sources.",
            "verify_at": "https://www.indi.gov.in/"
        })

        return {
            "content": fallback_data["content"],
            "safe": True,
            "violations": [],
            "helpline": scam_info.get("helpline", "1930"),
            "verify_at": fallback_data.get("verify_at", scam_info.get("verification_link", "https://www.indi.gov.in")),
            "fallback": True,
            "error": error_msg
        }

    # ── Filter through guardrails ─────────────────────
    filter_result = filter_content(raw_response)

    final_content = (
        filter_result["cleaned_text"]
        if not filter_result["safe"]
        else raw_response
    )

    # Ensure verification link and helpline are present
    verify_text = f"Verify at: {scam_info.get('verification_link', 'https://www.indi.gov.in')}"
    helpline_text = f"Helpline: {scam_info.get('helpline', '1930')}"

    if verify_text not in final_content:
        final_content += f"\n\n{verify_text}"
    if helpline_text not in final_content:
        final_content += f"\n{helpline_text}"

    return {
        "content": final_content.strip(),
        "safe": filter_result["safe"],
        "violations": filter_result["violations"],
        "helpline": scam_info.get("helpline", "1930"),
        "verify_at": scam_info.get("verification_link", "https://www.indi.gov.in"),
        "fallback": False
    }


# =====================================================
# TEST — run this to verify everything works
# python agents/scam_literacy_agent.py
# =====================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  Scam Literacy Agent — Structural Tests")
    print("=" * 60)

    # Test 1: Empty input
    print("\n[TEST 1] Empty scam type")
    r = get_scam_education("")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  error={r.get('error', 'None')}")

    # Test 2: Invalid scam type
    print("\n[TEST 2] Invalid scam type")
    r = get_scam_education("invalid_scam")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  error={r.get('error', 'None')}")

    # Test 3: Valid scam type (should use fallback if no GROQ key)
    print("\n[TEST 3] Valid scam type (UPI scam)")
    r = get_scam_education("upi_scam")
    print(f"  safe={r['safe']}  fallback={r['fallback']}")
    print(f"  has helpline: {'1930' in r['content']}")
    print(f"  has verify at: {'Verify at:' in r['content']}")
    print(f"  content preview: {r['content'][:100]}...")

    # Test 4: Check all scam types load
    print("\n[TEST 4] All scam types load")
    scam_patterns = load_scam_patterns()
    print(f"  Loaded {len(scam_patterns)} scam types")
    for key in scam_patterns.keys():
        print(f"    - {key}")

    print("\n" + "="*60)
    print("  Tests done. Scam Literacy Agent ready.")
    print("="*60)