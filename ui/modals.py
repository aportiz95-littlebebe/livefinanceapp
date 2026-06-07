import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

@st.dialog("💰 Edit Income & Budgets", width="large")
def render_unified_income_splits_modal():
    # Sync modal state persistence
    if 'temp_pct_split_needs' not in st.session_state: st.session_state.temp_pct_split_needs = st.session_state.pct_split_needs
    if 'temp_pct_split_wants' not in st.session_state: st.session_state.temp_pct_split_wants = st.session_state.pct_split_wants
    if 'temp_pct_split_savings' not in st.session_state: st.session_state.temp_pct_split_savings = st.session_state.pct_split_savings

    df_temp = st.session_state.temp_income_history.copy()
    if not df_temp.empty:
        df_temp['Effective Date'] = pd.to_datetime(df_temp['Effective Date']).dt.date
        past = df_temp[df_temp['Effective Date'] <= datetime.now().date()]
        active_pay = float(past.sort_values(by='Effective Date', ascending=False).iloc[0]['Amount']) if not past.empty else 0.00
    else:
        active_pay = 0.00

    st.markdown("### Base Pay & Timeline Setup")
    st.caption("Configure your paycheck amount, schedule, and timeline anchor.")
    
    col_inputs, col_ledger = st.columns([1.0, 1.2])
    past_dates_df = pd.DataFrame() 
    
    with col_inputs:
        new_pay = st.number_input("Paycheck Base Amount ($)", min_value=0.0, value=float(active_pay), step=50.0, format="%.2f")
        new_starting_savings = st.number_input("What was your starting amount in Savings at the start of the year?", value=float(st.session_state.get("temp_starting_savings_balance", 0.0)), step=100.0, format="%.2f")
        new_freq = st.text_input("How frequently do you get paid?", value="Bi-weekly", disabled=True)
        
        opts = ["Next Payday", "First Payday of the Year", "Manual Entry"]
        active_idx = opts.index(st.session_state.temp_anchor_mode) if st.session_state.temp_anchor_mode in opts else 0
        new_anchor = st.radio("Would you like to start your budget allocations with your upcoming paycheck, start of the year, or enter them manually?", opts, index=active_idx)
        
        int_val = 14
        if new_anchor == "Next Payday":
            new_payday = st.date_input("When is your next pay day?", value=st.session_state.temp_next_payday)
            calc_date = new_payday
            target_year = datetime.now().year
            while calc_date.year > target_year: calc_date -= timedelta(days=int_val)
            while (calc_date - timedelta(days=int_val)).year == target_year: calc_date -= timedelta(days=int_val)
            p_dates = [{"Effective Date": (calc_date + timedelta(days=i*int_val)), "Amount": float(new_pay)} for i in range(10) if (calc_date + timedelta(days=i*int_val)) <= datetime.now().date()]
            past_dates_df = pd.DataFrame(p_dates)
        elif new_anchor == "First Payday of the Year":
            new_first_payday = st.date_input("When was your first pay day this year?", value=st.session_state.temp_first_payday)
            p_dates = [{"Effective Date": (new_first_payday + timedelta(days=i*int_val)), "Amount": float(new_pay)} for i in range(26) if (new_first_payday + timedelta(days=i*int_val)) <= datetime.now().date()]
            past_dates_df = pd.DataFrame(p_dates)
            
    with col_ledger:
        st.markdown("<h5 style='margin-top:0; padding-top:0;'>Historical Timeline Ledger</h5>", unsafe_allow_html=True)
        display_df = df_temp.copy()
        if not past_dates_df.empty:
            display_df = pd.concat([display_df, past_dates_df], ignore_index=True).drop_duplicates(subset=['Effective Date'], keep='last').sort_values('Effective Date')
            
        edited_inc_df = st.data_editor(display_df, use_container_width=True, num_rows="dynamic", key="income_inline_grid_editor")
        
        if st.button("Save Ledger Edits", use_container_width=True):
            st.session_state.temp_pct_split_needs = st.session_state.val_needs_input # Ensure sync
            st.session_state.temp_pct_split_wants = st.session_state.val_wants_input
            st.session_state.temp_pct_split_savings = st.session_state.val_savings_input
            st.session_state.temp_income_history = edited_inc_df.sort_values(by='Effective Date').reset_index(drop=True)
            st.session_state.show_unified_modal = True
            st.rerun()
            
    st.markdown("---")
    modal_left_inputs, modal_right_preview = st.columns([1.0, 1.0])
    with modal_left_inputs:
        st.markdown("### Budget Allocations")
        val_needs = st.number_input("Needs:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_needs), step=5.0, key="val_needs_input")
        val_wants = st.number_input("Wants:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_wants), step=5.0, key="val_wants_input")
        val_savings = st.number_input("Savings:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_savings), step=5.0, key="val_savings_input")
    with modal_right_preview:
        st.markdown("### Active Budget Preview")
        st.metric(label="Needs Budget", value=f"${new_pay * (val_needs / 100.0):,.2f}")
        st.metric(label="Wants Budget", value=f"${new_pay * (val_wants / 100.0):,.2f}")
        st.metric(label="Savings Budget", value=f"${new_pay * (val_savings / 100.0):,.2f}")
        
    if val_needs + val_wants + val_savings == 100.0 or (val_needs == 0 and val_wants == 0 and val_savings == 0):
        if st.button("💾 Save Changes", use_container_width=True):
            final_df = edited_inc_df.dropna(subset=['Effective Date']).sort_values('Effective Date')
            
            # Generate Savings Ledger Auto-Deposits
            st.session_state.savings_ledger = st.session_state.savings_ledger[st.session_state.savings_ledger["Type"] != "Auto-Deposit"]
            new_sav_rows = []
            for _, row in final_df[final_df['Effective Date'] <= datetime.now().date()].iterrows():
                sav_pool = float(row['Amount']) * (val_savings / 100.0)
                for b_name, b_data in st.session_state.bucket_config.items():
                    if (dep := sav_pool * (float(b_data.get("pct", 0.0)) / 100.0)) > 0:
                        new_sav_rows.append({"Date": row['Effective Date'], "Fund": b_name, "Type": "Auto-Deposit", "Note": "Payday Allocation", "Amount": dep})
            
            if new_sav_rows:
                st.session_state.savings_ledger = pd.concat([st.session_state.savings_ledger, pd.DataFrame(new_sav_rows)], ignore_index=True)

            st.session_state.income_history, st.session_state.pct_split_needs, st.session_state.pct_split_wants, st.session_state.pct_split_savings = final_df, val_needs, val_wants, val_savings
            st.session_state.next_payday, st.session_state.first_payday, st.session_state.starting_savings_balance = new_payday, new_first_payday, new_starting_savings
            st.rerun()
    else:
        st.error("Percentages must sum to 100%.")

# ... [Keep rest of your render functions (render_bills_modal, etc.) unchanged below] ...
