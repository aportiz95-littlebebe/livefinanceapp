import streamlit as st
import pandas as pd
from datetime import datetime

def init_session_state():
    """Initializes all baseline session state variables for the dashboard."""
    
    # =====================================================================
    # 🧪 TESTING CONTROLLER SWITCH
    # =====================================================================
    # Set this to True to automatically load your paychecks and transactions.
    # Set this to False to completely clear out mock numbers and go live.
    TESTING_MODE = FALSE 
    # =====================================================================

    # --- DataFrames ---
    if 'income_history' not in st.session_state:
        if TESTING_MODE:
            # Pre-populates your historical paychecks with your exact net amounts
            st.session_state.income_history = pd.DataFrame([
                {"Effective Date": datetime(2026, 1, 2).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 1, 16).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 1, 30).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 2, 13).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 2, 27).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 3, 13).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 3, 27).date(), "Amount": 1980.97},
                {"Effective Date": datetime(2026, 4, 10).date(), "Amount": 2073.69},
                {"Effective Date": datetime(2026, 4, 24).date(), "Amount": 2073.69},
                {"Effective Date": datetime(2026, 5, 8).date(), "Amount": 2073.69},
                {"Effective Date": datetime(2026, 5, 22).date(), "Amount": 2073.69},
                {"Effective Date": datetime(2026, 6, 5).date(), "Amount": 2073.69}
            ])
        else:
            st.session_state.income_history = pd.DataFrame(columns=["Effective Date", "Amount"])

    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Sub-Category", "Amount"])

    if 'savings_ledger' not in st.session_state:
        if TESTING_MODE:
            # Pre-populates your manual January 8th withdrawal transaction
            st.session_state.savings_ledger = pd.DataFrame([
                {
                    "Date": datetime(2026, 1, 8).date(),
                    "Fund": "Tuition",
                    "Type": "Withdrawal",
                    "Note": "Spring Term Payment",
                    "Amount": -3239.00
                }
            ])
        else:
            st.session_state.savings_ledger = pd.DataFrame(columns=["Date", "Fund", "Type", "Note", "Amount"])
    else:
        if "Fund" not in st.session_state.savings_ledger.columns:
            st.session_state.savings_ledger["Fund"] = "Unallocated Savings"

    # --- Budget Splits & Baselines ---
    if 'pct_split_needs' not in st.session_state: 
        st.session_state.pct_split_needs = 50.0 if TESTING_MODE else 0.0
    if 'pct_split_wants' not in st.session_state: 
        st.session_state.pct_split_wants = 20.0 if TESTING_MODE else 0.0  # Corrected to 20%
    if 'pct_split_savings' not in st.session_state: 
        st.session_state.pct_split_savings = 30.0 if TESTING_MODE else 0.0  # Corrected to 30%
        
    if 'starting_savings_balance' not in st.session_state: 
        st.session_state.starting_savings_balance = 0.0

    # --- Envelopes & Goals ---
    if 'bucket_config' not in st.session_state:
        if TESTING_MODE:
            # Sets up your Tuition envelope configuration automatically
            st.session_state.bucket_config = {
                "Tuition": {"initial": 4000.00, "pct": 50.0}
            }
        else:
            st.session_state.bucket_config = {}

    if 'bucket_targets' not in st.session_state:
        if TESTING_MODE:
            st.session_state.bucket_targets = {
                "Unallocated Savings": 0.0,
                "Tuition": 4000.00
            }
        else:
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
        st.session_state.next_payday = datetime(2026, 6, 19).date() if TESTING_MODE else datetime.now().date()
        
    if 'pay_frequency' not in st.session_state:
        st.session_state.pay_frequency = "Bi-weekly"

    if 'anchor_mode' not in st.session_state:
        st.session_state.anchor_mode = "First Payday of the Year" if TESTING_MODE else "Next Payday"
        
    if 'first_payday' not in st.session_state:
        st.session_state.first_payday = datetime(2026, 1, 2).date() if TESTING_MODE else datetime(datetime.now().year, 1, 1).date()
