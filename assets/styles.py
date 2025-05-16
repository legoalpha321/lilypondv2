import streamlit as st

def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #888888;
            margin-bottom: 2rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 4rem;
            white-space: pre-wrap;
            border-radius: 4px 4px 0 0;
        }
        .footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #eeeeee;
            text-align: center;
            color: #888888;
        }
        .block-container {
            padding-top: 2rem;
        }
        /* Make the text area larger */
        .stTextArea textarea {
            height: 400px !important;
            font-family: monospace !important;
        }
        /* Highlight the active tab */
        .stTabs [aria-selected="true"] {
            background-color: rgba(151, 166, 195, 0.15);
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)