import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from data.state import push_df_to_google
from core.calculations import (
    get_period_dates, 
    get_income_for_date, 
    calculate_ytd_savings, 
    calculate_ytd_income,
    process_bills_for_period, 
    compute_budget_metrics,
    project_payday_cadence,
    calculate_bucket_balances,
    calculate_goal_timeline
)

def render_budget_dashboard():
    st.markdown("### Budget Dashboard")
    
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2.0, 1.5, 1.8, 2.2])
    with ctrl_col1:
        if st.button("💰 Edit Income & Budgets", use_container_width=True, key="main_tab_unified_btn"): 
            st.session_state.temp_income_history = st.session_state.income_history.copy()
            st.session_state.temp_pct_split_needs = st.session_state.pct_split_needs
            st.session_state.temp_pct_split_wants = st.session_state.pct_split_wants
            st.session_state.temp_pct_split_savings = st.session_state.pct_split_savings
            st.session_state.temp_next_payday = st.session_state.next_payday
            st.session_state.temp_pay_frequency = st.session_state.pay_frequency
            st.session_state.temp_anchor_mode = st.session_state.anchor_mode
            st.session_state.temp_first_payday = st.session_state.first_payday
            st.session_state.temp_starting_savings_balance = st.session_state.starting_savings_balance
            st.session_state.show_unified_modal = True
            st.rerun()
    with ctrl_col2:
        if st.button("📋 Edit Bills", use_container_width=True, key="main_tab_bills_btn"): 
            st.session_state.temp_fixed_bills = [dict(bill) for bill in st.session_state.fixed_bills]
            st.session_state.show_bills_modal = True
            st.rerun()
    with ctrl_col3:
        if st.button("⚙️ Edit Expense Types", use_container_width=True, key="main_tab_cats_btn"): 
            st.session_state.temp_custom_categories = dict(st.session_state.custom_categories)
            st.session_state.show_cats_modal = True
            st.rerun()
    with ctrl_col4:
        if st.button("📜 View Transaction History", use_container_width=True, key="main_tab_ledger_btn"): 
            st.session_state.show_ledger_modal = True
            st.rerun()

    st.markdown("---")

    today = datetime.now().date()
    interval_days = 7 if st.session_state.pay_frequency == "Weekly" else (30 if st.session_state.pay_frequency == "Monthly" else 14)
    anchor_date = st.session_state.first_payday if st.session_state.anchor_mode in ["First Payday of the Year", "Manual Entry"] else st.session_state.next_payday

    current_period_start, current_period_end, next_period_start, next_period_end = get_period_dates(anchor_date, interval_days, today)
    current_income = get_income_for_date(st.session_state.income_history, today)

    metrics = compute_budget_metrics(
        current_income=current_income,
        pct_needs=st.session_state.pct_split_needs,
        pct_wants=st.session_state.pct_split_wants,
        expenses_df=st.session_state.expenses,
        fixed_bills=st.session_state.fixed_bills,
        current_start=current_period_start,
        current_end=current_period_end
    )

    next_bills_total, next_formatted_bills_list = process_bills_for_period(st.session_state.fixed_bills, next_period_start, next_period_end)

    dash_top_left, dash_top_mid, dash_top_right = st.columns([1.5, 1.2, 1.2])
    with dash_top_left:
        st.markdown("### 💸 Budget Overview")
        st.metric(label="Current Base Pay", value=f"${current_income:,.2f}")
        
        ytd_earned = calculate_ytd_income(st.session_state.income_history, today)
        st.metric(label="📈 Salary Earned YTD", value=f"${ytd_earned:,.2f}")
            
        st.metric(label=f"Needs Budget ({st.session_state.pct_split_needs:,.0f}%)", value=f"${metrics['needs_target']:,.2f}")
        st.metric(label=f"Wants Budget ({st.session_state.pct_split_wants:,.0f}%)", value=f"${metrics['wants_target']:,.2f}")
        st.metric(label=f"Savings Budget ({st.session_state.pct_split_savings:,.0f}%)", value=f"${current_income * (st.session_state.pct_split_savings / 100.0):,.2f}")

    with dash_top_mid:
        st.markdown("### 📅 Bills Due This Pay Period")
        st.caption(f"Pay Period: **{current_period_start.strftime('%b %d')}** to **{current_period_end.strftime('%b %d')}**")
        if metrics['bills_bullets']:
            for bullet in metrics['bills_bullets']: st.markdown(bullet)
            st.markdown(f"**Total Amount Due: ${metrics['bills_total']:,.2f}**")
            if metrics['needs_overage'] > 0: 
                st.error(f"⚠️ Your bills exceed your {st.session_state.pct_split_needs:,.0f}% budget by **${metrics['needs_overage']:,.2f}**")
        else: st.success("No bills scheduled in this paycheck block.")

    with dash_top_right:
        st.markdown("### 🔮 Bills Due Next Pay Period")
        st.caption(f"Pay Period: **{next_period_start.strftime('%b %d')}** to **{next_period_end.strftime('%b %d')}**")
        if next_formatted_bills_list:
            for bullet in next_formatted_bills_list: st.markdown(bullet)
            st.markdown(f"**Total Amount Due: ${next_bills_total:,.2f}**")
            
            # --- NEW LOOK-AHEAD WARNING LOGIC ---
            next_income = get_income_for_date(st.session_state.income_history, next_period_start)
            next_needs_target = next_income * (st.session_state.pct_split_needs / 100.0)
            next_needs_overage = next_bills_total - next_needs_target
            
            if next_needs_overage > 0:
                st.warning(f"⚠️ Heads up! These bills will exceed your {st.session_state.pct_split_needs:,.0f}% Needs budget by **${next_needs_overage:,.2f}**")
            # ------------------------------------
            
        else: st.success("No bills scheduled in the next block.")

    st.markdown("---")
    
    side_col_form, side_col_progress = st.columns([1.1, 0.9])
    with side_col_form:
        st.subheader("📝 Log a Transaction")
        category_options = list(st.session_state.custom_categories.keys())
        log_col1, log_col2 = st.columns([1, 1])
        with log_col1: exp_date = st.date_input("Transaction Date", value=today, key="main_log_date")
        with log_col2: 
            if category_options: selected_type = st.selectbox("Type", category_options, key="main_log_type")
            else:
                st.info("Add categories first")
                selected_type = None
                
        exp_desc = st.text_input("Where / Description", placeholder="e.g., Kroger, Shell", key="main_log_desc")
        exp_amt = st.number_input("Amount ($)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="main_log_amt")
        if st.button("Add Transaction", use_container_width=True, key="main_log_submit_btn", disabled=not selected_type):
            if exp_desc and exp_amt > 0 and selected_type:
                assigned_bucket = st.session_state.custom_categories[selected_type]
                final_amt = exp_amt if assigned_bucket != "Extra Income" else -exp_amt
                new_row = pd.DataFrame([{"Date": exp_date.strftime("%Y-%m-%d"), "Description": exp_desc, "Category": assigned_bucket, "Sub-Category": selected_type, "Amount": final_amt}])
                
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
                push_df_to_google("Expenses", st.session_state.expenses)
                st.rerun()
                
    with side_col_progress:
        st.subheader("📊 Budget Progress")
        st.write(f"**Wants Budget:** Spent ${metrics['wants_spent']:,.2f} of ${metrics['effective_wants_target']:,.2f}")
        st.progress(metrics['wants_ratio'])
        st.write(f"👉 *Wants Remaining:* **${metrics['wants_remaining']:,.2f}**")
        if metrics['needs_overage'] > 0: st.caption(f"⚠️ *Fun money shrunk by **${metrics['needs_overage']:,.2f}** to patch Needs overages.*")
        st.write("---")
        st.write(f"**Needs Budget:** Spent ${metrics['total_needs_burden']:,.2f} of ${metrics['needs_target']:,.2f}")
        st.progress(metrics['needs_ratio'])
        st.write(f"👉 *Needs Remaining:* **${metrics['needs_remaining']:,.2f}**")
        if metrics['needs_remaining'] > 0:
            st.success(f"💡 End-of-period sweep potential: **${metrics['needs_remaining']:,.2f}** to savings!")

    st.markdown("---")
    st.subheader("📅 Monthly Bill Calendar")
    year, month = today.year, today.month
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    bill_map = {}
    for bill in st.session_state.fixed_bills:
        if bill["Amount"] > 0: bill_map.setdefault(bill["Due Day"], []).append(f"{bill['Name']} (${bill['Amount']:,.2f})")

    projected_paydays = project_payday_cadence(st.session_state.first_payday, st.session_state.pay_frequency, year)

    html_cal = f'<table style="width:100%; border-collapse:collapse; font-family:sans-serif; table-layout:fixed;"><tr>'
    for day_name in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]: html_cal += f'<th style="background-color:rgba(0,0,0,0.05); padding:10px; border:1px solid rgba(0,0,0,0.1);">{day_name}</th>'
    html_cal += '</tr>'
    
    for week in month_days:
        html_cal += "<tr>"
        for day in week:
            if day == 0: html_cal += '<td style="background-color:rgba(0,0,0,0.02); border:1px solid rgba(0,0,0,0.1); height:115px;"></td>'
            else:
                is_today = "background-color:rgba(124,179,66,0.2); border:2px solid #7cb342;" if (day == today.day and month == today.month) else "background-color:rgba(255,255,255,0.4); border:1px solid rgba(0,0,0,0.1);"
                html_cal += f'<td style="{is_today} height:115px; vertical-align:top; padding:0px;">'
                
                current_cal_date = datetime(year, month, day).date()
                if st.session_state.first_payday is not None and current_cal_date in projected_paydays: 
                    html_cal += '<span style="background-color:#2e7d32; color:white; font-size:11px; font-weight:bold; padding:3px 8px; display:block;">💰 Payday!</span>'
                
                html_cal += f'<div style="padding:8px;"><span style="font-weight:bold; font-size:14px; color:#555;">{day}</span>'
                if day in bill_map:
                    for tag in bill_map[day]: html_cal += f'<span style="background-color:#ffeef0; color:#b71c1c; font-size:11px; padding:3px 6px; margin:2px 0; border-radius:4px; display:block; border-left:3px solid #e53935;">{tag}</span>'
                html_cal += '</div></td>'
        html_cal += "</tr>"
    st.markdown(html_cal + "</table>", unsafe_allow_html=True)


