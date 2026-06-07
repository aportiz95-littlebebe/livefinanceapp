import sys
import os
import streamlit as st

# --- PATH FIX FOR STREAMLIT CLOUD ---
# This forces the cloud server to recognize the root folder 
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- NOW DO THE LOCAL IMPORTS ---
from data.state import init_session_state
from ui.theme import apply_custom_theme
from ui.views import render_budget_dashboard, render_savings_dashboard
from ui.modals import (
    render_unified_income_splits_modal, 
    render_bills_modal, 
    render_category_modal, 
    render_ledger_modal, 
    render_combined_envelopes_modal, 
    render_savings_history_modal
)

# ... [the rest of your main.py code stays exactly the same below this] ...

# --- APP CONFIGURATION ---
st.set_page_config(page_title="My Finance Dashboard V15.0", layout="wide")

# --- INITIALIZE CORE ARCHITECTURE ---
init_session_state()
apply_custom_theme()

# --- EVALUATE OVERLAY TRIGGERS ---
if st.session_state.get('show_unified_modal', False): 
    st.session_state.show_unified_modal = False
    render_unified_income_splits_modal()

if st.session_state.get('show_bills_modal', False): 
    st.session_state.show_bills_modal = False
    render_bills_modal()

if st.session_state.get('show_cats_modal', False): 
    st.session_state.show_cats_modal = False
    render_category_modal()

if st.session_state.get('show_ledger_modal', False): 
    st.session_state.show_ledger_modal = False
    render_ledger_modal()

if st.session_state.get('show_sav_buckets_modal', False): 
    st.session_state.show_sav_buckets_modal = False
    render_combined_envelopes_modal()

if st.session_state.get('show_sav_history_modal', False): 
    st.session_state.show_sav_history_modal = False
    render_savings_history_modal()

# --- DASHBOARD UI ---
st.title("📊 My Finance Dashboard")
st.markdown("---")

tab_dashboard, tab_savings = st.tabs(["📊 Budget Dashboard", "💰 Savings & Goals Dashboard"])

with tab_dashboard:
    render_budget_dashboard()

with tab_savings:
    render_savings_dashboard()
