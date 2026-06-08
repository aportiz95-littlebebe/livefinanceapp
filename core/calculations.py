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
    """Retrieves the correct base pay for a specific date."""
    if income_df.empty: return 0.00
    
    df = income_df.copy()
    df['Effective Date'] = pandas_to_date(df['Effective Date'])
    past_entries = df[df['Effective Date'] <= target_date]
    
    if past_entries.empty:
        df_sorted = df.sort_values(by='Effective Date', ascending=True)
        return float(df_sorted.iloc[0]['Amount']) if not df_sorted.empty else 0.00
    
    past_entries_sorted = past_entries.sort_values(by='Effective Date', ascending=False)
    return float(past_entries_sorted.iloc[0]['Amount'])

def pandas_to_date(column):
    """Helper to ensure dates are consistent."""
    import pandas as pd
    return pd.to_datetime(column).dt.date


# =====================================================================
# CORE BUDGET & LEDGER CALCULATIONS ENGINE
# =====================================================================

def get_ordinal_suffix(day):
    """Returns the ordinal suffix (st, nd, rd, th) for a given day integer."""
    if 11 <= day <= 13: return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"


def project_payday_cadence(first_payday, pay_frequency, target_year):
    """
    Projects all recurring payday dates for a target year based on interval rules.
    Returns an empty set if no date has been configured.
    """
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
    """Executes the analytical mathematics to determine targets and balances."""
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
    
    return {
        "needs_target": needs_target,
        "wants_target": wants_target,
        "wants_spent": wants_spent,
        "total_needs_burden": total_needs_burden,
        "needs_overage": needs_overage,
        "wants_remaining": wants_remaining,
        "needs_remaining": needs_remaining,
        "bills_total": bills_total,
        "bills_bullets": bills_bullets
    }


def generate_timeline_dates(first_payday, frequency, existing_income_df=None):
    """Generates a sequence of pay dates from the first payday until today."""
    if first_payday is None:
        return pd.DataFrame(columns=["Effective Date", "Amount"])

    interval_days = 7 if frequency == "Weekly" else (30 if frequency == "Monthly" else 14)
    
    generated_dates = []
    current_calc_date = first_payday
    today_date = datetime.now().date()
    
    while current_calc_date <= today_date:
        generated_dates.append(current_calc_date)
        if frequency == "Monthly":
            current_calc_date += timedelta(days=30)
        else:
            current_calc_date += timedelta(days=interval_days)
            
    template_df = pd.DataFrame({"Effective Date": generated_dates, "Amount": 0.0})
    
    if existing_income_df is not None and not existing_income_df.empty:
        existing_df = existing_income_df.copy()
        existing_df['Effective Date'] = pd.to_datetime(existing_df['Effective Date']).dt.date
        
        merged_df = pd.merge(template_df, existing_df, on="Effective Date", how="left", suffixes=("_gen", "_old"))
        merged_df["Amount"] = merged_df["Amount_old"].fillna(merged_df["Amount_gen"])
        return merged_df[["Effective Date", "Amount"]].sort_values('Effective Date').reset_index(drop=True)
        
    return template_df.sort_values('Effective Date').reset_index(drop=True)


def calculate_historical_savings_splits(income_df, savings_percentage, bucket_config, current_savings_ledger):
    """Flushes out old auto-deposits and calculates new historical distributions."""
    updated_ledger = current_savings_ledger[current_savings_ledger["Type"] != "Auto-Deposit"].copy()
    
    new_sav_rows = []
    for _, row in income_df.iterrows():
        payday_date = row['Effective Date']
        payday_amount = float(row['Amount'])
        
        sav_pool = payday_amount * (savings_percentage / 100.0)
        
        for b_name, b_data in bucket_config.items():
            b_pct = float(b_data.get("pct", 0.0))
            if (dep := sav_pool * (b_pct / 100.0)) > 0:
                new_sav_rows.append({
                    "Date": payday_date, 
                    "Fund": b_name, 
                    "Type": "Auto-Deposit", 
                    "Note": f"Payday Allocation (Split from {payday_date.strftime('%b %d')})", 
                    "Amount": dep
                })
                
    if new_sav_rows:
        return pd.concat([updated_ledger, pd.DataFrame(new_sav_rows)], ignore_index=True)
    return updated_ledger


def calculate_ytd_savings(income_history_df, pct_split_savings, today_date):
    """Calculates total lifetime and current year YTD savings accumulations."""
    accumulated_lifetime = 0.0
    accumulated_ytd = 0.0
    
    if income_history_df is not None and not income_history_df.empty:
        df_inc = income_history_df.copy()
        df_inc['Effective Date'] = pd.to_datetime(df_inc['Effective Date']).dt.date
        
        historical_paychecks = df_inc[df_inc['Effective Date'] <= today_date]
        for _, row in historical_paychecks.iterrows():
            accumulated_lifetime += float(row['Amount']) * (pct_split_savings / 100.0)
            
        ytd_paychecks = df_inc[(df_inc['Effective Date'] <= today_date) & (df_inc['Effective Date'].apply(lambda x: x.year == today_date.year))]
        for _, row in ytd_paychecks.iterrows():
            accumulated_ytd += float(row['Amount']) * (pct_split_savings / 100.0)
            
    return accumulated_lifetime, accumulated_ytd
