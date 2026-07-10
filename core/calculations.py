import pandas as pd
from datetime import datetime, timedelta

def get_period_dates(anchor_date, interval_days, today=None):
    """Calculates start and end dates for current and next periods safely."""
    if today is None: today = datetime.now().date()
    if anchor_date is None:
        return today, today, today, today
    
    days_since_anchor = (today - anchor_date).days
    period_multiplier = days_since_anchor // interval_days
    
    current_start = anchor_date + timedelta(days=period_multiplier * interval_days)
    current_end = current_start + timedelta(days=(interval_days - 1))
    
    next_start = current_start + timedelta(days=interval_days)
    next_end = next_start + timedelta(days=(interval_days - 1))
    
    return current_start, current_end, next_start, next_end

def get_income_for_date(income_df, target_date):
    """Retrieves the exact amount of the latest logged paycheck prior to or on target_date."""
    if income_df.empty: return 0.00
    
    df = income_df.copy()
    df['Effective Date'] = pd.to_datetime(df['Effective Date']).dt.date
    past_entries = df[df['Effective Date'] <= target_date]
    
    if past_entries.empty:
        return 0.00
    
    # Sort descending to grab the absolute latest paycheck entered
    past_entries_sorted = past_entries.sort_values(by='Effective Date', ascending=False)
    return float(past_entries_sorted.iloc[0]['Amount'])

def get_ordinal_suffix(day):
    """Returns the ordinal suffix (st, nd, rd, th) for a given day integer."""
    if 11 <= day <= 13: return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"

def project_payday_cadence(first_payday, pay_frequency, target_year):
    """Projects recurring milestone paydays for the visual calendar layout."""
    projected_dates = set()
    if first_payday is None:
        return projected_dates
        
    run_date = first_payday
    while run_date.year <= target_year:
        projected_dates.add(run_date)
        if pay_frequency == "Weekly":
            run_date += timedelta(days=7)
        elif pay_frequency == "Monthly":
            run_date += timedelta(days=30)
        else:
            run_date += timedelta(days=14)
            
    return projected_dates

def process_bills_for_period(fixed_bills, start_date, end_date):
    """Scans fixed bills list and aggregates items due inside the active pay period range."""
    total_amount = 0.0
    formatted_bullets = []
    
    for bill in fixed_bills:
        if bill.get("Amount", 0.0) > 0:
            current_check = start_date
            while current_check <= end_date:
                if current_check.day == bill.get("Due Day", 1):
                    amt = bill["Amount"]
                    total_amount += amt
                    formatted_bullets.append(f"* **{bill['Name']}:** ${amt:,.2f} on the {get_ordinal_suffix(bill['Due Day'])}")
                    break
                current_check += timedelta(days=1)
                
    return total_amount, formatted_bullets

def compute_budget_metrics(current_income, pct_needs, pct_wants, expenses_df, fixed_bills, current_start, current_end):
    """Executes the mathematical tracking for spending limits and ratios."""
    needs_target = current_income * (pct_needs / 100.0)
    wants_target = current_income * (pct_wants / 100.0)
    
    wants_spent, needs_spent, extra_inc = 0.0, 0.0, 0.0
    
    if expenses_df is not None and not expenses_df.empty:
        df_exp = expenses_df.copy()
        df_exp['Date'] = pd.to_datetime(df_exp['Date']).dt.date
        period_expenses = df_exp[(df_exp['Date'] >= current_start) & (df_exp['Date'] <= current_end)]
        
        if not period_expenses.empty:
            wants_spent = period_expenses[period_expenses['Category'] == "Wants"]["Amount"].sum()
            needs_spent = period_expenses[period_expenses['Category'] == "Needs"]["Amount"].sum()
            extra_inc = -period_expenses[period_expenses['Category'] == "Extra Income"]["Amount"].sum()

    bills_total, bills_bullets = process_bills_for_period(fixed_bills, current_start, current_end)
    
    total_needs_burden = needs_spent + bills_total
    needs_overage = total_needs_burden - needs_target
    
    if needs_overage > 0:
        wants_remaining = wants_target - wants_spent + extra_inc - needs_overage
    else:
        wants_remaining = wants_target - wants_spent + extra_inc
        
    needs_remaining = needs_target - total_needs_burden
    
    effective_wants_target = wants_target - max(0.0, needs_overage)
    wants_ratio = min(max(wants_spent / effective_wants_target, 0.0), 1.0) if effective_wants_target > 0 else 0.0
    needs_ratio = min(max(total_needs_burden / needs_target, 0.0), 1.0) if needs_target > 0 else 0.0

    return {
        "needs_target": needs_target,
        "wants_target": wants_target,
        "wants_spent": wants_spent,
        "total_needs_burden": total_needs_burden,
        "needs_overage": needs_overage,
        "wants_remaining": wants_remaining,
        "needs_remaining": needs_remaining,
        "bills_total": bills_total,
        "bills_bullets": bills_bullets,
        "effective_wants_target": effective_wants_target,
        "wants_ratio": wants_ratio,
        "needs_ratio": needs_ratio
    }

