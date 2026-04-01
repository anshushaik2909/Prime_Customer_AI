import streamlit as st
import pandas as pd
from app import load_data
import plotly.express as px

# ======================================
# PAGE CONFIG
# ======================================

st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide"
)

# ======================================
# STATIC THEME (MATCHES ui1.py)
# ======================================

st.markdown("""
<style>

/* ===== FORCE STATIC DARK BACKGROUND ===== */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #111217 !important;
    color: #e5e7eb !important;
}

section[data-testid="stSidebar"] {
    background-color: #282A36 !important;
}

header[data-testid="stHeader"] {
    background: #111217 !important;
}

/* ===== METRICS ===== */
[data-testid="stMetric"] {
    background: #0f274f !important;
    border: 1px solid #1f3b6d;
    border-radius: 12px;
    padding: 10px;
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"] {
    background-color: white !important;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ======================================
# HEADER
# ======================================

st.title("📊 DeliveryFlow Analytics Dashboard")
st.caption("Interactive delivery intelligence")

# ======================================
# LOAD DATA
# ======================================

df, _ = load_data()

# ======================================
# SIDEBAR FILTERS
# ======================================

st.sidebar.header("🎛 Filters")

prime_filter = st.sidebar.selectbox(
    "Customer Type",
    ["All", "PRIME", "NON-PRIME"]
)

customer_filter = st.sidebar.multiselect(
    "Select Customer",
    options=sorted(df["Customer Name"].unique())
)

search_order = st.sidebar.text_input("Search Order Number")

# ======================================
# APPLY FILTERS
# ======================================

filtered_df = df.copy()

if prime_filter != "All":
    filtered_df = filtered_df[
        filtered_df["customer_type"] == prime_filter
    ]

if customer_filter:
    filtered_df = filtered_df[
        filtered_df["Customer Name"].isin(customer_filter)
    ]

if search_order:
    filtered_df = filtered_df[
        filtered_df["Delivery Number"]
        .astype(str)
        .str.contains(search_order)
    ]

# ======================================
# METRICS
# ======================================

prime_count = (filtered_df["customer_type"] == "PRIME").sum()
non_prime_count = (filtered_df["customer_type"] == "NON-PRIME").sum()

m1, m2, m3 = st.columns(3)

m1.metric("Filtered Orders", len(filtered_df))
m2.metric("Prime Orders", prime_count)
m3.metric("Non Prime Orders", non_prime_count)

st.divider()

# ======================================
# VISUALIZATIONS
# ======================================

col1, col2 = st.columns(2)

# -------------------------
# PIE CHART
# -------------------------

with col1:

    pie_df = pd.DataFrame({
        "Customer Type": ["Prime", "Non Prime"],
        "Count": [prime_count, non_prime_count]
    })

    fig = px.pie(
        pie_df,
        names="Customer Type",
        values="Count",
        title="Prime vs Non Prime",
        color="Customer Type",
        color_discrete_map={
            "Prime": "#1d4ed8",     # dark blue
            "Non Prime": "#f97316"  # orange
        }
    )

    fig.update_layout(
        paper_bgcolor="#111217",
        plot_bgcolor="#111217",
        font_color="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# BAR CHART
# -------------------------

with col2:

    orders_chart = (
        filtered_df.groupby("Customer Name")["Delivery Number"]
        .count()
        .reset_index(name="Orders")
    )

    fig2 = px.bar(
        orders_chart,
        x="Customer Name",
        y="Orders",
        title="Orders per Customer",
        color="Orders",
        color_continuous_scale=[
            "#1d4ed8",
            "#f97316"
        ]
    )

    fig2.update_layout(
        paper_bgcolor="#111217",
        plot_bgcolor="#111217",
        font_color="white"
    )

    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ======================================
# TABLE VIEW
# ======================================

st.subheader("📋 Detailed Filtered Orders")

st.dataframe(filtered_df, use_container_width=True)

# ======================================
# EMPTY STATE
# ======================================

if filtered_df.empty:
    st.warning("No data matches current filters.")
