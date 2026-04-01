import pandas as pd
from pathlib import Path

# --------------------------------
# PATH SETUP
# --------------------------------

PROJECT_ROOT = Path.cwd()
data_path = PROJECT_ROOT / "data" / "customer_data.xlsx"
output_dir = PROJECT_ROOT / "output"
output_dir.mkdir(exist_ok=True)

STATE_FILE = output_dir / "delivery_state.xlsx"


# --------------------------------
# LOAD DATA FUNCTION
# --------------------------------

def load_data():

    customer_master = pd.read_excel(data_path, sheet_name="Customer Master data")
    history1 = pd.read_excel(data_path, sheet_name="Customer History data 1 ")
    history2 = pd.read_excel(data_path, sheet_name="customer history data 2")
    today_schedule = pd.read_excel(data_path, sheet_name="Today Delivery Schedule")

    for df in [customer_master, history1, history2, today_schedule]:
        df.columns = df.columns.str.strip()

    history = pd.concat([history1, history2], ignore_index=True)

    customer_value = (
        history.groupby("Customer Number")
        .agg(
            total_business_value=("Net business value", "sum"),
            order_count=("Delivery number", "count")
        )
        .reset_index()
    )

    profile = customer_master.merge(customer_value, on="Customer Number", how="left").fillna(0)

    profile["customer_priority_score"] = (
        profile["total_business_value"] * 0.7 +
        profile["order_count"] * 0.3
    )

    threshold = profile["customer_priority_score"].quantile(0.7)

    profile["customer_type"] = profile["customer_priority_score"].apply(
        lambda x: "PRIME" if x >= threshold else "NON-PRIME"
    )

    today_plan = today_schedule.merge(profile, on="Customer Number", how="left")

    today_plan["orders_today"] = (
        today_plan.groupby("Customer Number")["Delivery Number"].transform("count")
    )

    today_plan["order_priority_score"] = (
        today_plan["customer_priority_score"] +
        today_plan["orders_today"] * 0.05
    )

    today_plan = today_plan.sort_values(
        by=["order_priority_score", "Delivery Number"],
        ascending=[False, True]
    )

    # Load delivery state
    if STATE_FILE.exists():
        state_df = pd.read_excel(STATE_FILE)
        delivered = state_df["Delivery Number"].tolist()
    else:
        delivered = []

    return today_plan, delivered


# --------------------------------
# SAVE DELIVERY FUNCTION
# --------------------------------

def save_delivery(delivered_list):

    df = pd.DataFrame({
        "Delivery Number": delivered_list
    })

    df.to_excel(STATE_FILE, index=False)