def render_savings_dashboard():
    st.subheader("💰 Savings & Goals Dashboard")
    
    sav_ctrl_col1, sav_ctrl_col2, sav_ctrl_spacer = st.columns([2.5, 2.0, 5.5])
    with sav_ctrl_col1:
        if st.button("🛠️ Edit Buckets & Goals", use_container_width=True, key="btn_buck_conf_v123"): 
            st.session_state.temp_bucket_config = {k: dict(v) for k, v in st.session_state.bucket_config.items()}
            st.session_state.temp_bucket_targets = dict(st.session_state.bucket_targets)
            st.session_state.show_sav_buckets_modal = True
            st.rerun()
    with sav_ctrl_col2:
        if st.button("📜 View Savings History", use_container_width=True, key="btn_ledger_view_v123"): 
            st.session_state.show_sav_history_modal = True
            st.rerun()
            
    st.markdown("---")

    today = datetime.now().date()
    interval_days = 7 if st.session_state.pay_frequency == "Weekly" else (30 if st.session_state.pay_frequency == "Monthly" else 14)
    current_income = get_income_for_date(st.session_state.income_history, today)
    savings_target = current_income * (st.session_state.pct_split_savings / 100.0)

    bucket_balances, allocated_total, unassigned_pct, unassigned_ledger = calculate_bucket_balances(st.session_state.bucket_config, st.session_state.savings_ledger)
    accumulated_payday_savings, accumulated_payday_savings_ytd = calculate_ytd_savings(st.session_state.income_history, st.session_state.pct_split_savings, today)

    df_sav = st.session_state.savings_ledger.copy()
    manual_deposits_total = df_sav[df_sav["Type"] != "Auto-Deposit"]["Amount"].sum() if not df_sav.empty else 0.0
    net_total_savings = st.session_state.starting_savings_balance + accumulated_payday_savings + manual_deposits_total
    
    unassigned_bal = net_total_savings - allocated_total
    total_background_auto = df_sav[df_sav["Type"] == "Auto-Deposit"]["Amount"].sum() if not df_sav.empty else 0.0

    workspace_col_left, workspace_col_right = st.columns([1.1, 1.4])
    
    with workspace_col_left:
        st.markdown("### 📊 Savings Overview")
        st.metric(label="🏦 Grand Total Savings", value=f"${net_total_savings:,.2f}", delta=f"+${total_background_auto:,.2f} via Auto-Payday")
        st.write(" ") 
        st.metric(label="📈 Savings Deposited YTD", value=f"${accumulated_payday_savings_ytd:,.2f}")
        
        st.markdown("---")
        st.markdown("### 📥 Log Savings Activity")
        
        def process_sav_transaction():
            sav_amt = st.session_state["sav_amt_v124"]
            if sav_amt > 0:
                t_type = st.session_state["sav_type_v124"]
                final_amt = -sav_amt if t_type == "Withdrawal" else sav_amt
                
                new_row = pd.DataFrame([{
                    "Date": st.session_state["sav_date_input_v124"].strftime("%Y-%m-%d"),
                    "Fund": st.session_state["savings_dropdown_v124"],
                    "Type": t_type,
                    "Note": st.session_state["sav_note_v124"],
                    "Amount": final_amt
                }])
                st.session_state.savings_ledger = pd.concat([st.session_state.savings_ledger, new_row], ignore_index=True)
                push_df_to_google("Savings", st.session_state.savings_ledger)
                
                st.session_state["savings_dropdown_v124"] = "Unallocated Savings"
                st.session_state["sav_type_v124"] = "Extra Deposit"
                st.session_state["sav_note_v124"] = ""
                st.session_state["sav_amt_v124"] = 0.0

        sav_input_col1, sav_input_col2 = st.columns(2)
        with sav_input_col1: st.date_input(label="Date", value=today, key="sav_date_input_v124")
        with sav_input_col2: 
            fund_opts = ["Unallocated Savings"] + list(st.session_state.bucket_config.keys())
            st.selectbox(label="Target Bucket", options=fund_opts, key="savings_dropdown_v124")
        
        st.selectbox(label="Transaction Type", options=["Extra Deposit", "Withdrawal"], key="sav_type_v124")
        st.text_input(label="Memo / Note", value="", key="sav_note_v124")
        st.number_input(label="Amount ($)", min_value=0.0, value=0.0, step=50.0, format="%.2f", key="sav_amt_v124")
            
        st.button("Add Transaction", use_container_width=True, on_click=process_sav_transaction)

    with workspace_col_right:
        st.markdown("### 🎯 Savings Buckets & Target Goals")
        st.markdown("Review current Bucket amounts.")
        st.write(" ")
        
        all_tracking_buckets = list(st.session_state.bucket_targets.keys())
        
        for b_name in all_tracking_buckets:
            st.markdown(f"#### 💼 {b_name}")
            
            if b_name == "Unallocated Savings":
                cur_bal = unassigned_bal
                flow_pct = unassigned_pct
            elif b_name in bucket_balances:
                cur_bal = bucket_balances[b_name]
                flow_pct = float(st.session_state.bucket_config[b_name].get("pct", 0.0))
            else:
                cur_bal = 0.0
                flow_pct = 0.0
                
            biweekly_flow = savings_target * (flow_pct / 100.0)
            target_val = st.session_state.bucket_targets.get(b_name, 0.0)
            
            col1, col2, col3, col4 = st.columns([1.0, 1.0, 1.0, 1.5])
            
            with col1: st.metric("Overall Amount", f"${cur_bal:,.2f}")
            with col2: st.metric("Goal Name", f"${target_val:,.2f}")
            with col3:
                if target_val > 0:
                    remaining = target_val - cur_bal
                    if remaining <= 0: st.metric("Remaining to Reach", "$0.00")
                    else: st.metric("Remaining to Reach", f"${remaining:,.2f}")
                else: st.caption("No target set.")
                    
            with col4:
                if target_val > 0:
                    remaining = target_val - cur_bal
                    if remaining <= 0: st.success("✨ Fully Funded!")
                    else:
                        paychecks_req, accomplish_date = calculate_goal_timeline(remaining, biweekly_flow, st.session_state.next_payday, interval_days, today)
                        if paychecks_req and accomplish_date:
                            st.write(f"**Timeline:** ~{paychecks_req} checks")
                            st.write(f"📆 *Est:* **{accomplish_date.strftime('%b %d, %Y')}**")
                        else: st.write("**Timeline:** Manual Only")
                else: st.caption("Adjust tracking timelines inside setup settings.")
                    
            if target_val > 0:
                prog_ratio = min(max(cur_bal / target_val, 0.0), 1.0)
                st.progress(prog_ratio)
                
            st.markdown("---")
