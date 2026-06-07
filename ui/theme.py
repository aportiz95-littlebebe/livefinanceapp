import streamlit as st

def apply_custom_theme():
    """Injects the custom hex color theme and CSS styling into the Streamlit app."""
    st.markdown(
        """
        <style>
            .stApp, body, .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab-panel"] {
                background-color: #F9F5EA !important;
            }
            span, label, .stApp p { color: #3A3A3A; }
            h3 {
                color: #3A3A3A !important; background-color: #EAD8C0 !important;
                padding: 8px 16px !important; border-radius: 20px !important;
                display: inline-block !important; margin-bottom: 12px !important;
                border: 1px solid rgba(255,255,255,0.5) !important;
            }
            div[data-testid="stExpander"], div[data-testid="stForm"], 
            .stDataEditor, div[data-testid="stMetricContainer"] {
                background-color: #FFFDFB !important; border-radius: 8px !important;
                padding: 15px !important; border: 1px solid rgba(0,0,0,0.05) !important;
            }
            div.stButton > button {
                background-color: #98966D !important; border: none !important;
                border-radius: 12px !important; padding: 8px 20px !important;
                transition: all 0.2s ease-in-out !important;
            }
            div.stButton > button p {
                color: #FFFFFF !important; font-size: 13px !important;
                font-weight: 700 !important; font-family: sans-serif !important;
                letter-spacing: 0.5px !important; margin: 0px !important;
            }
            div.stButton > button:hover, div.stButton > button:active {
                background-color: #88865D !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
                color: #FFFFFF !important;
            }
            div.stButton > button:hover p, div.stButton > button:active p { color: #FFFFFF !important; }
            div[role="dialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5) div.stButton > button,
            div[role="dialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(6) div.stButton > button {
                transform: scale(0.75) !important;
            }
            div[data-baseweb="base-input"][data-disabled="true"], div[data-baseweb="select"] > div[aria-disabled="true"] {
                background-color: #F0F0F0 !important; border: 1px solid transparent !important;
            }
            div[data-baseweb="base-input"]:not([data-disabled="true"]), div[data-baseweb="select"] > div:not([aria-disabled="true"]) {
                background-color: #FFFFFF !important; border: 1px solid #D3D3D3 !important;
            }
            input, input:disabled, div[data-baseweb="select"] * {
                -webkit-text-fill-color: #000000 !important; color: #000000 !important; opacity: 1 !important;
            }
            div[data-testid="stAlert"] { background-color: #AA4F4E !important; border: none !important; }
            div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
                color: #FFFFFF !important; font-weight: 600 !important;
            }
            div[data-testid="stProgressBar"] > div > div { background-color: #526061 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
