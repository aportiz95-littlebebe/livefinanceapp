import streamlit as st
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
