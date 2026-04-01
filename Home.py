import streamlit as st
from app import load_data, save_delivery
import requests

# ======================================
# PAGE CONFIG
# ======================================
st.set_page_config(
    page_title="DeliveryFlow Enterprise",
    layout="wide"
)

# ======================================
# STATIC THEME + CARD STYLING
# ======================================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #111217 !important;
    color: #e5e7eb !important;
}
.stApp, .stMarkdown, .stText, .stCaption, .stSubheader, .stHeader, .stTitle, label, p, span, div, small, strong, em,
[data-testid="stSidebar"], [data-testid="stSidebar"] * { color: #e5e7eb !important; }

section[data-testid="stSidebar"] { background-color: #282A36 !important; }
header[data-testid="stHeader"] { background: #111217 !important; }

[data-testid="stMetric"] {
    background: #0f274f !important;
    border: 1px solid #1f3b6d;
    border-radius: 12px;
    padding: 10px;
}

.floating-btn button {
    position: fixed;
    bottom: 25px;
    right: 25px;
    height: 60px;
    width: 60px;
    border-radius: 50%;
    font-size: 26px;
    background: linear-gradient(135deg,#1d4ed8,#f97316);
    color: white !important;
    border: none;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.35);
    z-index: 9999;
}

.chat-panel {
    position: fixed;
    bottom: 100px;
    right: 25px;
    width: 360px;
    max-height: 520px;
    overflow-y: auto;
    background: #0f274f;
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
    z-index: 9999;
}

.delivery-card {
    background: white;
    color: #111827 !important;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 18px;
    border: 2px solid #f97316;
    box-shadow: 0 12px 28px rgba(0,0,0,0.25);
    transition: all 0.25s ease;
}
.delivery-card * { color: #111827 !important; }

.delivery-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 36px rgba(0,0,0,0.35);
}

.card-badge {
    background: linear-gradient(135deg,#1d4ed8,#f97316);
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ======================================
# SESSION STATE
# ======================================
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ======================================
# RESET BUTTON
# ======================================
if st.button("🔄 Reset Delivery State"):
    st.session_state.delivered_orders = []
    save_delivery([])
    st.rerun()

# ======================================
# LOAD DATA
# ======================================
df, saved_delivered = load_data()
if "delivered_orders" not in st.session_state:
    st.session_state.delivered_orders = saved_delivered

# ======================================
# HEADER
# ======================================
st.title("🚚 Delivery Operations")
st.caption("AI-powered order prioritization")
st.page_link("pages/Analytics.py", label="📊 View Analytics Dashboard")

# ======================================
# FILTER DATA
# ======================================
already_delivered = df[df["Delivery Number"].isin(st.session_state.delivered_orders)]
remaining_orders = df[~df["Delivery Number"].isin(st.session_state.delivered_orders)]

# ======================================
# DELIVERY CONFIG
# ======================================
if len(remaining_orders) > 0:
    max_deliveries = st.number_input(
        "Enter deliveries",
        min_value=1,
        max_value=len(remaining_orders),
        value=1
    )
else:
    st.success("🎉 All orders already delivered!")
    max_deliveries = 0

deliver_now = remaining_orders.head(max_deliveries)
pending = remaining_orders.iloc[max_deliveries:]

# ======================================
# METRICS
# ======================================
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Orders", len(df))
m2.metric("Already Delivered", len(already_delivered))
m3.metric("Deliver Now", len(deliver_now))
m4.metric("Pending", len(pending))
st.divider()

# ======================================
# CARD RENDER FUNCTION
# ======================================
def render_card(idx, row, status, badge, extra=""):
    prime_star = " ⭐" if row["customer_type"] == "PRIME" else ""
    st.markdown(f"""
<div class="delivery-card">
<div class="card-header">
<span>#{idx} Order {row['Delivery Number']}{prime_star}</span>
<span class="card-badge">{badge}</span>
</div>
<div class="card-section">
👤 <b>{row['Customer Name']}</b>
</div>
{extra}
<div class="card-section">
{status}
</div>
</div>
""", unsafe_allow_html=True)

# ======================================
# MAIN LAYOUT
# ======================================
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("✅ Already Delivered")
    for i, (_, row) in enumerate(already_delivered.iterrows(), 1):
        render_card(i, row, "✔ Delivered", "DELIVERED")

with c2:
    st.subheader("🚚 Deliver Now")
    if not deliver_now.empty:
        if st.button("🚀 Deliver All"):
            bulk = deliver_now["Delivery Number"].tolist()
            st.session_state.delivered_orders = list(set(
                st.session_state.delivered_orders + bulk
            ))
            save_delivery(st.session_state.delivered_orders)
            st.rerun()

    for i, (_, row) in enumerate(deliver_now.iterrows(), 1):
        explanation = row.get("ai_explanation", "Prioritized based on urgency.")
        extra = f"""
<div class="card-section">
⭐ Score: {round(row['order_priority_score'],2)} |
📦 Today: {row['orders_today']}
</div>
<div class="ai-box">
🤖 {explanation}
</div>
"""
        render_card(i, row, "", "PRIORITY", extra)

with c3:
    st.subheader("⏳ Pending")
    for i, (_, row) in enumerate(pending.iterrows(), 1):
        render_card(i, row, "⏳ Pending", "PENDING")

# ======================================
# FLOATING CHAT
# ======================================
with st.container():
    st.markdown('<div class="floating-btn">', unsafe_allow_html=True)
    if st.button("💬"):
        st.session_state.chat_open = not st.session_state.chat_open
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================
# CHAT PANEL (WORKING - NO API NEEDED)
# ======================================
if st.session_state.chat_open:
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Assistant")

    for role, msg in st.session_state.chat_history:
        st.chat_message(role).write(msg)

    prompt = st.chat_input("Ask anything…")

    if prompt:
        st.session_state.chat_history.append(("user", prompt))

        # SIMPLE SMART RESPONSES (NO API)
        if "total" in prompt.lower():
            reply = f"Total orders: {len(df)}"
        elif "delivered" in prompt.lower():
            reply = f"Delivered orders: {len(already_delivered)}"
        elif "pending" in prompt.lower():
            reply = f"Pending orders: {len(pending)}"
        elif "priority" in prompt.lower():
            top_orders = deliver_now.head(3)["Delivery Number"].tolist()
            reply = f"Top priority orders: {top_orders}"
        else:
            reply = "I can help with delivery insights. Try asking about total, pending, or priority orders."

        st.session_state.chat_history.append(("assistant", reply))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)