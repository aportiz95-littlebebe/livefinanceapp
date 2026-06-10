import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
import json

def init_session_state():
    """Initializes all baseline session state variables for the dashboard."""
    
    if 'income_history' not in st.session_state:
        st.session_state.income_history = pd.DataFrame(columns=["Effective Date", "Amount"])

    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Sub-Category", "Amount"])

    if 'savings_ledger' not in st.session_state:
        st.session_state.savings_ledger = pd.DataFrame(columns=["Date", "Fund", "Type", "Note", "Amount"])
    else:
        if "Fund" not in st.session_state.savings_ledger.columns:
            st.session_state.savings_ledger["Fund"] = "Unallocated Savings"

    if 'pct_split_needs' not in st.session_state: st.session_state.pct_split_needs = 0.0
    if 'pct_split_wants' not in st.session_state: st.session_state.pct_split_wants = 0.0
    if 'pct_split_savings' not in st.session_state: st.session_state.pct_split_savings = 0.0
    if 'starting_savings_balance' not in st.session_state: st.session_state.starting_savings_balance = 0.0

    if 'bucket_config' not in st.session_state: st.session_state.bucket_config = {}
    if 'bucket_targets' not in st.session_state: st.session_state.bucket_targets = {"Unallocated Savings": 0.0}
    if 'savings_goals' in st.session_state: del st.session_state['savings_goals']

    if 'fixed_bills' not in st.session_state: st.session_state.fixed_bills = []
    if 'custom_categories' not in st.session_state: st.session_state.custom_categories = {}

    if 'next_payday' not in st.session_state: st.session_state.next_payday = date(2026, 6, 19)
    if 'pay_frequency' not in st.session_state: st.session_state.pay_frequency = "Bi-weekly"
    if 'anchor_mode' not in st.session_state: st.session_state.anchor_mode = "First Payday of the Year"
    if 'first_payday' not in st.session_state: st.session_state.first_payday = date(2026, 1, 1)

# --- GOOGLE SHEETS API INTEGRATION ---

def get_google_sheet():
    """Authenticates using Streamlit Secrets and connects to the sheet."""
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    return gc.open("LiveFinanceApp")

def load_data_from_google():
    """Pulls Data from Google Sheets and loads it into session state."""
    try:
        sheet = get_google_sheet()
        
        # 1. Load Expenses
        try:
            worksheet = sheet.worksheet("Expenses")
            records = worksheet.get_all_records()
            if records: 
                st.session_state.expenses = pd.DataFrame(records)
        except gspread.exceptions.WorksheetNotFound:
            pass

        # 2. Load Income
        try:
            worksheet = sheet.worksheet("Income")
            records = worksheet.get_all_records()
            if records: 
                st.session_state.income_history = pd.DataFrame(records)
        except gspread.exceptions.WorksheetNotFound:
            pass
            
        # 3. Load Savings
        try:
            worksheet = sheet.worksheet("Savings")
            records = worksheet.get_all_records()
            if records: 
                st.session_state.savings_ledger = pd.DataFrame(records)
        except gspread.exceptions.WorksheetNotFound:
            pass

        # 4. Load Config Settings
        try:
            worksheet = sheet.worksheet("Config")
            records = worksheet.get_all_records()
            for row in records:
                key = row.get("Key")
                val = row.get("Value", None)
                
                if key and val != "":
                    if isinstance(val, str):
                        try:
                            parsed_val = json.loads(val)
                        except json.JSONDecodeError:
                            parsed_val = val
                    else:
                        parsed_val = val
                    
                    # Convert date strings back into proper date objects safely
                    if key in ["first_payday", "next_payday"]:
                        if isinstance(parsed_val, str):
                            try:
                                # Strip any extra quotes or spacing if JSON stringified it weirdly
                                clean_str = parsed_val.replace('"', '').strip()
                                st.session_state[key] = datetime.strptime(clean_str, "%Y-%m-%d").date()
                            except ValueError:
                                # Fallback if formatting doesn't match perfectly
                                try:
                                    st.session_state[key] = datetime.fromisoformat(clean_str).date()
                                except ValueError:
                                    st.session_state[key] = parsed_val
                        elif isinstance(parsed_val, (int, float)):
                            pass # Keep default if it read as a number erroneously
                        else:
                            st.session_state[key] = parsed_val
                    else:
                        st.session_state[key] = parsed_val
                        
        except gspread.exceptions.WorksheetNotFound:
            pass
            
    except Exception as e:
        st.error(f"Fatal connection error: {e}")

def push_df_to_google(sheet_name, df):
    """Pushes a Pandas DataFrame to a specific Google Sheet tab."""
    try:
        sheet = get_google_sheet()
        try: worksheet = sheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound: worksheet = sheet.add_worksheet(title=sheet_name, rows="100", cols="20")
        
        df_safe = df.copy().astype(str)
        worksheet.clear()
        worksheet.update([df_safe.columns.values.tolist()] + df_safe.values.tolist())
    except Exception as e:
        st.toast(f"Sync failed for {sheet_name}", icon="🚫")

def push_config_to_google():
    """Serializes core configurations and saves them to the 'Config' tab."""
    try:
        sheet = get_google_sheet()
        try: worksheet = sheet.worksheet("Config")
        except gspread.exceptions.WorksheetNotFound: worksheet = sheet.add_worksheet(title="Config", rows="50", cols="2")
        
        # Convert date objects to strings safely for JSON serialization
        f_payday_str = st.session_state.first_payday.strftime("%Y-%m-%d") if isinstance(st.session_state.first_payday, date) else str(st.session_state.first_payday)
        n_payday_str = st.session_state.next_payday.strftime("%Y-%m-%d") if isinstance(st.session_state.next_payday, date) else str(st.session_state.next_payday)

        configs = [
            ["fixed_bills", json.dumps(st.session_state.fixed_bills)],
            ["custom_categories", json.dumps(st.session_state.custom_categories)],
            ["bucket_config", json.dumps(st.session_state.bucket_config)],
            ["bucket_targets", json.dumps(st.session_state.bucket_targets)],
            ["pct_split_needs", json.dumps(st.session_state.pct_split_needs)],
            ["pct_split_wants", json.dumps(st.session_state.pct_split_wants)],
            ["pct_split_savings", json.dumps(st.session_state.pct_split_savings)],
            ["starting_savings_balance", json.dumps(st.session_state.starting_savings_balance)],
            ["first_payday", json.dumps(f_payday_str)],  # ADDED TO SYNC ENGINE
            ["next_payday", json.dumps(n_payday_str)],    # ADDED TO SYNC ENGINE
            ["pay_frequency", json.dumps(st.session_state.pay_frequency)] # ADDED TO SYNC ENGINE
        ]
        
        worksheet.clear()
        worksheet.update([["Key", "Value"]] + configs)
    except Exception as e:
        st.toast("Config Sync Failed", icon="🚫")
