import sys
import os
import streamlit as st

# --- PATH FIX FOR STREAMLIT CLOUD ---
# This forces the cloud server to recognize the root folder 
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- FOLDER IMPORTS ---
from data.state import init_session_state, load_data_from_google
from ui.theme import apply_custom_theme
from ui.views import render_budget_dashboard, render_savings_dashboard
from ui.modals import (
    render_unified_income_splits_modal, 
    render_bills_modal, 
    render_category_modal, 
    render_ledger_modal, 
    render_combined_envelopes_modal, 
    render_savings_history_modal,
    render_savings_account_modal # Ensures the new dialog is imported cleanly
)

# --- APP CONFIGURATION ---
st.set_page_config(page_title="My Finance Dashboard V15.0", layout="wide")

# --- INITIALIZE CORE ARCHITECTURE ---
init_session_state()

# --- FETCH GOOGLE DATA (Only runs once per session) ---
if 'google_data_loaded' not in st.session_state:
    load_data_from_google()
    st.session_state.google_data_loaded = True

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

# Active overlay execution block for your new savings profile window
if st.session_state.get('show_savings_account_modal', False):
    st.session_state.show_savings_account_modal = False
    render_savings_account_modal()

# --- DASHBOARD UI ---
st.title("📊 My Finance Dashboard")
st.markdown("---")

# ADDED THIRD OPTION TO TABS LIST HERE
tab_dashboard, tab_savings, tab_projections = st.tabs([
    "📊 Budget Dashboard", 
    "💰 Savings & Goals Dashboard", 
    "🔮 Savings Projections"
])

with tab_dashboard:
    render_budget_dashboard()

with tab_savings:
    render_savings_dashboard()

# EXECUTE CHRONOLOGICAL SIMULATOR RENDER LOOP
with tab_projections:
    from ui.views import render_projection_dashboard
    render_projection_dashboard()
