# Envelope Savings Hub (BBS 1st Finance App)

![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data-150458.svg)

The Envelope Savings Hub is a modular, state-driven personal finance application built with Streamlit and Pandas. It provides dynamic budgeting, chronological pay-period tracking, and a highly predictive goal-oriented envelope savings system.

## ✨ Core Features

* **Dynamic Calendar & Pay Cadence:** Automatically maps Bi-weekly, Weekly, or Monthly paydays across the entire year to align expenses with actual cash flow.
* **The Overage Cascade:** Smart budget logic where essential overspending ("Needs") automatically deducts from your discretionary pool ("Wants") before breaking the core budget.
* **Dynamic Savings Distribution:** "Regular Savings" is not a fixed amount; it dynamically calculates as the difference between your total savings pool and the custom percentages allocated to your specific target envelopes.
* **Goal Projections:** Automatically calculates flow rates into individual savings buckets and forecasts the exact date a goal will be fully funded.
* **Retroactive Ledger Syncing:** Modifying an expense type or saving bucket name automatically scans and updates historical transactions to maintain data integrity.

---

## 🏗️ System Architecture

The application is heavily modularized to separate data initialization, visual identity, mathematical processing, and front-end rendering into distinct components.

### 1. `state.py` (The Memory Bank)
Initializes all baseline Streamlit session state variables.
* Boots up empty Pandas DataFrames for `income_history`, `expenses`, and `savings_ledger`.
* Establishes the default budget parameters, dictionary schemas for `fixed_bills`, `custom_categories`, and `bucket_config`.
* Sets the temporal anchor limits (First Payday, Next Payday, Pay Frequency).

### 2. `calculations.py` (The Math Engine)
Pure Python functions strictly dedicated to number crunching and dataframe manipulation. It contains no visual elements.
* **Time & Schedule:** `get_period_dates`, `project_payday_cadence`, `generate_timeline_dates`
* **Income & Expenses:** `get_income_for_date`, `process_bills_for_period`, `calculate_ytd_income`, `compute_budget_metrics`
* **Savings & Goals:** `calculate_bucket_balances`, `calculate_historical_savings_splits`, `calculate_ytd_savings`, `calculate_goal_timeline`

### 3. `modals.py` (The Control Panels)
Houses all interactive data-entry popups using the `@st.dialog` decorator to keep the main dashboard clean.
* Implements "temp state" variables allowing users to stage changes (edit multiple rows, rename buckets, adjust splits) safely before committing them to the live session state.
* Functions include: `render_unified_income_splits_modal`, `render_bills_modal`, `render_category_modal`, `render_ledger_modal`, `render_combined_envelopes_modal`, and `render_savings_history_modal`.

### 4. `theme.py` (The Visual Identity)
Injects custom CSS to override Streamlit's default aesthetics.
* Implements a cohesive color palette: Cream background (`#F5F7EC`), warm beige metric containers (`#E0CEBA`), and muted sage green action buttons (`#959B75`).
* Overrides tab selection logic, button hover shadows, disabled form inputs, and custom progress bar mapping.

### 5. `views.py` (The Dashboards)
The front-end user interface that imports the logic and memory components to render the visual experience.
* **`render_budget_dashboard()`:** Displays base pay, YTD earnings, Needs/Wants/Savings limit gauges, upcoming bills, an active transaction logger, and a custom HTML chronological monthly calendar.
* **`render_savings_dashboard()`:** Displays grand total wealth, an activity logger for extra deposits/withdrawals, individual bucket balances, and timeline completion forecasts.

---

## 🚀 Running the Application

### 1. Prerequisites
Ensure you have Python 3.9+ installed along with the required libraries:
```bash
pip install streamlit pandas
```

### 2. File Structure
To run the app, the 5 core files must be routed through a `main.py` entry point. Ensure your directory looks like this:
```text
/your-repo-name
│── main.py
│── state.py
│── calculations.py
│── modals.py
│── theme.py
└── views.py
```

### 3. Execution
Launch the app via the terminal:
```bash
streamlit run main.py
```
