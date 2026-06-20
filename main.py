# main.py
"""
AarthSaathi Financial Literacy Companion
======================================
Streamlit web app for Indian households to learn about:
- Government schemes
- Financial products (through stories)
- Scam awareness
- Daily financial news
- Personal dashboard
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import time

# Import our agents
from agents.scam_literacy_agent import get_scam_education
from agents.story_agent import get_story

# Import guardrails for safety filtering
try:
    from layers.guardrails import filter_content
except ImportError:
    # Fallback if guardrails not available
    def filter_content(text):
        return {"cleaned_text": text, "safe": True, "violations": []}

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AarthSaathi - Financial Literacy Companion",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Nomura red theme and mobile-friendly layout
st.markdown("""
<style>
    /* Nomura Red Theme */
    :root {
        --nomura-red: #E60012;
        --nomura-dark: #8B0000;
        --nomura-light: #FFE6E6;
    }

    /* Main styling */
    .main-header {
        background: linear-gradient(90px, var(--nomura-red), var(--nomura-dark));
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }

    .sidebar .sidebar-content {
        background-color: var(--nomura-light);
    }

    .stButton>button {
        background-color: var(--nomura-red);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }

    .stButton>button:hover {
        background-color: var(--nomura-dark);
        color: white;
    }

    /* Card styling */
    .story-card, .scam-card, .scheme-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .metric-card {
        background: linear-gradient(135deg, var(--nomura-red) 0%, var(--nomura-dark) 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            padding: 0.5rem;
        }
        .story-card, .scam-card, .scheme-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        'name': '',
        'age_group': 'Not specified',
        'location': 'India',
        'income_range': 'Not specified',
        'concerns': 'General financial literacy'
    }

if 'scam_education_cache' not in st.session_state:
    st.session_state.scam_education_cache = {}

if 'story_cache' not in st.session_state:
    st.session_state.story_cache = {}

