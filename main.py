import streamlit as st
from pathlib import Path
from faq import ingest_faq_data
from chat import ask

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="ShopAssist AI | E-Commerce Concierge",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Modern UI Styling & Pinned Header
st.markdown("""
<style>
    /* Make Streamlit header transparent so it doesn't obscure the sticky card */
    header[data-testid="stHeader"] {
        background: transparent;
        pointer-events: none;
    }
    header[data-testid="stHeader"] * {
        pointer-events: auto;
    }

    /* Clean up container padding and hide default menu/footer */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Pin the Streamlit wrapper containing the hero card */
    div[data-testid="stElementContainer"]:has(.hero-card),
    div[data-testid="element-container"]:has(.hero-card) {
        position: sticky;
        top: 0.5rem;
        z-index: 999;
    }

    /* Hero Header Card Styling */
    .hero-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 1.25rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        gap: 10px;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 0.9rem;
        color: #c7d2fe;
        margin-top: 0.3rem;
        margin-bottom: 0;
        font-weight: 400;
    }

    /* Route Indicator Badges */
    .route-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    .badge-faq {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-sql {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-small_talk {
        background-color: rgba(168, 85, 247, 0.15);
        color: #a855f7;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }
    .badge-unknown {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Chat Message Container Polish */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
    }

    /* Quick Prompt Buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        border-color: #6366f1;
    }
</style>
""", unsafe_allow_html=True)


# 3. Cached Data Ingestion
@st.cache_resource(show_spinner="Initializing Knowledge Base...")
def init_faq():
    faqs_path = Path(__file__).parent / 'resources/faq_data.csv'
    ingest_faq_data(faqs_path)


init_faq()

# 4. Route Metadata & Helper Logic
ROUTE_META = {
    'faq': ('📋 Policy & FAQ', 'badge-faq'),
    'sql': ('🔍 Product Catalog', 'badge-sql')
}


def render_badge(route_name: str):
    label, css_class = ROUTE_META.get(route_name, ('⚠️ Unrouted', 'badge-unknown'))
    st.markdown(f'<div class="route-badge {css_class}">{label}</div>', unsafe_allow_html=True)


# 5. Session State Initialization
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# 6. Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.caption("Smart routing across SQL inventory, FAQ policies, and conversational AI.")

    show_badges = st.toggle("Show Router Badges", value=True,
                            help="Display which internal chain answered your question.")
    st.divider()

    st.markdown("#### 🧠 Capabilities")
    st.markdown(
        "- **🔍 Product Search:** Filter by price, brand, rating, or discount.\n"
        "- **📋 Store FAQs:** Return policies, payment methods, & order tracking."
    )
    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state['messages'] = []
        st.rerun()

# 7. Main Header Banner (Pinned)
st.markdown("""
<div class="hero-card">
    <div class="hero-title">🛍️ ShopAssist AI</div>
    <p class="hero-subtitle">Ask about products, discounts, return policies, or order support.</p>
</div>
""", unsafe_allow_html=True)

# 8. Welcome Screen & Quick-Action Prompts (Only shown when chat is empty)
selected_suggestion = None
if not st.session_state['messages']:
    st.markdown("##### ✨ Try asking one of these:")
    col1, col2 = st.columns(2)

    suggestions = [
        ("👟 Show Nike shoes under ₹3000", col1),
        ("📦 What is your return policy?", col2),
        ("🔥 Top 5 rated shoes with >30% discount", col1),
        ("💳 What payment methods do you accept?", col2)
    ]

    for prompt_text, col in suggestions:
        with col:
            if st.button(prompt_text, use_container_width=True):
                selected_suggestion = prompt_text.split(" ", 1)[1]

# 9. Render Existing Chat History
for message in st.session_state['messages']:
    avatar = "🧑‍💻" if message['role'] == 'user' else "🤖"
    with st.chat_message(message['role'], avatar=avatar):
        if message['role'] == 'assistant' and show_badges and 'route' in message:
            render_badge(message['route'])
        st.markdown(message['content'])

# 10. Handle Input
chat_input_query = st.chat_input("Ask about products, prices, or store policies...")
active_query = selected_suggestion or chat_input_query

if active_query:
    with st.chat_message('user', avatar="🧑‍💻"):
        st.markdown(active_query)
    st.session_state['messages'].append({'role': 'user', 'content': active_query})

    with st.chat_message('assistant', avatar="🤖"):
        with st.spinner("Thinking..."):
            response_text, route_used = ask(active_query)

        if show_badges:
            render_badge(route_used)
        st.markdown(response_text)

    st.session_state['messages'].append({
        'role': 'assistant',
        'content': response_text,
        'route': route_used
    })

    if selected_suggestion:
        st.rerun()