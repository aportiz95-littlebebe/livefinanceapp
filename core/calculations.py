import pandas as pd
from datetime import datetime, timedelta

def get_period_dates(anchor_date, interval_days, today=None):
    """Calculates start and end dates for current and next periods."""
    if today is None: today = datetime.now().date()
    
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
# NEW CORE CALCULATIONS BELOW
# =====================================================================

def generate_timeline_dates(first_payday, frequency, existing_income_df=None):
    """
    Generates a sequence of pay dates from the first payday until today.
    Merges with existing history to protect typed-in paycheck amounts.
    """
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
    """
    Flushes out old auto-deposits and calculates new historical distributions 
    for every individual paycheck based on its explicit net value.
    """
    # Filter out old automatic records to prevent duplicate compounding
    updated_ledger = current_savings_ledger[current_savings_ledger["Type"] != "Auto-Deposit"].copy()
    
    new_sav_rows = []
    for _, row in income_df.iterrows():
        payday_date = row['Effective Date']
        payday_amount = float(row['Amount'])
        
        # Determine the total pool allocated toward savings for this check
        sav_pool = payday_amount * (savings_percentage / 100.0)
        
        # Split that sub-pool into individual envelope targets
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