# Load data files
@st.cache_data
def load_scam_patterns():
    try:
        with open("data/scam_patterns.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@st.cache_data
def load_stories():
    try:
        with open("data/stories.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@st.cache_data
def load_schemes():
    try:
        with open("data/schemes.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Helper functions
def get_groq_key():
    return os.getenv("GROQ_API_KEY", "").strip()

def display_with_guardrails(content):
    """Display content after applying guardrails"""
    if content:
        filtered = filter_content(content)
        if filtered["safe"]:
            return filtered["cleaned_text"]
        else:
            st.warning("⚠️ Content filtered for safety")
            return filtered["cleaned_text"]
    return content

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div class="main-header">
        <h1>AarthSaathi</h1>
        <p>Financial Literacy Companion</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 My Profile")
    with st.expander("Edit Profile", expanded=False):
        st.session_state.user_profile['name'] = st.text_input("Name", value=st.session_state.user_profile['name'])
        st.session_state.user_profile['age_group'] = st.selectbox(
            "Age Group",
            ["18-25", "26-35", "36-45", "46-55", "56-65", "65+", "Not specified"],
            index=["18-25", "26-35", "36-45", "46-55", "56-65", "65+", "Not specified"].index(st.session_state.user_profile['age_group'])
        )
        st.session_state.user_profile['location'] = st.text_input("Location", value=st.session_state.user_profile['location'])
        st.session_state.user_profile['income_range'] = st.selectbox(
            "Income Range (Monthly)",
            ["< ₹25,000", "₹25,000-50,000", "₹50,000-1,00,000", "₹1,00,000-2,00,000", "> ₹2,00,000", "Not specified"],
            index=["< ₹25,000", "₹25,000-50,000", "₹50,000-1,00,000", "₹1,00,000-2,00,000", "> ₹2,00,000", "Not specified"].index(st.session_state.user_profile['income_range'])
        )
        st.session_state.user_profile['concerns'] = st.text_area(
            "Primary Concerns",
            value=st.session_state.user_profile['concerns'],
            height=100
        )

    st.markdown("---")

    # Navigation menu
    page = st.selectbox(
        "Navigate to:",
        ["🏠 Onboarding", "📊 My Dashboard", "📚 Learn", "🛡️ Scam Awareness", "📖 Stories", "📰 Daily News"]
    )

    st.markdown("---")
    st.markdown("### 🔊 Voice Output")
    voice_enabled = st.checkbox("Enable voice output (placeholder)", value=False)

    st.markdown("---")
    st.markdown("### 📞 Help & Support")
    st.markdown("""
    **National Cyber Crime Helpline:** 1930
    **SEBI Toll Free:** 1800 266 7575
    **RBI Toll Free:** 1800 11 4000
    **Government of India Helpline:** 1800 11 1111
    """)

# Main content based on selected page
if page == "🏠 Onboarding":
    st.markdown("""
    <div class="main-header">
        <h1>Welcome to AarthSaathi!</h1>
        <p>Your trusted companion for financial literacy in India</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎯 What is AarthSaathi?")
        st.markdown("""
        AarthSaathi is a comprehensive financial literacy companion designed specifically for Indian households.
        Our mission is to empower you with knowledge to make informed financial decisions and protect yourself
        from financial frauds.

        ### 🌟 Key Features:
        - **Learn about government schemes** available to you
        - **Understand financial products** through relatable stories
        - **Stay safe from scams** with awareness education
        - **Track your financial journey** with personalized dashboard
        - **Get daily financial news** updates
        """)

        if st.button("Get Started →", type="primary"):
            st.balloons()
            st.success("Welcome aboard! Let's begin your financial literacy journey.")

    with col2:
        st.markdown("### 📈 Quick Stats")
        st.markdown("""
        <div class="metric-card">
            <h3>7+</h3>
            <p>Scam Types Covered</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-card">
            <h3>9+</h3>
            <p>Financial Stories</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-card">
            <h3>5+</h3>
            <p>Government Schemes</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📋 How to Use This App")
    steps = [
        "👤 **Setup your profile** in the sidebar for personalized content",
        "📚 **Explore the Learn section** to understand government schemes",
        "📖 **Read Stories** to see real-life financial situations",
        "🛡️ **Visit Scam Awareness** to learn about financial frauds",
        "📊 **Check your Dashboard** to track your progress",
        "📰 **Stay updated** with Daily Financial News"
    ]

    for i, step in enumerate(steps, 1):
        st.markdown(f"{i}. {step}")

elif page == "📊 My Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>My Financial Dashboard</h1>
        <p>Track your financial literacy journey</p>
    </div>
    """, unsafe_allow_html=True)

    # Profile summary
    st.markdown("### 👤 Your Profile")
    profile_col1, profile_col2, profile_col3 = st.columns(3)

    with profile_col1:
        st.info(f"**Name:** {st.session_state.user_profile['name'] or 'Not set'}")
        st.info(f"**Age Group:** {st.session_state.user_profile['age_group']}")

    with profile_col2:
        st.info(f"**Location:** {st.session_state.user_profile['location']}")
        st.info(f"**Income Range:** {st.session_state.user_profile['income_range']}")

    with profile_col3:
        st.info(f"**Primary Concerns:** {st.session_state.user_profile['concerns']}")
        st.info(f"**Last Updated:** {datetime.now().strftime('%d %b, %Y')}")

    st.markdown("---")

    # Learning progress
    st.markdown("### 📚 Learning Progress")

    # Mock progress data - in real app, this would come from user activity
    progress_data = {
        "Government Schemes": 60,
        "Financial Products": 45,
        "Scam Awareness": 30,
        "Financial Planning": 25
    }

    for topic, progress in progress_data.items():
        st.markdown(f"**{topic}**")
        st.progress(progress / 100)
        st.caption(f"{progress}% completed")

    st.markdown("---")

    # Recommended actions
    st.markdown("### 🎯 Recommended for You")

    recommendations = []

    # Based on user profile
    if "saving" in st.session_state.user_profile['concerns'].lower() or "emergency" in st.session_state.user_profile['concerns'].lower():
        recommendations.append({
            "title": "Emergency Fund Story",
            "type": "story",
            "product": "emergency_fund",
            "reason": "Learn about building financial safety nets"
        })

    if "investment" in st.session_state.user_profile['concerns'].lower():
        recommendations.append({
            "title": "Mutual Fund SIP Guide",
            "type": "learn",
            "topic": "sip",
            "reason": "Understand systematic investment planning"
        })

    if "loan" in st.session_state.user_profile['concerns'].lower() or "debt" in st.session_state.user_profile['concerns'].lower():
        recommendations.append({
            "title": "Predatory Loan Apps Awareness",
            "type": "scam",
            "scam_type": "predatory_loan_apps",
            "reason": "Protect yourself from illegal lending practices"
        })

    # Default recommendations if none match
    if not recommendations:
        recommendations = [
            {
                "title": "PM-KISAN Scheme",
                "type": "learn",
                "topic": "PM-KISAN",
                "reason": "Learn about income support for farmers"
            },
            {
                "title": "UPI Scam Awareness",
                "type": "scam",
                "scam_type": "upi_scam",
                "reason": "Stay safe with digital payments"
            },
            {
                "title": "SIP Success Story",
                "type": "story",
                "product": "sip",
                "story_type": "best",
                "reason": "See how disciplined investing works"
            }
        ]

    # Display recommendations in cards
    rec_cols = st.columns(min(3, len(recommendations)))

    for i, rec in enumerate(recommendations[:3]):
        with rec_cols[i]:
            if rec["type"] == "story":
                with st.container():
                    st.markdown("""
                    <div class="story-card">
                        <h4>📖 {}</h4>
                        <p>{}</p>
                    </div>
                    """.format(rec['title'], rec['reason']), unsafe_allow_html=True)
                    if st.button(f"Read Story", key=f"story_{i}"):
                        st.session_state.selected_story = rec
                        st.switch_page("📖 Stories")

            elif rec["type"] == "scam":
                with st.container():
                    st.markdown("""
                    <div class="scam-card">
                        <h4>🛡️ {}</h4>
                        <p>{}</p>
                    </div>
                    """.format(rec['title'], rec['reason']), unsafe_allow_html=True)
                    if st.button(f"Learn More", key=f"scam_{i}"):
                        st.session_state.selected_scam = rec
                        st.switch_page("🛡️ Scam Awareness")

            elif rec["type"] == "learn":
                with st.container():
                    st.markdown("""
                    <div class="scheme-card">
                        <h4>📚 {}</h4>
                        <p>{}</p>
                    </div>
                    """.format(rec['title'], rec['reason']), unsafe_allow_html=True)
                    if st.button(f"Read Details", key=f"learn_{i}"):
                        st.session_state.selected_scheme = rec
                        st.switch_page("📚 Learn")

elif page == "📚 Learn":
    st.markdown("""
    <div class="main-header">
        <h1>Learn About Government Schemes</h1>
        <p>Discover benefits you're eligible for</p>
    </div>
    """, unsafe_allow_html=True)

    schemes = load_schemes()

    if not schemes:
        st.error("No scheme data available. Please check data/schemes.json")
    else:
        # Scheme selection
        scheme_names = list(schemes.keys())
        selected_scheme = st.selectbox(
            "Select a government scheme to learn about:",
            scheme_names,
            format_func=lambda x: schemes[x]['scheme_name']
        )

        if selected_scheme:
            scheme = schemes[selected_scheme]

            # Display scheme details
            st.markdown(f"### {scheme['scheme_name']}")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Eligibility:**")
                st.write(scheme['eligibility'])

                st.markdown("**Benefits:**")
                st.write(scheme['benefit'])

                st.markdown("**How to Apply:**")
                st.write(scheme['how_to_apply'])

            with col2:
                st.markdown("**Official Link:**")
                st.markdown(f"[Visit Official Website]({scheme['official_link']})")

                if scheme.get('languages_available'):
                    st.markdown("**Languages Available:**")
                    for lang in scheme['languages_available']:
                        st.markdown(f"- {lang}")

            # Verification step
            st.markdown("---")
            st.markdown("### ✅ How to Verify Authenticity")
            st.info(f"Always verify government schemes on official websites ending in **.gov.in** or **.nic.in**. Never pay money to receive government benefits.")

            if st.button("Verify This Scheme", type="primary"):
                with st.spinner("Redirecting to official website..."):
                    time.sleep(1)
                    st.success(f"Opening {scheme['official_link']}...")
                    # In a real app, we might use st.javascript or similar to open external link
                    st.markdown(f"[Click here to visit {scheme['scheme_name']} official website]({scheme['official_link']})")

elif page == "🛡️ Scam Awareness":
    st.markdown("""
    <div class="main-header">
        <h1>Scam Awareness & Prevention</h1>
        <p>Learn to identify and avoid financial frauds</p>
    </div>
    """, unsafe_allow_html=True)

    scam_patterns = load_scam_patterns()

    if not scam_patterns:
        st.error("No scam data available. Please check data/scam_patterns.json")
    else:
        # Scam type selection
        scam_types = list(scam_patterns.keys())
        selected_scam = st.selectbox(
            "Select a scam type to learn about:",
            scam_types,
            format_func=lambda x: scam_patterns[x]['scam_type']
        )

        if selected_scam:
            scam_info = scam_patterns[selected_scam]

            # Display scam details
            st.markdown(f"### 🚨 {scam_info['scam_type']}")

            # Use agent to get education content
            if st.button("Get Detailed Education", type="primary"):
                with st.spinner("Generating scam education content..."):
                    groq_key = get_groq_key()
                    education_result = get_scam_education(
                        scam_type=selected_scam,
                        user_profile=st.session_state.user_profile,
                        groq_key=groq_key
                    )

                    if education_result['safe']:
                        st.markdown("#### 📝 Education Content")
                        st.write(display_with_guardrails(education_result['content']))

                        # Show metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"Safe: {education_result['safe']}")
                        with col2:
                            st.caption(f"Fallback: {education_result['fallback']}")
                        with col3:
                            if education_result['violations']:
                                st.caption(f"Violations: {len(education_result['violations'])}")
                    else:
                        st.error("Failed to generate scam education content")
                        st.write(education_result.get('content', 'No content available'))

            # Static information panel
            st.markdown("---")
            st.markdown("### 📋 Quick Facts")

            fact_col1, fact_col2 = st.columns(2)

            with fact_col1:
                st.markdown("**Description:**")
                st.write(scam_info['description'])

                st.markdown("**Red Flags to Watch For:**")
                for flag in scam_info['red_flags']:
                    st.markdown(f"• {flag}")

            with fact_col2:
                st.markdown("**Real Example:**")
                st.write(scam_info['real_example'])

                st.markdown("**Verification Step:**")
                st.write(scam_info['verification_step'])

            # Action buttons
            st.markdown("---")
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if st.button("📞 Report This Scam"):
                    st.info(f"Contact: {scam_info['helpline']}")

            with action_col2:
                if st.button("🔗 Verify Official Source"):
                    st.markdown(f"[Visit Verification Link]({scam_info['verification_link']})")

            with action_col3:
                if st.button("📚 Learn More"):
                    st.session_state.selected_scam_for_story = selected_scam
                    st.switch_page("📖 Stories")

elif page == "📖 Stories":
    st.markdown("""
    <div class="main-header">
        <h1>Financial Literacy Stories</h1>
        <p>Learn through relatable real-life situations</p>
    </div>
    """, unsafe_allow_html=True)

    stories = load_stories()

    if not stories:
        st.error("No story data available. Please check data/stories.json")
    else:
        # Story selection
        story_cols = st.columns([1, 1, 2])

        with story_cols[0]:
            product_options = list(stories.keys())
            selected_product = st.selectbox(
                "Select Product:",
                product_options,
                format_func=lambda x: x.replace('_', ' ').title()
            )

        with story_cols[1]:
            if selected_product:
                type_options = list(stories[selected_product].keys())
                selected_type = st.selectbox(
                    "Select Type:",
                    type_options,
                    format_func=lambda x: x.title()
                )

        with story_cols[2]:
            if selected_product and selected_type:
                if st.button("Get Story", type="primary", use_container_width=True):
                    with st.spinner("Fetching story..."):
                        groq_key = get_groq_key()
                        story_result = get_story(
                            product=selected_product,
                            story_type=selected_type,
                            user_profile=st.session_state.user_profile,
                            groq_key=groq_key
                        )

                        if story_result['safe']:
                            st.session_state.current_story = {
                                'content': story_result['content'],
                                'product': selected_product,
                                'type': selected_type,
                                'verify_at': story_result['verify_at'],
                                'safe': story_result['safe'],
                                'fallback': story_result['fallback']
                            }
                        else:
                            st.error("Failed to fetch story")

        # Display current story
        if 'current_story' in st.session_state and st.session_state.current_story:
            story_data = st.session_state.current_story

            # Story header
            product_name = story_data['product'].replace('_', ' ').title()
            type_name = story_data['type'].title()

            st.markdown(f"""
            <div class="story-card">
                <h3>📖 {product_name} - {type_name} Scenario</h3>
            </div>
            """, unsafe_allow_html=True)

            # Story content
            st.markdown("### 📜 Story")
            st.write(display_with_guardrails(story_data['content']))

            # Story metadata
            st.markdown("---")
            meta_col1, meta_col2, meta_col3 = st.columns(3)

            with meta_col1:
                if story_data['fallback']:
                    st.warning("⚠️ Using static content (API unavailable)")
                else:
                    st.success("✅ Enhanced with AI")

            with meta_col2:
                st.caption(f"Safe: {story_data['safe']}")

            with meta_col3:
                if not story_data['safe']:
                    st.error("Content filtered")

            # Verification
            st.markdown(f"""
            <div style="text-align: center; margin-top: 1rem;">
                <p><small>Verify at: {story_data['verify_at']}</small></p>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if st.button("🔄 Get Another Story", use_container_width=True):
                    if 'current_story' in st.session_state:
                        del st.session_state.current_story
                    st.rerun()

            with action_col2:
                if st.button("📊 See Related Scheme", use_container_width=True):
                    # Map products to schemes (simplified)
                    product_to_scheme = {
                        'emergency_fund': 'Jan_Dhan',  # Savings account
                        'sip': 'PM-Suraksha-Bima',     # Investment-related
                        'fd': 'Atal_Pension_Yojana'    # Long-term savings
                    }
                    scheme_key = product_to_scheme.get(story_data['product'])
                    if scheme_key:
                        st.info(f"Try learning about {scheme_key} in the Learn section")
                    else:
                        st.info("Explore the Learn section for related government schemes")

            with action_col3:
                if st.button("💡 Learn Scam Prevention", use_container_width=True):
                    st.info("Visit the Scam Awareness section to learn about financial frauds")

elif page == "📰 Daily News":
    st.markdown("""
    <div class="main-header">
        <h1>Daily Financial News</h1>
        <p>Stay updated with the latest financial developments</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📰 Latest Financial Updates")

    # Mock news data - in real app, this would come from a news API
    news_items = [
        {
            "title": "RBI Repo Rate Unchanged at 6.5%",
            "timestamp": "2 hours ago",
            "summary": "The Reserve Bank of India decided to keep the repo rate unchanged at 6.5% in its latest monetary policy meeting, citing inflation concerns.",
            "category": "Banking",
            "importance": "High"
        },
        {
            "title": "SEBI Introduces New Rules for Mutual Fund Advertising",
            "timestamp": "4 hours ago",
            "summary": "SEBI has introduced stricter guidelines for mutual fund advertisements to prevent misleading claims about returns.",
            "category": "Investment",
            "importance": "Medium"
        },
        {
            "title": "UPI Transactions Cross ₹15 Lakh Crore Monthly",
            "timestamp": "6 hours ago",
            "summary": "Unified Payments Interface (UPI) transactions continue to grow, crossing ₹15 lakh crore in monthly volume for the first time.",
            "category": "Digital Payments",
            "importance": "High"
        },
        {
            "title": "Government Launches New Savings Scheme for Senior Citizens",
            "timestamp": "1 day ago",
            "summary": "A new savings scheme offering 7.8% interest has been launched specifically for senior citizens above 60 years of age.",
            "category": "Savings",
            "importance": "Medium"
        },
        {
            "title": "Stock Market Shows Volatility Amid Global Cues",
            "timestamp": "1 day ago",
            "summary": "Indian stock markets showed mixed trends today as global markets reacted to international economic data releases.",
            "category": "Markets",
            "importance": "Low"
        }
    ]

    # Filter options
    filter_col1, filter_col2 = st.columns([2, 1])

    with filter_col1:
        category_filter = st.multiselect(
            "Filter by Category:",
            options=list(set(item['category'] for item in news_items)),
            default=list(set(item['category'] for item in news_items))
        )

    with filter_col2:
        importance_filter = st.multiselect(
            "Filter by Importance:",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )

    # Display filtered news
    filtered_news = [
        item for item in news_items
        if item['category'] in category_filter and item['importance'] in importance_filter
    ]

    if not filtered_news:
        st.info("No news items match the selected filters.")
    else:
        for news in filtered_news:
            # Determine card color based on importance
            if news['importance'] == 'High':
                border_color = "#E60012"  # Nomura red
                bg_color = "#FFE6E6"
            elif news['importance'] == 'Medium':
                border_color = "#FFA500"  # Orange
                bg_color = "#FFF8F0"
            else:
                border_color = "#4CAF50"  # Green
                bg_color = "#F0FFF8"

            st.markdown(f"""
            <div style="
                border-left: 4px solid {border_color};
                background-color: {bg_color};
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 0 5px 5px 0;
            ">
                <h4>{news['title']}</h4>
                <p><small>{news['timestamp']} | {news['category']} | {news['importance']} Importance</small></p>
                <p>{news['summary']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📺 Financial Education Resources")

    resource_col1, resource_col2, resource_col3 = st.columns(3)

    with resource_col1:
        st.markdown("""
        **📚 Investor Education**
        - SEBI Investor Website: sebiedu.in
        - RBI Financial Education: rbi.org.in/financialeducation
        - NSE Academy: nseindia.com/education
        """)

    with resource_col2:
        st.markdown("""
        **📱 Government Apps**
        - UMANG: umang.gov.in
        - Digilocker: digilocker.gov.in
        - Aarogya Setu: aarogyasetu.gov.in
        """)

    with resource_col3:
        st.markdown("""
        **📞 Help Lines**
        - SEBI Toll Free: 1800 266 7575
        - RBI Toll Free: 1800 11 4000
        - NHB Complaints: 1800 11 33 88
        - Consumer Helpline: 1800 11 4000
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>© 2026 AarthSaathi - Financial Literacy Companion for Indian Houses</p>
    <p>Empowering financial literacy through education and awareness</p>
</div>
""", unsafe_allow_html=True)