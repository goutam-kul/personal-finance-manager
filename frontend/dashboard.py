import streamlit as st
import requests
import jwt
import time 

# API Base URL
API_BASE_URL = "http://localhost:6000"
METABASE_SITE_URL = "http://localhost:3000"
METABASE_SECRET_KEY = "3f6ba348dd179e3a69f3e356ba71f922013486d08f31acf9a144e4cc712fa5d9"

payload = {
  "resource": {"dashboard": 3},
  "params": {
    
  },
  "exp": round(time.time()) + (60 * 10) # 10 minute expiration
}
token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true"

# Streamlit App
st.set_page_config(page_title="Finance Manager", layout="wide")
st.title("Personal Finance Manager")

# Tabs Layout
tabs = st.tabs([
    "Add Expense", 
    "View Expenses", 
    "Set/Update Budget", 
    "Remaining Budget", 
    "Monthly Expenses", 
    "Delete Expense", 
    "Category Summary", 
    "Spending Summary",
    "Visualization/Dashboard"
])

# Add Expense Tab
with tabs[0]:
    st.header("Add Expense")
    amount = st.number_input("Amount", min_value=1.0, step=0.01)
    category = st.selectbox("Select Category", ["food", "groceries", "transport", "entertainment", "health", "clothing", "miscellaneous",], key="add_expense_category")
    date = st.date_input("Date")
    date_str = date.strftime("%Y-%m-%d")
    if st.button("Add Expense"):
        data = {"amount": amount, "category": category, "date": date_str}
        response = requests.post(f"{API_BASE_URL}/expenses/", json=data)
        if response.status_code == 200:
            st.success("Expense added successfully!")
        else:
            st.error(f"Error: {response.json().get('detail')}") 

# View Expenses
with tabs[1]:
    st.header("Expenses")
    response = requests.get(f"{API_BASE_URL}/expenses/summary/")
    if response.status_code == 200:
        expenses = response.json()
        st.table(expenses)
    else:
        st.error("Failed to fetch expenses.")

# Set or Update budget
with tabs[2]:
    st.header("Set/Update a Budget")

    # Fetch pre-existing budgets from the API
    response = requests.get(f"{API_BASE_URL}/budget/show")
    if response.status_code == 200:
        budgets = response.json()
        st.subheader("Current Budgets:")
        for budget in budgets:
            st.markdown(f"- **{budget['category']}**: Limit = {budget['limit']}")

    else:
        st.warning("No budget found or failed to fetch existing budget")
    
    # Allow user to set or update a budget
    category = st.selectbox(
        "Select Category",
        ["food", "groceries", "transport", "entertainment", "health", "clothing", "miscellaneous"],
        key="budget_category"
    )
    limit = st.number_input("Enter Budget Limit", min_value=10.0, step=0.01, key="budget_limit")

    if st.button("Update", key="set_or_update_budget_button"):
        # Check if the already exists for the selected category
        response = requests.get(f"{API_BASE_URL}/budget/{category}")
        if response.status_code == 404: # Budget does not exist
            # Set a new budget
            data = {"category": category, "limit": limit}
            response = requests.post(f"{API_BASE_URL}/budget/", json=data)
            if response.status_code == 200:
                st.success(f"New Budget set for {category}.\nLimit = {limit}")
            else:
                st.error(f"Error: {response.json.get('detail')}")

        else: # Budget exists
            st.warning("Budget already exists, updating the budget to new limit.")
            data = {"new_limit": limit}
            response = requests.put(f"{API_BASE_URL}/budget/{category}", json=data)
            if response.status_code == 200:
                st.success(f"Budget for {category} has been updated.")
                st.success(f"NEW LIMIT: {limit}")
            else:
                st.error(f"Error: {response.json().get('detail')}")

with tabs[3]:
    st.header("Check Remaining Budget")
    category = st.selectbox("Select Category", ["food", "groceries", "transport", "entertainment", "health", "clothing", "miscellaneous"], key="remaining_budget_category")
    if st.button("Check"):
        response = requests.get(f"{API_BASE_URL}/budget/remaining/{category}")
        if response.status_code == 200:
            budget = response.json()
            st.table(budget)
        else:
            st.error(f"Error: {response.json().get('detail')}")

# Monthly Report Tab
with tabs[4]:
    st.header("Monthly Expense Report")
    year = st.number_input("Year", min_value=2000, max_value=2100, step=1, value=2025)
    month = st.number_input("Month", min_value=1, max_value=12, step=1, value=1)
    if st.button("Get Report"):
        response = requests.get(f"{API_BASE_URL}/expenses/report/{year}/{month}")
        if response.status_code == 200:
            report = response.json()
            st.table(report)
        else:
            st.error(f"Error: {response.json().get('detail')}")

# Delete Expense Tab
with tabs[5]:
    st.header("Delete an Expense")
    expense_id = st.number_input("Expense ID", min_value=1, step=1)
    if st.button("Delete"):
        response = requests.delete(f"{API_BASE_URL}/expenses/{expense_id}")
        if response.status_code == 200:
            st.success("Expense deleted successfully!")
        else:
            st.error(f"Error: {response.json().get('detail')}")  

# Category Summary Tab
with tabs[6]:
    st.header("Category-Wise Expense Summary")
    response = requests.get(f"{API_BASE_URL}/expenses/category-summary/")
    if response.status_code == 200:
        summary = response.json()
        st.table(summary)
    else:
        st.error(f"Error: {response.json().get('detail')}")

# Monthly Summary Tab
with tabs[7]:
    st.header("Monthly Expense Summary")
    response = requests.get(f"{API_BASE_URL}/expenses/monthly-summary/")
    if response.status_code == 200:
        summary = response.json()
        st.table(summary)
    else:
        st.error(f"Error: {response.json().get('detail')}")

with tabs[8]:
    st.header("Metabase Dashboard")
    st.markdown("Explore detailed visualization")
    st.components.v1.iframe(iframeUrl, height=1000)
st.markdown("---")  