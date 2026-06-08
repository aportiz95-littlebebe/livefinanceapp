import streamlit as st

def apply_custom_theme():
    """Injects the custom hex color theme and CSS styling into the Streamlit app."""
    st.markdown(
        """
        <style>
            /* Main Page Background Canvas Override */
            .stApp, body, .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab-panel"] {
                background-color: #F5F7EC !important;
            }
            
            /* Text Color Baselines */
            span, label, .stApp p { color: #3A3A3A; }
            
            /* Section Headers and Title Banners */
            h3 {
                color: #3A3A3A !important; 
                background-color: #E0CEBA !important;
                padding: 10px 20px !important; 
                border-radius: 16px !important;
                display: inline-block !important; 
                margin-bottom: 14px !important;
                border: 1px solid rgba(255,255,255,0.4) !important;
                font-family: sans-serif !important;
            }
            
            /* Dynamic Boxes around Tab Layout Items Selector Header */
            .stTabs [data-baseweb="tab"] {
                background-color: #FFFFFF !important;
                border: 2px solid #F8ECDE !important;
                border-radius: 8px !important;
                padding: 6px 16px !important;
                margin-right: 6px !important;
                font-weight: 700 !important;
            }
            
            /* Handle active/selected Tab highlight states cleanly */
            .stTabs [aria-selected="true"] {
                background-color: #F8ECDE !important;
                color: #3A3A3A !important;
            }
            
            /* Text Boxes, Data Grid Containers, and Metric Cards Wrapper */
            div[data-testid="stExpander"], div[data-testid="stForm"], 
            .stDataEditor, div[data-testid="stMetricContainer"] {
                background-color: #E0CEBA !important; 
                border-radius: 10px !important;
                padding: 16px !important; 
                border: 1px solid rgba(0,0,0,0.04) !important;
            }
            
            /* Standard Functional Dashboard Buttons Styling Controls */
            div.stButton > button {
                background-color: #959B75 !important; 
                border: none !important;
                border-radius: 10px !important; 
                padding: 8px 22px !important;
                transition: all 0.2s ease-in-out !important;
            }
            div.stButton > button p {
                color: #FFFFFF !important; 
                font-size: 13px !important;
                font-weight: 700 !important; 
                font-family: sans-serif !important;
                letter-spacing: 0.4px !important; 
                margin: 0px !important;
            }
            div.stButton > button:hover, div.stButton > button:active {
                background-color: #828863 !important; 
                box-shadow: 0px 4px 8px rgba(0,0,0,0.1) !important;
            }
            
            /* Layout formatting normalization tweaks for nested column widgets */
            div[role="dialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5) div.stButton > button,
            div[role="dialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(6) div.stButton > button {
                transform: scale(0.85) !important;
            }
            
            /* Disabled Input Form Fields Styling Structure */
            div[data-baseweb="base-input"][data-disabled="true"], div[data-baseweb="select"] > div[aria-disabled="true"] {
                background-color: #ECEAE1 !important; 
                border: 1px solid rgba(0,0,0,0.05) !important;
            }
            
            /* Active Interactive Data Entry Fields Styling Structure */
            div[data-baseweb="base-input"]:not([data-disabled="true"]), div[data-baseweb="select"] > div:not([aria-disabled="true"]) {
                background-color: #FFFFFF !important; 
                border: 1px solid #C4B5A5 !important;
            }
            
            /* Global typography layout text-fill parameter forcing overrides */
            input, input:disabled, div[data-baseweb="select"] * {
                -webkit-text-fill-color: #1A1A1A !important; 
                color: #1A1A1A !important; 
                opacity: 1 !important;
            }
            
            /* Errors and Warning / Alerts Boxes Spec Blocks */
            div[data-testid="stAlert"] { 
                background-color: #8B3131 !important; 
                border: none !important; 
                border-radius: 8px !important;
            }
            div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
                color: #FFFFFF !important; 
                font-weight: 600 !important;
            }
            
            /* Financial Progress Bar custom thematic mapping fills */
            div[data-testid="stProgressBar"] > div > div { 
                background-color: #959B75 !important; 
            }
        </style>
        """,
        unsafe_allow_html=True
    )