def generate_timeline_dates(first_payday, frequency, existing_income_df=None):
    """Simply passes back your clean manual ledger dataframe instead of generating blank filler values."""
    if existing_income_df is not None:
        return existing_income_df.copy()
    return pd.DataFrame(columns=["Effective Date", "Amount"])

def calculate_ytd_savings(income_history_df, pct_split_savings, today_date):
    """Calculates savings strictly by summing actual manually recorded paycheck parameters."""
    import streamlit as st
    accumulated_ytd = 0.0
    tracking_start = st.session_state.get('tracking_start_date', datetime.now().date())
    
    if income_history_df is not None and not income_history_df.empty:
        df_inc = income_history_df.copy()
        df_inc['Effective Date'] = pd.to_datetime(df_inc['Effective Date']).dt.date
        
        # Pull only rows you manually added after your blank slate date
        ytd_paychecks = df_inc[(df_inc['Effective Date'] <= today_date) & (df_inc['Effective Date'] >= tracking_start)]
        for _, row in ytd_paychecks.iterrows():
            accumulated_ytd += float(row['Amount']) * (pct_split_savings / 100.0)
            
    return accumulated_ytd, accumulated_ytd

def calculate_ytd_income(income_history_df, today_date):
    """Sums real paycheck rows you manually typed into the system."""
    import streamlit as st
    ytd_earned = 0.0
    tracking_start = st.session_state.get('tracking_start_date', datetime.now().date())
    
    if income_history_df is not None and not income_history_df.empty:
        df_ytd = income_history_df.copy()
        df_ytd['Effective Date'] = pd.to_datetime(df_ytd['Effective Date']).dt.date
        df_ytd = df_ytd[(df_ytd['Effective Date'] <= today_date) & (df_ytd['Effective Date'] >= tracking_start)]
        ytd_earned = df_ytd['Amount'].sum()
    return ytd_earned

def calculate_bucket_balances(bucket_config, savings_ledger_df):
    """Sums up your manual baseline bucket values plus any explicit manual transaction items."""
    import streamlit as st
    bucket_balances = {}
    allocated_total = 0.0
    total_assigned_pct = 0.0
    
    df_sav = savings_ledger_df.copy() if savings_ledger_df is not None else pd.DataFrame()
    tracking_start = st.session_state.get('tracking_start_date', datetime.now().date())
    
    if not df_sav.empty:
        df_sav['Date'] = pd.to_datetime(df_sav['Date']).dt.date

    for b_name, b_data in bucket_config.items():
        b_init = float(b_data.get("initial", 0.0))
        b_pct = float(b_data.get("pct", 0.0))
        total_assigned_pct += b_pct
        
        # Captures items explicitly generated during manual paycheck entry or extra logging
        if not df_sav.empty:
            b_ledger = df_sav[(df_sav["Fund"] == b_name) & (df_sav["Date"] >= tracking_start)]["Amount"].sum()
        else:
            b_ledger = 0.0
            
        b_bal = b_init + b_ledger
        bucket_balances[b_name] = b_bal
        allocated_total += b_bal
        
    unassigned_pct = max(0.0, 100.0 - total_assigned_pct)
    return bucket_balances, allocated_total, unassigned_pct, 0.0

def calculate_goal_timeline(remaining, biweekly_flow, next_payday_date, interval_days, today):
    if biweekly_flow <= 0 or remaining <= 0: return None, None
    paychecks_req = int(-(-remaining // biweekly_flow))
    if next_payday_date and today > next_payday_date:
        days_diff = (today - next_payday_date).days
        next_payday_date = next_payday_date + timedelta(days=((days_diff // interval_days) + 1) * interval_days)
    if next_payday_date:
        return paychecks_req, next_payday_date + timedelta(days=(paychecks_req - 1) * interval_days)
    return None, None

def calculate_payoff_recovery(current_balance, debt_amount, current_monthly_contribution, freed_up_payment):
    """Calculates the time to recover a bucket balance and the crossover point."""
    if current_balance < debt_amount:
        return {"error": "Insufficient funds in the bucket."}
    
    new_monthly_contribution = current_monthly_contribution + freed_up_payment
    
    # Time to get back to the pre-payoff balance
    months_to_replenish = debt_amount / new_monthly_contribution if new_monthly_contribution > 0 else float('inf')
    
    # Time until the new trajectory is mathematically richer than the old one
    crossover_month = debt_amount / freed_up_payment if freed_up_payment > 0 else float('inf')
    
    return {
        "new_starting_balance": current_balance - debt_amount,
        "new_monthly_rate": new_monthly_contribution,
        "months_to_replenish": round(months_to_replenish, 1),
        "crossover_month": round(crossover_month, 1)
    }
