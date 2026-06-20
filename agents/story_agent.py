# agents/story_agent.py
"""
AarthSaathi Story Agent
-----------------------
Provides financial literacy stories for different products and user types.
Uses Groq for enhanced storytelling with fallback to static content.
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


def load_stories():
    """Load stories from JSON file."""
    try:
        json_path = Path(__file__).parent.parent / "data" / "stories.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading stories: {e}")
        return {}


# =====================================================
# STATIC FALLBACKS
# Shown when API is unavailable — never blank screen
# =====================================================

STORY_FALLBACKS = {
    "emergency_fund": {
        "common": {
            "content": "Priya lives in Mumbai with her roommate. She earns ₹40,000 monthly but has never saved for emergencies. When her laptop broke during a crucial presentation, she had to borrow ₹15,000 from friends at 2% monthly interest. It took her 4 months to repay, causing stress and straining relationships. After this experience, Priya started saving ₹5,000 monthly in a separate savings account. After 10 months, she has ₹50,000 as her emergency fund. An emergency fund isn't optional - it's your financial shock absorber. Start small but start now.",
            "verify_at": "rbi.org.in — for guidance on savings accounts"
        },
        "best": {
            "content": "Amit from Bangalore learned about emergency funds early in his career. He automated savings of 20% of his salary into a liquid fund and high-yield savings account. When his father had a medical emergency requiring ₹3 lakhs, Amit could pay immediately without breaking his investments or taking loans. Amit's emergency fund covered 6 months of expenses. He continued his SIPs uninterrupted and his father recovered well. The peace of mind was invaluable. Planning today prevents panic tomorrow. An emergency fund protects your long-term wealth from short-term crises.",
            "verify_at": "rbi.org.in — for guidance on emergency savings"
        },
        "worst": {
            "content": "Sneha from Hyderabad believed her credit card was her emergency fund. When she lost her job during lockdown, she maxed out her ₹1 lakh limit on essentials. With 40% annual interest and minimum payments, her debt grew to ₹1.3 lakhs in 6 months. It took Sneha 18 months of strict budgeting to clear her credit card debt. She missed investment opportunities and her credit score suffered significantly. Credit cards are not emergency funds. High-interest debt can derail years of financial progress in months.",
            "verify_at": "rbi.org.in — for guidance on debt management"
        }
    },
    "sip": {
        "common": {
            "content": "Rajesh from Jaipur started a ₹2,000 monthly SIP in an equity mutual fund 5 years ago. He missed only 3 months during his wedding. Despite market ups and downs, his investment grew to ₹1.6 lakhs. After 5 years, Rajesh has built discipline and confidence. He increased his SIP to ₹3,000 when he got a promotion and plans to start another SIP for his daughter's education. Consistency beats timing in mutual funds. Small, regular investments build wealth over time.",
            "verify_at": "sebi.gov.in — verify mutual fund registration"
        },
        "best": {
            "content": "Ananya from Pune started SIPs worth ₹15,000 monthly across different fund categories when she turned 25. She reviewed her portfolio annually but never paused SIPs during market downturns, viewing them as buying opportunities. After 4 years, Ananya's investments grew to ₹9 lakhs. She's on track to buy her first home without straining her finances. Starting early gives compound interest time to work magic. Market timing is less important than time in market.",
            "verify_at": "sebi.gov.in — verify mutual fund registration"
        },
        "worst": {
            "content": "Vikram from Delhi stopped his ₹5,000 monthly SIP after 8 months when he saw a 5% loss. He kept the money in his savings account earning 3% interest. When he restarted SIPs 2 years later, he missed significant market growth. Had Vikram continued his SIPs, he would have had ₹40,000 more today. His attempt to 'time the market' cost him dearly. Trying to time the market often means missing the market. Stay invested through ups and downs.",
            "verify_at": "sebi.gov.in — verify mutual fund registration"
        }
    },
    "fd": {
        "common": {
            "content": "Lakshmi from Chennai keeps her emergency fund and short-term savings in fixed deposits. She laddered her FDs - ₹1 lakh each for 6 months, 1 year, and 2 years - to balance returns with liquidity needs. When Lakshmi needed ₹2 lakhs for her son's college admission, she could break only the 6-month FD, minimizing interest loss. Her planned approach worked perfectly. Fixed deposits provide safety and predictable returns. Laddering helps balance liquidity and yield.",
            "verify_at": "rbi.org.in — verify bank FD safety"
        },
        "best": {
            "content": "Mohammed from Lucknow uses FDs for goal-based saving. When his daughter was born, he started FDs maturing at ages 18 and 21 for her education. The guaranteed returns helped him plan precisely. When his daughter turned 18, the FD matured to exactly the amount needed for her engineering admission. No loans, no stress. For specific financial goals with known timelines, FDs offer certainty that market-linked products cannot.",
            "verify_at": "rbi.org.in — verify bank FD safety"
        },
        "worst": {
            "content": "Deepak from Indore kept all his savings in long-term FDs for 5 years to get slightly higher interest. When his mother needed urgent surgery, he broke the FD prematurely, losing interest and paying penalties. Deepak received less money than expected and learned that locking funds too long creates liquidity problems during emergencies. Match your investment horizon with your financial goals. Don't sacrifice liquidity for slightly higher returns.",
            "verify_at": "rbi.org.in — verify bank FD safety"
        }
    }
}


# =====================================================
# MAIN STORY AGENT
# =====================================================

def get_story(product: str, story_type: str, user_profile: dict = None, groq_key: str = None) -> dict:
    """
    Get a financial literacy story for a specific product and user type.

    Parameters
    ----------
    product       : str — e.g. "emergency_fund", "sip", "fd"
    story_type    : str — e.g. "common", "best", "worst"
    user_profile  : dict — contains user info like income, location, etc. (optional)
    groq_key      : str — Groq API key (optional, will try to load from .env)

    Returns
    -------
    dict:
        content    : str   — story explanation
        safe       : bool  — passed guardrail filter?
        violations : list  — any flagged phrases found
        helpline   : str   — relevant helpline number (if applicable)
        verify_at  : str   — official source for verification
        fallback   : bool  — True if API unavailable
    """

    # Load stories data
    stories = load_stories()

    # Validate inputs
    if product not in stories:
        return {
            "content": f"Product '{product}' not found in database.",
            "safe": False,
            "violations": [],
            "helpline": "1800 11 1111 — Government of India Helpline",
            "verify_at": "https://www.indi.gov.in/",
            "fallback": True,
            "error": "Invalid product"
        }

    if story_type not in stories[product]:
        return {
            "content": f"Story type '{story_type}' not found for product '{product}'.",
            "safe": False,
            "violations": [],
            "helpline": "1800 11 1111 — Government of India Helpline",
            "verify_at": "https://www.indi.gov.in/",
            "fallback": True,
            "error": "Invalid story type"
        }

    # ── Validate input ────────────────────────────────
    if not product or not product.strip():
        return {
            "content": "No product specified.",
            "safe": False,
            "violations": [],
            "helpline": "1800 11 1111 — Government of India Helpline",
            "verify_at": "https://www.indi.gov.in/",
            "fallback": True,
            "error": "Empty product"
        }

    if not story_type or not story_type.strip():
        return {
            "content": "No story type specified.",
            "safe": False,
            "violations": [],
            "helpline": "1800 11 1111 — Government of India Helpline",
            "verify_at": "https://www.indi.gov.in/",
            "fallback": True,
            "error": "Empty story type"
        }

    story_info = stories[product][story_type]

    # ── Check for GROQ API Key ────────────────────────────
    if not groq_key:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()

    use_groq = bool(groq_key and groq_key.strip())

    if not use_groq:
        # Return static fallback
        fallback_data = STORY_FALLBACKS.get(product, {}).get(story_type, {
            "content": f"Story about {product} ({story_type}) is currently unavailable. Please check official sources for financial education.",
            "verify_at": "https://www.indi.gov.in/"
        })

        return {
            "content": fallback_data["content"],
            "safe": True,
            "violations": [],
            "helpline": story_info.get("helpline", "1800 11 1111 — Government of India Helpline"),
            "verify_at": fallback_data.get("verify_at", story_info.get("verify_at", "https://www.indi.gov.in")),
            "fallback": True
        }

    # ── Build prompt ──────────────────────────────────
    user_context = ""
    if user_profile:
        user_context = f"""
    USER PROFILE:
    - Location: {user_profile.get('location', 'India')}
    - Age group: {user_profile.get('age_group', 'Not specified')}
    - Income range: {user_profile.get('income_range', 'Not specified')}
    - Primary concerns: {user_profile.get('concerns', 'General financial literacy')}
    """

    prompt = f"""You are AarthSaathi, a trusted financial literacy educator for everyday Indians.
    Your specialization is creating relatable stories that teach financial concepts.

    STRICT RULES — always follow:
    - NEVER guarantee any returns or profits (this is education, not investment advice)
    - NEVER recommend specific financial products or services
    - NEVER use urgency or fear tactics
    - Use simple language that anyone can understand
    - Keep response under 250 words
    - END with exactly: Verify at: {story_info.get('verify_at', 'https://www.indi.gov.in')}
    - Make the story relatable to everyday Indians
    - Focus on the lesson learned, not just the narrative

    {user_context}

    Create a financial literacy story about {product} for a {story_type} scenario covering:
    1. Relatable protagonist with realistic Indian name and occupation
    2. Their financial situation and challenges
    3. The specific situation that demonstrates the importance of {product}
    4. What happened (the consequence of their actions or inaction)
    5. What they learned and how they changed their behavior
    6. The key lesson for the reader

    End with: Verify at: {story_info.get('verify_at', 'https://www.indi.gov.in')}"""

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
            max_tokens=350,
            temperature=0.7
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
        fallback_data = STORY_FALLBACKS.get(product, {}).get(story_type, {
            "content": f"Story about {product} ({story_type}) is currently unavailable. Please check official sources for financial education.",
            "verify_at": "https://www.indi.gov.in/"
        })

        return {
            "content": fallback_data["content"],
            "safe": True,
            "violations": [],
            "helpline": story_info.get("helpline", "1800 11 1111 — Government of India Helpline"),
            "verify_at": fallback_data.get("verify_at", story_info.get("verify_at", "https://www.indi.gov.in")),
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

    # Ensure verification link is present
    verify_text = f"Verify at: {story_info.get('verify_at', 'https://www.indi.gov.in')}"

    if verify_text not in final_content:
        final_content += f"\n\n{verify_text}"

    return {
        "content": final_content.strip(),
        "safe": filter_result["safe"],
        "violations": filter_result["violations"],
        "helpline": story_info.get("helpline", "1800 11 1111 — Government of India Helpline"),
        "verify_at": story_info.get("verify_at", "https://www.indi.gov.in"),
        "fallback": False
    }


# =====================================================
# TEST — run this to verify everything works
# python agents/story_agent.py
# =====================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  Story Agent — Structural Tests")
    print("=" * 60)

    # Test 1: Empty product
    print("\n[TEST 1] Empty product")
    r = get_story("", "common")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  error={r.get('error', 'None')}")

    # Test 2: Invalid product
    print("\n[TEST 2] Invalid product")
    r = get_story("invalid_product", "common")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  error={r.get('error', 'None')}")

    # Test 3: Invalid story type
    print("\n[TEST 3] Invalid story type")
    r = get_story("emergency_fund", "invalid_type")
    print(f"  safe={r['safe']}  fallback={r['fallback']}  error={r.get('error', 'None')}")

    # Test 4: Valid inputs (should use fallback if no GROQ key)
    print("\n[TEST 4] Valid inputs (emergency_fund, common)")
    r = get_story("emergency_fund", "common")
    print(f"  safe={r['safe']}  fallback={r['fallback']}")
    print(f"  has verify at: {'Verify at:' in r['content']}")
    print(f"  content preview: {r['content'][:100]}...")

    # Test 5: Check all products and types load
    print("\n[TEST 5] All products and story types load")
    stories = load_stories()
    print(f"  Loaded {len(stories)} products")
    for product, types in stories.items():
        print(f"    - {product}: {list(types.keys())}")

    print("\n" + "="*60)
    print("  Tests done. Story Agent ready.")
    print("="*60)