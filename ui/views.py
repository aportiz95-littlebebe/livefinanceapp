import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date, timedelta
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
            st.session_state.first_payday = st.session_state.get('first_payday', date(2026,1,1))
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
    anchor_date = st.session_state.first_payday if st.session_state.get('first_payday') else today

    current_period_start, current_period_end, next_period_start, next_period_end = get_period_dates(anchor_date, interval_days, today)
    
    # Budgets are structurally locked onto your configured steady Base Pay
    current_income = st.session_state.get("base_pay", 0.0)

    metrics = compute_budget_metrics(
        current_income=current_income,
        pct_needs=st.session_state.pct_split_needs,
        pct_wants=st.session_state.pct_split_wants,
        expenses_df=st.session_state.expenses,
        fixed_bills=st.session_state.fixed_bills,
        current_start=current_period_start,
        current_end=current_period_end
    )

    next_bills_total, next_formatted_bullets_list = process_bills_for_period(st.session_state.fixed_bills, next_period_start, next_period_end)

    dash_top_left, dash_top_mid, dash_top_right = st.columns([1.5, 1.2, 1.2])
    with dash_top_left:
        st.markdown("### 💸 Budget Overview")
        st.metric(label="Current Base Pay Baseline", value=f"${current_income:,.2f}")
        
        ytd_earned = calculate_ytd_income(st.session_state.income_history, today)
        st.metric(label="📈 Total Salary Earned YTD", value=f"${ytd_earned:,.2f}")
            
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
        if next_formatted_bullets_list:
            for bullet in next_formatted_bullets_list: st.markdown(bullet)
            st.markdown(f"**Total Amount Due: ${next_bills_total:,.2f}**")
            
            next_needs_target = current_income * (st.session_state.pct_split_needs / 100.0)
            next_needs_overage = next_bills_total - next_needs_target
            
            if next_needs_overage > 0:
                st.error(f"⚠️ Heads up! These bills will exceed your {st.session_state.pct_split_needs:,.0f}% Needs budget by **${next_needs_overage:,.2f}**")
        else: st.success("No bills scheduled in the next block.")

    st.markdown("---")
    
    side_col_form, side_col_progress = st.columns([1.1, 0.9])
    with side_col_form:
        st.subheader("📝 Log Paycheck or Transaction")
        entry_mode = st.radio("What are you logging?", ["Expense / Transaction", "💰 Received Paycheck"], horizontal=True)
        
        if entry_mode == "💰 Received Paycheck":
            pay_date = st.date_input("Pay Date", value=today, key="manual_inc_date")
            pay_amt = st.number_input("Actual Net Paycheck Amount Received ($)", min_value=0.0, value=float(current_income), step=100.0, format="%.2f", key="manual_inc_amt")
            
            if st.button("🚀 Log Paycheck & Distribute Savings", use_container_width=True):
                if pay_amt > 0:
                    # 1. Write the absolute manual paycheck to the Income history ledger
                    new_inc = pd.DataFrame([{"Effective Date": pay_date.strftime("%Y-%m-%d"), "Amount": pay_amt}])
                    st.session_state.income_history = pd.concat([st.session_state.income_history, new_inc], ignore_index=True)
                    push_df_to_google("Income", st.session_state.income_history)
                    
                    # 2. RUN BASE PAY ALLOCATIONS VS. GAS SURPLUS ROUTING
                    base_pay_pool = current_income * (st.session_state.pct_split_savings / 100.0)
                    new_ledger_rows = []
                    
                    # Calculate current balances so we know if a bucket is already full
                    current_balances, _, _, _ = calculate_bucket_balances(st.session_state.bucket_config, st.session_state.savings_ledger)
                    total_spillover = 0.0
                    
                    # Distribute regular savings percentage based strictly on core base pay
                    for b_name, b_data in st.session_state.bucket_config.items():
                        b_pct = float(b_data.get("pct", 0.0))
                        b_overflow = bool(b_data.get("overflow", False))
                        b_target = st.session_state.bucket_targets.get(b_name, 0.0)
                        
                        if (dep := base_pay_pool * (b_pct / 100.0)) > 0:
                            actual_dep = dep
                            
                            # Trigger Spillover logic if the setting is checked and a target exists
                            if b_overflow and b_target > 0:
                                current_bal = current_balances.get(b_name, 0.0)
                                room_left = max(0.0, b_target - current_bal)
                                
                                # If the incoming deposit is larger than the room left, split it
                                if dep > room_left:
                                    actual_dep = room_left
                                    total_spillover += (dep - room_left)
                            
                            # Log the allowed portion to the specific bucket
                            if actual_dep > 0:
                                new_ledger_rows.append({
                                    "Date": pay_date.strftime("%Y-%m-%d"),
                                    "Fund": b_name,
                                    "Type": "Payday Split",
                                    "Note": f"Standard Payday Split ({b_pct}%)",
                                    "Amount": actual_dep
                                })
                    
                    # Route any caught bucket spillover to Unallocated Savings
                    if total_spillover > 0:
                        new_ledger_rows.append({
                            "Date": pay_date.strftime("%Y-%m-%d"),
                            "Fund": "Unallocated Savings",
                            "Type": "Payday Split",
                            "Note": "Bucket Goal Spillover / Redistributed Excess",
                            "Amount": total_spillover
                        })
                    
                    # CALCULATE NON-ITEMIZED SURPLUS (Gas Reimbursement, Bonus, etc.)
                    reimbursement_surplus = pay_amt - current_income
                    if reimbursement_surplus > 0:
                        new_ledger_rows.append({
                            "Date": pay_date.strftime("%Y-%m-%d"),
                            "Fund": "Unallocated Savings",
                            "Type": "Payday Split",
                            "Note": f"Gas Reimbursement / Paycheck Surplus Margin",
                            "Amount": reimbursement_surplus
                        })
                        
                    if new_ledger_rows:
                        st.session_state.savings_ledger = pd.concat([st.session_state.savings_ledger, pd.DataFrame(new_ledger_rows)], ignore_index=True)
                        push_df_to_google("Savings", st.session_state.savings_ledger)
                        
                    st.toast("Paycheck processed! Core splits & spillovers routed safely!", icon="💸")
                    st.rerun()
        else:
            category_options = list(st.session_state.custom_categories.keys())
            log_col1, log_col2 = st.columns([1, 1])
            with log_col1: exp_date = st.date_input("Transaction Date", value=today, key="main_log_date")
            with log_col2: 
                if category_options: selected_type = st.selectbox("Type", category_options, key="main_log_type")
                else: st.info("Add categories first"); selected_type = None
                    
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
        
        # Wants Progress Section
        st.markdown(f"<div class='progress-label'>Wants Budget: Spent ${metrics['wants_spent']:,.2f} of ${metrics['effective_wants_target']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(metrics['wants_ratio'])
        st.markdown(f"<div class='progress-label' style='font-size: 16px; font-weight: 400;'>👉 <i>Wants Remaining:</i> <b>${metrics['wants_remaining']:,.2f}</b></div>", unsafe_allow_html=True)
        
        if metrics['needs_overage'] > 0: 
            st.caption(f"⚠️ *Fun money shrunk by **${metrics['needs_overage']:,.2f}** to patch Needs overages.*")
            
        st.write("---")
        
        # Needs Progress Section
        st.markdown(f"<div class='progress-label'>Needs Budget: Spent ${metrics['total_needs_burden']:,.2f} of ${metrics['needs_target']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(metrics['needs_ratio'])
        st.markdown(f"<div class='progress-label' style='font-size: 16px; font-weight: 400;'>👉 <i>Needs Remaining:</i> <b>${metrics['needs_remaining']:,.2f}</b></div>", unsafe_allow_html=True)
        
        if metrics['needs_remaining'] > 0:
            st.success(f"💡 End-of-period sweep potential: **${metrics['needs_remaining']:,.2f}** to savings!")

    st.markdown("---")
    st.markdown("---")
    st.subheader("📅 Monthly Bill & Spend Calendar")
    
    # 1. Add interactive selectors to view the entire logging history
    cal_col1, cal_col2, _ = st.columns([1, 1, 4])
    with cal_col1:
        sel_month = st.selectbox("Month", range(1, 13), index=today.month - 1, format_func=lambda x: calendar.month_name[x], key="cal_month_sel")
    with cal_col2:
        start_year = st.session_state.get('tracking_start_date', today).year
        # Allow viewing from the tracking start year up to next year
        sel_year = st.selectbox("Year", range(start_year, today.year + 2), index=today.year - start_year, key="cal_year_sel")
        
    year, month = sel_year, sel_month
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    # 2. Map Fixed Bills
    bill_map = {}
    for bill in st.session_state.fixed_bills:
        if bill["Amount"] > 0: bill_map.setdefault(bill["Due Day"], []).append(f"{bill['Name']} (${bill['Amount']:,.2f})")

    # 3. Aggregate daily expenses split by Needs and Wants
    needs_map, wants_map = {}, {}
    if not st.session_state.expenses.empty:
        df_exp = st.session_state.expenses.copy()
        df_exp['Date'] = pd.to_datetime(df_exp['Date']).dt.date
        
        # Filter strictly for the selected calendar month, independent of pay periods
        month_expenses = df_exp[
            (df_exp['Date'].apply(lambda d: d.year == year and d.month == month)) &
            (df_exp['Amount'] > 0)
        ]
        
        for _, row in month_expenses.iterrows():
            day = row['Date'].day
            cat = row.get('Category', '')
            amt = float(row['Amount'])
            
            if cat == "Needs":
                needs_map[day] = needs_map.get(day, 0.0) + amt
            elif cat == "Wants":
                wants_map[day] = wants_map.get(day, 0.0) + amt

    projected_paydays = project_payday_cadence(st.session_state.first_payday, st.session_state.pay_frequency, year)

    # 4. Build the Calendar HTML (Styled to match your custom UI hex theme)
    html_cal = f'<table style="width:100%; border-collapse:collapse; font-family:sans-serif; table-layout:fixed;"><tr>'
    for day_name in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]: html_cal += f'<th style="background-color:rgba(0,0,0,0.05); padding:10px; border:1px solid rgba(0,0,0,0.1);">{day_name}</th>'
    html_cal += '</tr>'
    
    for week in month_days:
        html_cal += "<tr>"
        for day in week:
            if day == 0: html_cal += '<td style="background-color:rgba(0,0,0,0.02); border:1px solid rgba(0,0,0,0.1); height:115px;"></td>'
            else:
                is_today = "background-color:rgba(149,155,117,0.2); border:2px solid #959B75;" if (day == today.day and month == today.month and year == today.year) else "background-color:rgba(255,255,255,0.4); border:1px solid rgba(0,0,0,0.1);"
                html_cal += f'<td style="{is_today} height:115px; vertical-align:top; padding:0px;">'
                
                current_cal_date = datetime(year, month, day).date()
                if st.session_state.first_payday is not None and current_cal_date in projected_paydays: 
                    html_cal += '<span style="background-color:#959B75; color:white; font-size:11px; font-weight:bold; padding:3px 8px; display:block;">💰 Payday!</span>'
                
                html_cal += f'<div style="padding:8px;"><span style="font-weight:bold; font-size:14px; color:#3A3A3A;">{day}</span>'
                
                # Render Fixed Bills (Red alert theme)
                if day in bill_map:
                    for tag in bill_map[day]: html_cal += f'<span style="background-color:#ffeef0; color:#8B3131; font-size:11px; padding:3px 6px; margin:2px 0; border-radius:4px; display:block; border-left:3px solid #8B3131;">{tag}</span>'
                
                # Render Needs (Sage Green Theme)
                if day in needs_map and needs_map[day] > 0:
                    html_cal += f'<span style="background-color:#E8EAE0; color:#4A4F36; font-size:11px; font-weight:bold; padding:3px 6px; margin:2px 0; border-radius:4px; display:block; border-left:3px solid #959B75;">🛡️ Needs: ${needs_map[day]:,.2f}</span>'

                # Render Wants (Beige/Tan Theme)
                if day in wants_map and wants_map[day] > 0:
                    html_cal += f'<span style="background-color:#F8ECDE; color:#6D5D4B; font-size:11px; font-weight:bold; padding:3px 6px; margin:2px 0; border-radius:4px; display:block; border-left:3px solid #E0CEBA;">🎉 Wants: ${wants_map[day]:,.2f}</span>'

                html_cal += '</div></td>'
        html_cal += "</tr>"
    st.markdown(html_cal + "</table>", unsafe_allow_html=True)


def render_savings_dashboard():
    st.subheader("💰 Savings & Goals Dashboard")
    
    sav_ctrl_col1, sav_ctrl_col2, sav_ctrl_col3, sav_ctrl_spacer = st.columns([2.5, 2.0, 2.2, 3.3])
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
    with sav_ctrl_col3:
        if st.button("🏦 Edit Savings Account", use_container_width=True, key="btn_isolated_savings_acct_trigger"):
            st.session_state.show_savings_account_modal = True
            st.rerun()
            
    st.markdown("---")

    today = datetime.now().date()
    interval_days = 7 if st.session_state.pay_frequency == "Weekly" else (30 if st.session_state.pay_frequency == "Monthly" else 14)
    base_income = st.session_state.get("base_pay", 0.0)
    savings_target = base_income * (st.session_state.pct_split_savings / 100.0)

    bucket_balances, allocated_total, unassigned_pct, _ = calculate_bucket_balances(st.session_state.bucket_config, st.session_state.savings_ledger)
    _, accumulated_payday_savings_ytd = calculate_ytd_savings(st.session_state.income_history, st.session_state.pct_split_savings, today)

    df_sav = st.session_state.savings_ledger.copy()
    
    tracking_start = st.session_state.get('tracking_start_date', today)
    if not df_sav.empty:
        df_sav['Date'] = pd.to_datetime(df_sav['Date']).dt.date
        active_manual_df = df_sav[(df_sav["Type"] != "Payday Split") & (df_sav["Date"] > tracking_start)]
        manual_deposits_total = active_manual_df["Amount"].sum()
        forward_payday_auto = df_sav[(df_sav["Type"] == "Payday Split") & (df_sav["Date"] > tracking_start)]["Amount"].sum()
    else:
        manual_deposits_total = 0.0
        forward_payday_auto = 0.0

    net_total_savings = st.session_state.starting_savings_balance + forward_payday_auto + manual_deposits_total
    unassigned_bal = net_total_savings - allocated_total

    workspace_col_left, workspace_col_right = st.columns([1.1, 1.4])
    
    with workspace_col_left:
        st.markdown("### 📊 Savings Overview")
        st.metric(label="🏦 Grand Total Savings", value=f"${net_total_savings:,.2f}", delta=f"+${forward_payday_auto:,.2f} via Payday Splits")
        st.write(" ") 
        st.metric(label="📈 New Savings Logged YTD", value=f"${accumulated_payday_savings_ytd:,.2f}")
        
        st.markdown("---")
        st.markdown("### 📥 Log Savings Activity")
        
        fund_opts = ["Unallocated Savings"] + list(st.session_state.bucket_config.keys())
        
        def process_sav_transaction():
            sav_amt = st.session_state.get("sav_amt_v124", 0.0)
            if sav_amt > 0:
                t_type = st.session_state["sav_type_v124"]
                
                # --- NEW BUCKET TRANSFER LOGIC ---
                if t_type == "Bucket Transfer":
                    from_fund = st.session_state.get("transfer_from_v124")
                    to_fund = st.session_state.get("transfer_to_v124")
                    memo = st.session_state.get("sav_note_v124", "")
                    
                    if from_fund and to_fund and from_fund != to_fund:
                        row_out = {
                            "Date": st.session_state["sav_date_input_v124"].strftime("%Y-%m-%d"),
                            "Fund": from_fund,
                            "Type": "Transfer Out",
                            "Note": f"To {to_fund}" + (f" ({memo})" if memo else ""),
                            "Amount": -sav_amt
                        }
                        row_in = {
                            "Date": st.session_state["sav_date_input_v124"].strftime("%Y-%m-%d"),
                            "Fund": to_fund,
                            "Type": "Transfer In",
                            "Note": f"From {from_fund}" + (f" ({memo})" if memo else ""),
                            "Amount": sav_amt
                        }
                        new_rows = pd.DataFrame([row_out, row_in])
                        st.session_state.savings_ledger = pd.concat([st.session_state.savings_ledger, new_rows], ignore_index=True)
                
                # --- STANDARD DEPOSIT/WITHDRAWAL LOGIC ---
                else:
                    final_amt = -sav_amt if t_type == "Withdrawal" else sav_amt
                    new_row = pd.DataFrame([{
                        "Date": st.session_state["sav_date_input_v124"].strftime("%Y-%m-%d"),
                        "Fund": st.session_state.get("savings_dropdown_v124", "Unallocated Savings"),
                        "Type": t_type,
                        "Note": st.session_state.get("sav_note_v124", ""),
                        "Amount": final_amt
                    }])
                    st.session_state.savings_ledger = pd.concat([st.session_state.savings_ledger, new_row], ignore_index=True)
                
                push_df_to_google("Savings", st.session_state.savings_ledger)
                
                # Reset fields after a successful log
                st.session_state["sav_note_v124"] = ""
                st.session_state["sav_amt_v124"] = 0.0

        # --- DYNAMIC UI LAYOUT ---
        st.selectbox(label="Transaction Type", options=["Extra Deposit", "Withdrawal", "Bucket Transfer"], key="sav_type_v124")
        st.date_input(label="Date", value=today, key="sav_date_input_v124")
        
        # Swap between one dropdown or two depending on the action selected
        if st.session_state.get("sav_type_v124", "Extra Deposit") == "Bucket Transfer":
            t_col1, t_col2 = st.columns(2)
            with t_col1: st.selectbox("Transfer From", options=fund_opts, key="transfer_from_v124")
            with t_col2: st.selectbox("Transfer To", options=fund_opts, index=1 if len(fund_opts) > 1 else 0, key="transfer_to_v124")
        else:
            st.selectbox(label="Target Bucket", options=fund_opts, key="savings_dropdown_v124")
            
        st.text_input(label="Memo / Note", value="", key="sav_note_v124")
        st.number_input(label="Amount ($)", min_value=0.0, value=0.0, step=50.0, format="%.2f", key="sav_amt_v124")
            
        st.button("Add Transaction", use_container_width=True, on_click=process_sav_transaction)

    with workspace_col_right:
        st.markdown("### 🎯 Savings Buckets & Target Goals")
        st.markdown("Review current Bucket amounts.")
        st.write(" ")
        
        all_tracking_buckets = ["Unallocated Savings"] + list(st.session_state.bucket_targets.keys())
        all_tracking_buckets = list(dict.fromkeys(all_tracking_buckets))
        
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
def render_projection_dashboard():
    # Header Section
    head_col1, head_col2 = st.columns([3.5, 1])
    with head_col1:
        st.subheader("🔮 Savings Bucket & Cash Flow Projections")
        st.caption("Simulate bucket-specific changes over time, including upcoming planned expenditures and subsequent payday recovery splits.")
    with head_col2:
        if st.button("🧮 View the Math", use_container_width=True):
            st.session_state.show_proj_math_modal = True
            st.rerun()

    today = datetime.now().date()
    
    # --- DATA PARSING ---
    base_income = st.session_state.get("base_pay", 0.0)
    savings_target_pool = base_income * (st.session_state.pct_split_savings / 100.0)
    bucket_balances, allocated_total, unassigned_pct, _ = calculate_bucket_balances(st.session_state.bucket_config, st.session_state.savings_ledger)
    
    all_buckets = ["Unallocated Savings"] + list(st.session_state.bucket_config.keys())
    all_buckets = list(dict.fromkeys(all_buckets))
    
    simulated_balances = {b: bucket_balances.get(b, 0.0) for b in all_buckets}
    simulated_balances["Unallocated Savings"] = (st.session_state.starting_savings_balance - allocated_total)

    st.markdown("---")

    # --- TOP ROW: INPUTS SIDE-BY-SIDE ---
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown("### 🎛️ Step 1: Scenario Adjustments")
        st.caption("Temporarily tweak your deposit percentages. Changes reset on refresh.")
        sim_percentages = {}
        total_sim_pct = 0.0
        pct_cols = st.columns(2)
        for idx, (b_name, b_data) in enumerate(st.session_state.bucket_config.items()):
            with pct_cols[idx % 2]:
                val = st.number_input(f"{b_name} (%)", min_value=0.0, max_value=100.0, value=float(b_data.get("pct", 0.0)), step=1.0, key=f"sim_pct_{b_name}")
                sim_percentages[b_name] = val
                total_sim_pct += val
        sim_unassigned_pct = max(0.0, 100.0 - total_sim_pct)

    with right_col:
        st.markdown("### 🛠️ Step 2: Schedule Future Events")
        if "projection_events" not in st.session_state: st.session_state.projection_events = []

        def add_scheduled_event():
            if st.session_state.proj_evt_amt > 0:
                st.session_state.projection_events.append({
                    "Bucket": st.session_state.proj_evt_bucket,
                    "Type": st.session_state.proj_evt_type,
                    "Amount": st.session_state.proj_evt_amt,
                    "Target Date": st.session_state.proj_evt_date,
                    "Frequency": "Monthly" if "Recurring" in st.session_state.proj_evt_type else "None"
                })

        r1, r2 = st.columns(2)
        with r1: st.selectbox("Target Bucket", all_buckets, key="proj_evt_bucket")
        with r2: st.selectbox("Action Type", ["One-Time Withdrawal", "One-Time Deposit", "Recurring Monthly Deposit"], key="proj_evt_type")
        
        r3, r4 = st.columns(2)
        with r3: st.number_input("Amount ($)", min_value=0.0, step=10.0, key="proj_evt_amt")
        with r4: st.date_input("Event Date", value=today, min_value=today, key="proj_evt_date")

        c_add, c_reset = st.columns(2)
        with c_add: st.button("➕ Add Event", use_container_width=True, on_click=add_scheduled_event)
        with c_reset: st.button("🔄 Reset Schedule", use_container_width=True, on_click=lambda: st.session_state.update({"projection_events": []}))

    # --- BOTTOM SECTION: CHART ---
    st.markdown("---")
    st.markdown("### 🗓️ Step 3: Set Horizon & View Results")
    months = st.number_input("Months to project:", min_value=1, max_value=120, value=24, key="proj_horizon")
    eoy_date = today + timedelta(days=int(months * 30.44))

    # --- SIMULATION LOGIC ---
    future_paydays = [p for p in project_payday_cadence(st.session_state.first_payday, st.session_state.pay_frequency, eoy_date.year + 1) if today <= p <= eoy_date]
    timeline = sorted([{"Date": d, "Type": "PAYDAY"} for d in future_paydays] + [{"Date": e["Target Date"], "Type": "USER_EVENT", "Meta": e} for e in st.session_state.projection_events if e["Target Date"] <= eoy_date], key=lambda x: x["Date"])

    snapshots = [{"Date": today, **simulated_balances}]
    for step in timeline:
        if step["Type"] == "PAYDAY":
            for b_name, b_data in st.session_state.bucket_config.items():
                dep = savings_target_pool * (sim_percentages.get(b_name, float(b_data.get("pct", 0.0))) / 100.0)
                simulated_balances[b_name] += dep
            simulated_balances["Unallocated Savings"] += (savings_target_pool * (sim_unassigned_pct / 100.0))
        elif step["Type"] == "USER_EVENT":
            meta = step["Meta"]
            if meta.get("Frequency") == "Monthly" and step["Date"].day == meta["Target Date"].day:
                simulated_balances[meta["Bucket"]] += (meta["Amount"] if "Deposit" in meta["Type"] else -meta["Amount"])
            elif step["Date"] == meta["Target Date"]:
                simulated_balances[meta["Bucket"]] += (meta["Amount"] if "Deposit" in meta["Type"] else -meta["Amount"])
        snapshots.append({"Date": step["Date"], **simulated_balances})

    # --- FILTERED CHART ---
    chart_df = pd.DataFrame(snapshots).set_index("Date")
    f_col, r_col = st.columns([4, 1], vertical_alignment="bottom")
    with f_col:
        selected = st.multiselect("Filter buckets (leave blank for all):", chart_df.columns.tolist(), key="proj_chart_filter_multiselect")
    with r_col:
        st.button("🔄 Reset View", on_click=lambda: st.session_state.update({"proj_chart_filter_multiselect": []}))
        
    st.line_chart(chart_df[selected] if selected else chart_df, use_container_width=True)
