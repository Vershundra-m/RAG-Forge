import google.generativeai as genai
import streamlit as st
from rag_forge import config
from rag_forge.vectorstores import get_store

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS - TWU Maroon + Accessibility

st.markdown(
    """
<style>
    /* TWU Maroon: #850928 */
    .stButton > button {
        background-color: #850928;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #5C0620;
        color: white;
    }
    .stButton > button:focus {
        outline: 3px solid #FFD700;
        outline-offset: 2px;
    }
    .user-message {
        background-color: #F5F5F5;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #850928;
    }
    .assistant-message {
        background-color: #FFF8F8;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #850928;
    }
    .citation {
        background-color: #F0F0F0;
        border-left: 3px solid #850928;
        padding: 6px 12px;
        margin-top: 8px;
        font-size: 0.85em;
        color: #333;
        border-radius: 4px;
    }
   .disclaimer {
     background-color: #FFF3CD;
     border: 2px solid #850928;
     border-radius: 8px;
     padding: 10px 14px;
    margin: 10px 0;
    font-size: 0.95em;
     color: #1A1A1A !important;
    font-weight: 500;
}
    .disclaimer strong {
        color: #850928 !important;
}
    /* High-contrast focus indicator for accessibility */
    *:focus-visible {
        outline: 3px solid #FFD700 !important;
        outline-offset: 2px !important;
    }
    /* Screen reader only text */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# FAQ Questions

FAQ_QUESTIONS = [
    ("Alcohol Policy", "What is the alcohol policy on campus?"),
    ("Academic Integrity", "What is the academic integrity policy?"),
    ("Sick Leave", "What is the sick leave policy?"),
    ("Title IX", "What is the Title IX policy?"),
    ("Employee Leave", "What is the employee leave policy?"),
]

# URP Categories (with subcategories)

URP_CATEGORIES = {
    "Administration": [
        "Governance", "General", "Office of General Counsel",
        "Marketing and Communication",
    ],
    "Academic Affairs": [
        "Governance", "General", "Faculty Affairs", "Research",
    ],
    "Advancement": [
        "General", "Administration of Gifts and Grants", "Endowment Funds",
    ],
    "Finance and Administration": [
        "General", "Fiscal Management", "Procurement", "Risk Management",
        "Facilities Management and Construction", "Public Safety",
        "Information Technology",
    ],
    "Human Resources": [
        "Equal Employment Opportunity and Nondiscrimination",
        "Recruitment and Appointment",
        "Employee Development and Education",
        "Employee Benefits and Compensation",
        "Employee Leave",
        "Employment Relations",
    ],
    "Student Affairs": [
        "General", "Student Conduct", "University Housing",
        "Student Organizations", "Student Employment",
    ],
}

# Session State

if "messages" not in st.session_state:
    st.session_state.messages = []
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "category_filter" not in st.session_state:
    st.session_state.category_filter = None
if "subcategory_filter" not in st.session_state:
    st.session_state.subcategory_filter = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "db" not in st.session_state:
    with st.spinner(f"Loading {config.APP_NAME}..."):
        db = get_store()
        db.setup()
        st.session_state.db = db

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")


# Sidebar - Category Filters + Info

with st.sidebar:
    st.header("📋 Filter by Category")

    category = st.selectbox(
        "URP Category",
        options=["View All"] + list(URP_CATEGORIES.keys()),
        key="category_select",
    )
    st.session_state.category_filter = None if category == "View All" else category

    # Show subcategories when a category is selected
    if category != "View All":
        subcategory = st.selectbox(
            "Subcategory",
            options=["All Subcategories"] + URP_CATEGORIES[category],
            key="subcategory_select",
        )
        st.session_state.subcategory_filter = (
            None if subcategory == "All Subcategories" else subcategory
        )
    else:
        st.session_state.subcategory_filter = None

    st.markdown("---")

    # Info icon with disclaimer
    st.header("ⓘ Session Info")
    st.markdown(
        """
        <div class="disclaimer" role="note" aria-label="Session limit disclaimer">
            <strong>10 questions per session.</strong><br>
            Click "Reset Session" to start over.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(st.session_state.question_count / 10)
    st.caption(f"Questions used: {st.session_state.question_count}/10")

    st.markdown("---")
    st.header("ℹ️ About")
    st.caption(f"Model: Gemini 2.5 Flash-Lite")
    st.caption(f"Vector Store: {config.VECTOR_STORE}")
    st.caption(f"Index: {config.PINECONE_INDEX_NAME}")

    st.markdown("---")
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.question_count = 0
        st.session_state.pending_question = None
        st.rerun()

# Header

col1, col2 = st.columns([3, 1])
with col1:
    st.title(config.APP_NAME)
    st.caption("Ask questions about Texas Woman's University Regulations & Procedures (URPs)")
with col2:
    if config.HELP_URL:
        st.markdown(f"[❓ Help]({config.HELP_URL})")

st.markdown("---")


# FAQ Shortcut Buttons

st.subheader("Frequently Asked Questions")
faq_cols = st.columns(len(FAQ_QUESTIONS))

for idx, (label, question) in enumerate(FAQ_QUESTIONS):
    with faq_cols[idx]:
        if st.button(label, use_container_width=True, key=f"faq_{idx}"):
            st.session_state.pending_question = question


# Search Input

with st.form(key="question_form", clear_on_submit=True):
    text_input = st.text_input(
        "Ask a question about TWU policies",
        placeholder="e.g., What is the policy on alcohol use?",
        label_visibility="visible",
    )
    ask_button = st.form_submit_button("🔍 Ask", use_container_width=True)

# Chat History

st.markdown("---")
st.subheader("Chat History")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # Show citations if present
        if msg.get("citations"):
            st.markdown(
                f'<div class="citation" role="note" aria-label="Sources">'
                f'<strong>📚 Sources:</strong><br>{msg["citations"]}</div>',
                unsafe_allow_html=True,
            )

if not st.session_state.messages:
    st.info("👋 Welcome! Ask a question above or click one of the FAQ buttons to get started.")


# Clear Chat Button
col_clear, _ = st.columns([1, 5])
with col_clear:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.question_count = 0
        st.session_state.pending_question = None
        st.rerun()


# Footer
st.markdown("---")
if config.FOOTER_TEXT:
    st.caption(config.FOOTER_TEXT)


# Answer Generation
def generate_answer(question: str) -> tuple[str, str]:
    """Returns (answer, citations_html)"""
    retrieved = st.session_state.db.query(question, top_k=3)

    if not retrieved:
        return (
            "No relevant information found. Please try rephrasing your question.",
            "",
        )

    context = "\n\n---\n\n".join([chunk["text"] for chunk in retrieved])
    no_info = "I don't have that information."
    prompt = (
        f"Answer the question based on the context below. "
        f'If the answer is not in the context, say "{no_info}"\n\n'
        f"CONTEXT: {context}\nQUESTION: {question}\nANSWER:"
    )

    response = model.generate_content(prompt)
    answer = response.text

    # Build citations HTML
    citations = []
    for i, chunk in enumerate(retrieved, 1):
        text_preview = chunk["text"][:100].replace("\n", " ")
        score = chunk.get("score", 0)
        citations.append(
            f"<b>{i}.</b> Score: {score:.3f} — {text_preview}..."
        )
    citations_html = "<br>".join(citations)

    return answer, citations_html


# Handle Queries 

question_to_process = None

if st.session_state.question_count >= 10:
    if st.session_state.pending_question or (ask_button and text_input.strip()):
        st.warning(
            "⚠️ You have reached the 10-question limit for this session. "
            "Please click 'Reset Session' in the sidebar to continue."
        )
        st.session_state.pending_question = None

elif st.session_state.pending_question:
    question_to_process = st.session_state.pending_question
    st.session_state.pending_question = None

elif ask_button and text_input and text_input.strip():
    question_to_process = text_input.strip()

if question_to_process:
    st.session_state.messages.append({"role": "user", "content": question_to_process})

    with st.spinner("Searching policies..."):
        answer, citations = generate_answer(question_to_process)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "citations": citations}
    )
    st.session_state.question_count += 1
    st.rerun()