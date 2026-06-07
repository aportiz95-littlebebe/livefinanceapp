import streamlit as st
import pandas as pd
from datetime import datetime

def init_session_state():
    """Initializes all baseline session state variables for the dashboard."""
    
    # --- DataFrames ---
    if 'income_history' not in st.session_state:
        st.session_state.income_history = pd.DataFrame(columns=["Effective Date", "Amount"])

    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Sub-Category", "Amount"])

    if 'savings_ledger' not in st.session_state:
        st.session_state.savings_ledger = pd.DataFrame(columns=["Date", "Fund", "Type", "Note", "Amount"])
    else:
        if "Fund" not in st.session_state.savings_ledger.columns:
            st.session_state.savings_ledger["Fund"] = "Unallocated Savings"

    # --- Budget Splits & Baselines ---
    if 'pct_split_needs' not in st.session_state: st.session_state.pct_split_needs = 0.0
    if 'pct_split_wants' not in st.session_state: st.session_state.pct_split_wants = 0.0
    if 'pct_split_savings' not in st.session_state: st.session_state.pct_split_savings = 0.0
    if 'starting_savings_balance' not in st.session_state: st.session_state.starting_savings_balance = 0.0

    # --- Envelopes & Goals ---
    if 'bucket_config' not in st.session_state:
        st.session_state.bucket_config = {}

    if 'bucket_targets' not in st.session_state:
        st.session_state.bucket_targets = {
            "Unallocated Savings": 0.0
        }
        
    if 'savings_goals' in st.session_state:
        del st.session_state['savings_goals']

    # --- Lists & Dictionaries ---
    if 'fixed_bills' not in st.session_state:
        st.session_state.fixed_bills = []

    if 'custom_categories' not in st.session_state:
        st.session_state.custom_categories = {}

    # --- Timeline Anchors ---
    if 'next_payday' not in st.session_state:
        st.session_state.next_payday = datetime.now().date()
        
    if 'pay_frequency' not in st.session_state:
        st.session_state.pay_frequency = "Bi-weekly"

    if 'anchor_mode' not in st.session_state:
        st.session_state.anchor_mode = "Next Payday"
        
    if 'first_payday' not in st.session_state:
        st.session_state.first_payday = datetime(datetime.now().year, 1, 1).date()
