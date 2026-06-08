import streamlit as st
import pandas as pd
from datetime import datetime
from core.calculations import generate_timeline_dates, calculate_historical_savings_splits

@st.dialog("💰 Edit Income & Budgets", width="large")
def render_unified_income_splits_modal():
    # 0. Sync Persistent State safely
    if 'temp_pct_split_needs' not in st.session_state: st.session_state.temp_pct_split_needs = st.session_state.pct_split_needs
    if 'temp_pct_split_wants' not in st.session_state: st.session_state.temp_pct_split_wants = st.session_state.pct_split_wants
    if 'temp_pct_split_savings' not in st.session_state: st.session_state.temp_pct_split_savings = st.session_state.pct_split_savings

    col_inputs, col_ledger = st.columns([1.0, 1.2])
    
    with col_inputs:
        st.markdown("#### ⚙️ Auto-Generate Pay Dates")
        
        # Check box toggle tool to declare if calendar timeline should be turned on
        has_payday_setup = st.checkbox(
            "Configure / Enable Payday Timeline", 
            value=(st.session_state.get("first_payday") is not None),
            key="modal_payday_timeline_toggle"
        )
        
        chosen_first_payday = None
        if has_payday_setup:
            fallback_date = st.session_state.get("first_payday") if st.session_state.get("first_payday") is not None else datetime(datetime.now().year, 1, 1).date()
            chosen_first_payday = st.date_input(
                "First Payday of the Year:", 
                value=fallback_date,
                key="modal_first_payday_input"
            )
        
        frequency_opts = ["Weekly", "Bi-weekly", "Monthly"]
        chosen_freq = st.selectbox(
            "Pay Frequency:", 
            frequency_opts, 
            index=frequency_opts.index(st.session_state.get("pay_frequency", "Bi-weekly"))
        )
        
        if st.button("🗓️ Generate/Refresh Pay Dates", use_container_width=True):
            if not has_payday_setup or chosen_first_payday is None:
                st.error("Please check the configuration box and select a date first.")
            else:
                st.session_state.temp_income_history = generate_timeline_dates(
                    first_payday=chosen_first_payday,
                    frequency=chosen_freq,
                    existing_income_df=st.session_state.income_history
                )
                st.session_state.first_payday = chosen_first_payday
                st.session_state.pay_frequency = chosen_freq
                st.toast("Pay dates generated up to today!", icon="📆")

        st.markdown("---")
        new_starting_savings = st.number_input(
            "Starting Savings Balance ($):", 
            value=float(st.session_state.get("starting_savings_balance", 0.0)), 
            step=100.0, 
            format="%.2f"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Budget Allocations")
        val_needs = st.number_input("Needs %:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_needs), key="val_needs_input")
        val_wants = st.number_input("Wants %:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_wants), key="val_wants_input")
        val_savings = st.number_input("Savings %:", min_value=0.0, max_value=100.0, value=float(st.session_state.temp_pct_split_savings), key="val_savings_input")

    with col_ledger:
        st.markdown("<h4 style='margin-top:0; padding-top:0;'>📝 Paycheck Amounts Ledger</h4>", unsafe_allow_html=True)
        st.caption("Double-click any cell in **Net Amount ($)** to log what you were paid on that day.")
        
        display_df = st.session_state.temp_income_history.copy() if 'temp_income_history' in st.session_state else pd.DataFrame()
        
        if display_df.empty:
            display_df = pd.DataFrame(columns=["Effective Date", "Amount"])
        else:
            display_df['Effective Date'] = pd.to_datetime(display_df['Effective Date']).dt.date
            display_df = display_df.sort_values('Effective Date').reset_index(drop=True)

        edited_inc_df = st.data_editor(
            display_df, 
            use_container_width=True, 
            num_rows="fixed", 
            key="income_auto_dates_grid_editor",
            column_config={
                "Effective Date": st.column_config.DateColumn("Pay Date", disabled=True),
                "Amount": st.column_config.NumberColumn("Net Amount ($)", min_value=0.0, format="$%.2f", required=True)
            }
        )
        
        if st.button("Stage Ledger Changes", use_container_width=True):
            st.session_state.temp_income_history = edited_inc_df.dropna(subset=['Effective Date', 'Amount'])
            st.toast("Amounts staged successfully!", icon="💾")

    st.markdown("---")
    if (val_needs + val_wants + val_savings == 100.0) or (val_needs == 0 and val_wants == 0 and val_savings == 0):
        if st.button("💾 Save All Changes & Calculate Split History", use_container_width=True):
            final_df = edited_inc_df.dropna(subset=['Effective Date', 'Amount']).copy()
            
            if not final_df.empty:
                final_df['Effective Date'] = pd.to_datetime(final_df['Effective Date']).dt.date
                final_df = final_df.sort_values('Effective Date').reset_index(drop=True)
            
            st.session_state.savings_ledger = calculate_historical_savings_splits(
                income_df=final_df,
                savings_percentage=val_savings,
                bucket_config=st.session_state.bucket_config,
                current_savings_ledger=st.session_state.savings_ledger
            )

            st.session_state.income_history = final_df
            st.session_state.pct_split_needs = val_needs
            st.session_state.pct_split_wants = val_wants
            st.session_state.pct_split_savings = val_savings
            st.session_state.starting_savings_balance = new_starting_savings
            if not has_payday_setup:
                st.session_state.first_payday = None
            st.rerun()
    else:
        st.error("❌ Budget Allocation percentages must sum up to exactly 100%.")


@st.dialog("📋 Edit My Fixed Monthly Bills", width="large")
def render_bills_modal():
    st.markdown("### Fixed Bills Ledger")
    def toggle_edit(idx, state): st.session_state[f"edit_bill_{idx}"] = state
    def save_bill(idx):
        bill = st.session_state.temp_fixed_bills[idx]
        bill["Name"] = st.session_state[f"edit_b_name_{idx}"]
        bill["Amount"] = float(st.session_state[f"edit_b_amt_{idx}"])
        bill["Bucket"] = st.session_state[f"edit_b_bucket_{idx}"]
        bill["Due Day"] = int(st.session_state[f"edit_b_day_{idx}"])
        st.session_state[f"edit_bill_{idx}"] = False
    def del_bill(idx):
        st.session_state.temp_fixed_bills.pop(idx)
        st.session_state.pop(f"edit_bill_{idx}", None)

    for idx, bill in enumerate(st.session_state.temp_fixed_bills):
        is_editing = st.session_state.get(f"edit_bill_{idx}", False)
        show_label = "visible" if idx == 0 else "collapsed"
        b_col1, b_col2, b_col3, b_col4, b_col5, b_col6 = st.columns([2.4, 1.5, 1.5, 1.0, 0.5, 0.5])
        with b_col1: st.text_input("Bill Name", value=bill["Name"], key=f"edit_b_name_{idx}", disabled=not is_editing, label_visibility=show_label)
        with b_col2: st.number_input("Amount ($)", min_value=0.0, value=float(bill["Amount"]), step=10.0, format="%.2f", key=f"edit_b_amt_{idx}", disabled=not is_editing, label_visibility=show_label)
        with b_col3: st.selectbox("Bucket", ["Needs", "Wants"], index=["Needs", "Wants"].index(bill.get("Bucket", "Needs")), key=f"edit_b_bucket_{idx}", disabled=not is_editing, label_visibility=show_label)
        with b_col4: st.selectbox("Due Day", list(range(1, 32)), index=int(bill.get("Due Day", 1)) - 1, key=f"edit_b_day_{idx}", disabled=not is_editing, label_visibility=show_label)
        with b_col5:
            if idx == 0: st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if is_editing: st.button("✅", key=f"save_b_{idx}", on_click=save_bill, args=(idx,))
            else: st.button("📝", key=f"start_edit_b_{idx}", on_click=toggle_edit, args=(idx, True))
        with b_col6:
            if idx == 0: st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if is_editing: st.button("🚫", key=f"cancel_b_{idx}", on_click=toggle_edit, args=(idx, False))
            else: st.button("❌", key=f"del_b_{idx}", on_click=del_bill, args=(idx,))
    
    st.markdown("---")
    st.markdown("### ✨ Add a New Bill")
    new_b_col1, new_b_col2, new_b_col3, new_b_col4 = st.columns([2.5, 1.5, 1.5, 1.0])
    with new_b_col1: st.text_input("Bill Name", key="modal_create_b_name")
    with new_b_col2: st.number_input("Amount ($)", min_value=0.0, step=10.0, format="%.2f", key="modal_create_b_amt")
    with new_b_col3: st.selectbox("Bucket", ["Needs", "Wants"], key="modal_create_b_bucket")
    with new_b_col4: st.selectbox("Due Day", list(range(1, 32)), key="modal_create_b_day")
    
    def add_bill():
        name = st.session_state.get("modal_create_b_name", "")
        amt = st.session_state.get("modal_create_b_amt", 0.0)
        bucket = st.session_state.get("modal_create_b_bucket", "Needs")
        day = st.session_state.get("modal_create_b_day", 1)
        if name and amt >= 0: st.session_state.temp_fixed_bills.append({"Name": name, "Amount": float(amt), "Bucket": bucket, "Due Day": int(day)})

    is_any_bill_editing = any(st.session_state.get(f"edit_bill_{i}", False) for i in range(len(st.session_state.temp_fixed_bills)))
    col_save_l, col_save_r = st.columns([2, 6])
    with col_save_l: st.button("Add Bill", use_container_width=True, on_click=add_bill, disabled=is_any_bill_editing)
    with col_save_r:
        if st.button("🔄 Save Changes", use_container_width=True, disabled=is_any_bill_editing): 
            st.session_state.fixed_bills = [dict(bill) for bill in st.session_state.temp_fixed_bills]
            st.rerun()


@st.dialog("🛠️ Edit Expense Options & Types", width="large")
def render_category_modal():
    st.markdown("### Expenses & Types")
    def toggle_edit_cat(idx, state): st.session_state[f"edit_cat_{idx}"] = state
    def save_cat(idx):
        new_name = st.session_state[f"edit_c_name_{idx}"]
        new_bucket = st.session_state[f"edit_c_bucket_{idx}"]
        new_categories = {}
        for i, (k, v) in enumerate(st.session_state.temp_custom_categories.items()):
            if i == idx: new_categories[new_name] = new_bucket
            else: new_categories[k] = v
        st.session_state.temp_custom_categories = new_categories
        st.session_state[f"edit_cat_{idx}"] = False
    def del_cat(idx):
        key_to_del = list(st.session_state.temp_custom_categories.keys())[idx]
        st.session_state.temp_custom_categories.pop(key_to_del, None)
        st.session_state.pop(f"edit_cat_{idx}", None)

    for idx, (opt_name, opt_bucket) in enumerate(list(st.session_state.temp_custom_categories.items())):
        is_editing = st.session_state.get(f"edit_cat_{idx}", False)
        show_label = "visible" if idx == 0 else "collapsed"
        c_col1, c_col2, c_col3, c_col4 = st.columns([3.4, 2.0, 0.5, 0.5], vertical_alignment="bottom")
        with c_col1: st.text_input("Category Name", value=opt_name, key=f"edit_c_name_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c_col2: st.selectbox("Bucket", ["Needs", "Wants", "Extra Income"], index=["Needs", "Wants", "Extra Income"].index(opt_bucket) if opt_bucket in ["Needs", "Wants", "Extra Income"] else 0, key=f"edit_c_bucket_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c_col3:
            if is_editing: st.button("✅", key=f"save_c_{idx}", on_click=save_cat, args=(idx,), use_container_width=True)
            else: st.button("📝", key=f"start_edit_c_{idx}", on_click=toggle_edit_cat, args=(idx, True), use_container_width=True)
        with c_col4:
            if is_editing: st.button("🚫", key=f"cancel_c_{idx}", on_click=toggle_edit_cat, args=(idx, False), use_container_width=True)
            else: st.button("❌", key=f"del_c_{idx}", on_click=del_cat, args=(idx,), use_container_width=True)
                
    st.markdown("---")
    st.markdown("### ✨ Add a New Expense")
    new_c_col1, new_c_col2 = st.columns([3.4, 2.0])
    with new_c_col1: st.text_input("Category Name", key="modal_create_c_name")
    with new_c_col2: st.selectbox("Bucket", ["Needs", "Wants", "Extra Income"], key="modal_create_c_bucket")
    def add_cat():
        name = st.session_state.get("modal_create_c_name", "")
        bucket = st.session_state.get("modal_create_c_bucket", "Needs")
        if name and name not in st.session_state.temp_custom_categories: st.session_state.temp_custom_categories[name] = bucket

    is_any_cat_editing = any(st.session_state.get(f"edit_cat_{i}", False) for i in range(len(st.session_state.temp_custom_categories)))
    col_save_l, col_save_r = st.columns([2, 6])
    with col_save_l: st.button("Add Expense Type", use_container_width=True, on_click=add_cat, disabled=is_any_cat_editing)
    with col_save_r:
        if st.button("🔄 Save Changes", use_container_width=True, disabled=is_any_cat_editing): 
            st.session_state.custom_categories = dict(st.session_state.temp_custom_categories)
            st.rerun()


@st.dialog("📜 View Transaction History", width="large")
def render_ledger_modal():
    st.dataframe(st.session_state.expenses, use_container_width=True)


@st.dialog("🛠️ Configure Envelopes & Targets", width="large")
def render_combined_envelopes_modal():
    st.markdown("### 🗂️ Configure Envelopes & Targets")
    def toggle_edit_buck(idx, state): st.session_state[f"edit_buck_{idx}"] = state
    def save_buck(idx):
        old_name = list(st.session_state.temp_bucket_config.keys())[idx]
        new_name = st.session_state[f"eb_name_{idx}"]
        new_init = float(st.session_state[f"eb_init_{idx}"])
        new_pct = float(st.session_state[f"eb_pct_{idx}"])
        new_tgt = float(st.session_state[f"eb_tgt_{idx}"])
        if new_name != old_name and new_name.strip():
            st.session_state.temp_bucket_config[new_name] = {"initial": new_init, "pct": new_pct}
            st.session_state.temp_bucket_targets[new_name] = new_tgt
            del st.session_state.temp_bucket_config[old_name]
            if old_name in st.session_state.temp_bucket_targets: del st.session_state.temp_bucket_targets[old_name]
        else:
            st.session_state.temp_bucket_config[old_name] = {"initial": new_init, "pct": new_pct}
            st.session_state.temp_bucket_targets[old_name] = new_tgt
        st.session_state[f"edit_buck_{idx}"] = False

    def del_buck(idx):
        name_to_del = list(st.session_state.temp_bucket_config.keys())[idx]
        del st.session_state.temp_bucket_config[name_to_del]
        if name_to_del in st.session_state.temp_bucket_targets: del st.session_state.temp_bucket_targets[name_to_del]
        st.session_state.pop(f"edit_buck_{idx}", None)

    for idx, (b_name, b_data) in enumerate(list(st.session_state.temp_bucket_config.items())):
        is_editing = st.session_state.get(f"edit_buck_{idx}", False)
        show_label = "visible" if idx == 0 else "collapsed"
        c1, c2, c3, c4, c5, c6 = st.columns([2.0, 1.2, 1.2, 1.4, 0.4, 0.4], vertical_alignment="bottom")
        with c1: st.text_input("Envelope Name", value=b_name, key=f"eb_name_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c2: st.number_input("Current Balance ($)", min_value=0.0, value=float(b_data.get("initial", 0.0)), step=100.0, format="%.2f", key=f"eb_init_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c3: st.number_input("Paycheck Split (%)", min_value=0.0, max_value=100.0, value=float(b_data.get("pct", 0.0)), step=5.0, format="%.1f", key=f"eb_pct_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c4: st.number_input("Target Milestone ($)", min_value=0.0, value=float(st.session_state.temp_bucket_targets.get(b_name, 0.0)), step=100.0, format="%.2f", key=f"eb_tgt_{idx}", disabled=not is_editing, label_visibility=show_label)
        with c5:
            if is_editing: st.button("✅", key=f"save_b_{idx}", on_click=save_buck, args=(idx,), use_container_width=True)
            else: st.button("📝", key=f"edit_b_{idx}", on_click=toggle_edit_buck, args=(idx, True), use_container_width=True)
        with c6:
            if is_editing: st.button("🚫", key=f"canc_b_{idx}", on_click=toggle_edit_buck, args=(idx, False), use_container_width=True)
            else: st.button("❌", key=f"del_b_{idx}", on_click=del_buck, args=(idx,), use_container_width=True)
            
    st.markdown("---")
    st.markdown("### ✨ Create a New Paycheck Envelope & Target Goal")
    nc1, nc2, nc3, nc4 = st.columns([2.0, 1.2, 1.2, 1.4])
    with nc1: st.text_input("New Envelope Name", key="new_b_name")
    with nc2: st.number_input("Current Balance ($)", min_value=0.0, step=100.0, format="%.2f", key="new_b_init")
    with nc3: st.number_input("Paycheck Split (%)", min_value=0.0, max_value=100.0, step=5.0, format="%.1f", key="new_b_pct")
    with nc4: st.number_input("Target Milestone ($)", min_value=0.0, step=500.0, format="%.2f", key="new_b_tgt")
    
    def add_bucket():
        n = st.session_state.get("new_b_name", "").strip()
        i = st.session_state.get("new_b_init", 0.0)
        p = st.session_state.get("new_b_pct", 0.0)
        t = st.session_state.get("new_b_tgt", 0.0)
        if n and n not in st.session_state.temp_bucket_config:
            st.session_state.temp_bucket_config[n] = {"initial": i, "pct": p}
            st.session_state.temp_bucket_targets[n] = t
            for k in ["new_b_name", "new_b_init", "new_b_pct", "new_b_tgt"]: st.session_state[k] = "" if k == "new_b_name" else 0.0
            
    is_any_bucket_editing = any(st.session_state.get(f"edit_buck_{i}", False) for i in range(len(st.session_state.temp_bucket_config)))
    add_btn_col, _ = st.columns([2.5, 5.5])
    with add_btn_col: st.button("Add Savings Bucket", use_container_width=True, on_click=add_bucket, disabled=is_any_bucket_editing)

    custom_unbacked_goals = [k for k in st.session_state.temp_bucket_targets.keys() if k not in ["Unallocated Savings"] and k not in st.session_state.temp_bucket_config]
    if custom_unbacked_goals:
        st.markdown("---")
        st.markdown("### 🎯 Standalone Custom Milestones")
        def save_custom_unbacked(key_name, idx):
            new_n = st.session_state[f"unbk_n_{idx}"]
            new_v = float(st.session_state[f"unbk_v_{idx}"])
            if new_n != key_name and new_n.strip():
                st.session_state.temp_bucket_targets[new_n] = new_v
                del st.session_state.temp_bucket_targets[key_name]
            else: st.session_state.temp_bucket_targets[key_name] = new_v
            st.session_state[f"edit_unbk_{idx}"] = False

        for idx, g_name in enumerate(custom_unbacked_goals):
            unbk_edit = st.session_state.get(f"edit_unbk_{idx}", False)
            cc1, cc2, cc3, cc4 = st.columns([3.2, 2.6, 0.4, 0.4], vertical_alignment="bottom")
            with cc1: st.text_input("Goal Milestone Label", value=g_name, key=f"unbk_n_{idx}", disabled=not unbk_edit, label_visibility="collapsed")
            with cc2: st.number_input("Target Amount ($)", min_value=0.0, value=float(st.session_state.temp_bucket_targets[g_name]), format="%.2f", key=f"unbk_v_{idx}", disabled=not unbk_edit, label_visibility="collapsed")
            with cc3:
                if unbk_edit: st.button("✅", key=f"sv_unbk_{idx}", on_click=save_custom_unbacked, args=(g_name, idx))
                else: st.button("📝", key=f"ed_unbk_{idx}", on_click=lambda i=idx: st.session_state.update({f"edit_unbk_{i}": True}))
            with cc4:
                if unbk_edit: st.button("🚫", key=f"cn_unbk_{idx}", on_click=lambda i=idx: st.session_state.update({f"edit_unbk_{i}": False}))
                else: st.button("❌", key=f"dl_unbk_{idx}", on_click=lambda name=g_name: st.session_state.temp_bucket_targets.pop(name))

    st.markdown("---")
    st.markdown("### ✨ Create a Standalone Custom Milestone Goal")
    uc1, uc2 = st.columns([3.2, 2.6])
    with uc1: st.text_input("Standalone Goal Label", key="new_unbacked_name")
    with uc2: st.number_input("Goal Target Amount ($)", min_value=0.0, step=100.0, format="%.2f", key="new_unbacked_val")
    def add_standalone_goal():
        n = st.session_state.get("new_unbacked_name", "").strip()
        v = st.session_state.get("new_unbacked_val", 0.0)
        if n and n not in st.session_state.temp_bucket_targets:
            st.session_state.temp_bucket_targets[n] = float(v)
            for k in ["new_unbacked_name", "new_unbacked_val"]: st.session_state[k] = "" if k == "new_unbacked_name" else 0.0
            
    is_any_unbacked_editing = any(st.session_state.get(f"edit_unbk_{i}", False) for i in range(len(custom_unbacked_goals)))
    add_unbk_col, _ = st.columns([2.5, 5.5])
    with add_unbk_col: st.button("Add Standalone Goal", use_container_width=True, on_click=add_standalone_goal, disabled=is_any_unbacked_editing)
    st.markdown("---")
    
    is_any_row_editing = is_any_bucket_editing or is_any_unbacked_editing
    is_typing_anything = bool(st.session_state.get("new_b_name", "").strip()) or bool(st.session_state.get("new_unbacked_name", "").strip())
    lock_sync_button = is_any_row_editing or is_typing_anything
    _, save_col = st.columns([6, 2])
    with save_col:
        if st.button("🔄 Save Changes", use_container_width=True, disabled=lock_sync_button): 
            st.session_state.bucket_config = {k: dict(v) for k, v in st.session_state.temp_bucket_config.items()}
            st.session_state.bucket_targets = dict(st.session_state.temp_bucket_targets)
            st.rerun()


@st.dialog("📜 Historical Savings Ledger", width="large")
def render_savings_history_modal():
    edited_sav_df = st.data_editor(st.session_state.savings_ledger, use_container_width=True, num_rows="dynamic", key="ledger_grid_v113")
    st.session_state.savings_ledger = edited_sav_df
    if st.button("Save Changes", use_container_width=True): st.rerun()
