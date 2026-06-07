import streamlit as st
from data.state import init_session_state
from ui.theme import apply_custom_theme
from ui.views import render_budget_dashboard, render_savings_dashboard
from ui.modals import (
    render_unified_income_splits_modal, render_bills_modal, 
    render_category_modal, render_ledger_modal, 
    render_combined_envelopes_modal, render_savings_history_modal
)

st.set_page_config(page_title="My Finance Dashboard V15.0", layout="wide")
init_session_state()
apply_custom_theme()

# --- TRIGGER OVERLAYS ---
if st.session_state.get('show_unified_modal', False): st.session_state.show_unified_modal = False; render_unified_income_splits_modal()
if st.session_state.get('show_bills_modal', False): st.session_state.show_bills_modal = False; render_bills_modal()
if st.session_state.get('show_cats_modal', False): st.session_state.show_cats_modal = False; render_category_modal()
if st.session_state.get('show_ledger_modal', False): st.session_state.show_ledger_modal = False; render_ledger_modal()
if st.session_state.get('show_sav_buckets_modal', False): st.session_state.show_sav_buckets_modal = False; render_combined_envelopes_modal()
if st.session_state.get('show_sav_history_modal', False): st.session_state.show_sav_history_modal = False; render_savings_history_modal()

st.title("📊 My Finance Dashboard")
tab_dashboard, tab_savings = st.tabs(["📊 Budget Dashboard", "💰 Savings & Goals Dashboard"])

with tab_dashboard:
    render_budget_dashboard()
with tab_savings:
    render_savings_dashboard()
