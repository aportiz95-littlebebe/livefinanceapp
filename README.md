# My Finance Dashboard

![Version](https://img.shields.io/badge/version-15.0-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)

A comprehensive, state-driven personal finance dashboard built with Streamlit and Pandas. This application handles dynamic pay period tracking, budget splitting, expense tracking with rollover logic, and a highly predictive savings & goal tracking engine.

---

## 🏗️ Upcoming Architecture (Code Splitting Strategy)

To prepare for future scalability, the monolithic `app.py` is being divided into a modular repository. When initializing this new GitHub repo, structure your directories as follows:

```text
my-finance-dashboard/
│
├── main.py                 # Main Streamlit entry point (Page config, tab routing)
├── ui/
│   ├── __init__.py
│   ├── theme.py            # CSS injections, color hex codes, custom styling
│   ├── modals.py           # @st.dialog functions (Income, Bills, Envelopes)
│   └── views.py            # Tab layouts (Budget Dashboard, Savings Dashboard)
│
├── core/
│   ├── __init__.py
│   ├── calculations.py     # Timeline math, period multipliers, budget overages
│   └── projections.py      # Goal timeline estimations and auto-accrual math
│
├── data/
│   ├── __init__.py
│   ├── state.py            # Session state initialization and baselines
│   └── models.py           # DataFrame schemas, transaction processing
│
├── requirements.txt
└── README.md
```

---

## 🧮 The Math & Calculation Engine

The application relies heavily on dynamic date calculations and bottom-up summation rather than static numbers. Here is how the core mathematical engines function:

### 1. Chronological Timeline Engine
The app anchors all budget logic to a defined pay schedule (Weekly, Bi-weekly, or Monthly).
* **Anchor Date:** Can be set to Next Payday, First Payday of the Year, or manually entered.
* **Period Multiplier:** Calculates exactly how many pay periods have elapsed since the anchor.
    ```python
    days_since_anchor = (today - anchor_date).days
    period_multiplier = days_since_anchor // interval_days
    ```
* **Current Period Bounds:** Determines the start and end dates of the *current* active pay period using the multiplier, ensuring expenses are only queried for the current cycle.

### 2. Income & Split Budgets
* **Historical Base Pay:** The app reads from `income_history` and finds the most recent base pay effective *before or on* today's date.
* **Target Calculation:** The active income is multiplied by user-defined percentages (Needs, Wants, Savings). 
    * *Note: Percentages must strictly sum to 100%.*

### 3. Expense Rollover & Overage Logic
* **Needs Burden:** Calculated as `needs_spent + bills_due_in_period`.
* **The Overage Cascade:** If the Needs burden exceeds the Needs target, the deficit (`needs_overage`) is automatically subtracted from the `wants_remaining` pool. This ensures that essential overspending naturally shrinks discretionary "Fun Money" rather than breaking the budget.
* **Extra Income:** Treated as a negative expense, naturally increasing the available pool for Wants.

### 4. Savings & Projection Engine
Savings balances are calculated using a bottom-up approach combining historical starting balances, automatic accrual, and manual ledger entries.
* **Auto-Accrual:** `(savings_target * (bucket_pct / 100.0)) * paydays_passed`. The system implicitly assumes that scheduled payday transfers occurred successfully.
* **Remaining Savings (Buffer):** Any percentage of the global savings target not explicitly allocated to a custom envelope flows into the `Unallocated Savings` pool, acting as a buffer.
* **Goal Projections:** For targets with an established goal amount, the engine calculates the remaining deficit and divides it by the expected bi-weekly flow (`savings_target * (flow_pct / 100.0)`). It then adds the required number of pay periods to the calendar to project the exact date the goal will be fully funded.

---

## 🎨 UI, Formatting, and Theming

The UI is heavily customized using Streamlit's raw HTML/CSS injection via `st.markdown(unsafe_allow_html=True)`.

### Color Palette (Hex Codes)
* **Global Background:** `#F9F5EA` (A soft, warm off-white).
* **Card/Container Background:** `#FFFDFB` (Pure, clean white for contrast).
* **Text & Typography:** `#3A3A3A` (Dark charcoal, softer than pure black).
* **Headers:** Background `#EAD8C0` with `#3A3A3A` text, fully rounded (`border-radius: 20px`).
* **Primary Action Buttons:** `#98966D` (Muted olive/sage green), transitions to `#88865D` on hover with a subtle box-shadow.
* **Alerts / Warnings:** `#AA4F4E` (Muted brick red).
* **Progress Bars:** `#526061` (Deep slate grey).

### Spacing & Layout Constraints
* **Layout:** Wide mode is enforced (`layout="wide"`).
* **Calendar View:** Built using a raw HTML table. Follows a **Monday-start week** (`calendar.Calendar(firstweekday=0)`) to align with standard working financial cycles. 
* **Containers:** Extensively uses `st.columns` with specific ratios (e.g., `[2.4, 1.5, 1.5, 1.0, 0.5, 0.5]`) to build highly aligned data-entry tables without relying strictly on `st.data_editor`.

---

## 🖱️ Interactive Elements & State Management

### Dialog Modals (`@st.dialog`)
The application bypasses standard Streamlit expanders in favor of floating modal windows for configuration.
* `render_unified_income_splits_modal()`: Handles base pay, historical ledger generation, and budget percentages.
* `render_bills_modal()` & `render_category_modal()`: Uses an inline edit-toggle state (`st.session_state[f"edit_bill_{idx}"]`) allowing users to swap static text out for input fields dynamically row-by-row.
* `render_combined_envelopes_modal()`: Manages custom buckets, percentages, and standalone unbacked goals.

### Button Workflows
* All major data mutations are wrapped in a temporary state (`st.session_state.temp_*`). 
* Changes only commit to the main global state when the user clicks the explicit `🔄 Save Changes` button, which triggers a full `st.rerun()`.
* Form submission logic strictly disables buttons if required fields (like selecting a category) are missing or if other rows are actively in "Edit" mode.

---

## 🚀 Getting Started

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/my-finance-dashboard.git
cd my-finance-dashboard
pip install -r requirements.txt
```

**Required Packages:**
```text
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.14.0
```

### 2. Run the Application
```bash
streamlit run app.py
```

### 3. Developer Notes
* **Session State:** On the first run, the app hydrates over 15 different session state variables to establish the baseline empty tables. If you encounter missing key errors during development, clear your browser cache or restart the Streamlit server to re-trigger the init block.
* **Data Persistence:** Currently, state only lives in RAM. Future iterations (post code-split) should inject a SQLite or JSON file handler into the `data/models.py` layer to serialize the `st.session_state` dataframes on `Save Changes`.
