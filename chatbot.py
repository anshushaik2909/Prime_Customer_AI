import pandas as pd
import re

class SmartChatbot:

    def __init__(self, df, delivered_orders):
        self.df = df
        self.delivered_orders = delivered_orders
        self.context = {}

    # --------------------------------
    # ORDER EXPLANATION FUNCTION
    # --------------------------------
    def explain_order(self, order_id):
        order = self.df[self.df["Delivery Number"].astype(str) == str(order_id)]

        if order.empty:
            return "❌ I couldn't find that order. Please check the order number."

        row = order.iloc[0]

        return f"""
📦 **Order {row['Delivery Number']} Explanation**

👤 **Customer:** {row['Customer Name']}  
⭐ **Customer Type:** {row['customer_type']}

### 📊 Why this order is prioritized:

• Customer Value Score: **{round(row['customer_priority_score'], 2)}**  
• Orders Today: **{row['orders_today']}**  
• Final Priority Score: **{round(row['order_priority_score'], 2)}**

### 🧠 Reason:
This order is ranked higher because the customer contributes significant business value and has active deliveries today.

🚀 Higher score → Higher priority in delivery queue
"""

    # --------------------------------
    # MAIN RESPONSE FUNCTION
    # --------------------------------
    def respond(self, prompt):
        p = prompt.lower()

        total_orders = len(self.df)
        delivered = len(self.delivered_orders)
        pending = total_orders - delivered

        # --------------------------------
        # DETECT ORDER NUMBER
        # --------------------------------
        order_match = re.search(r"\b\d{3,}\b", p)

        if order_match:
            order_id = order_match.group()
            self.context["last_order"] = order_id

            if any(word in p for word in ["why", "explain", "priority"]):
                return self.explain_order(order_id)

        # --------------------------------
        # CONTEXT: "this order"
        # --------------------------------
        if "this order" in p or "that order" in p:
            if "last_order" in self.context:
                return self.explain_order(self.context["last_order"])
            else:
                return "Please mention the order number."

        # --------------------------------
        # CONTEXT MEMORY FOR TOPIC
        # --------------------------------
        if "that" in p or "those" in p:
            if "last_topic" in self.context:
                p += " " + self.context["last_topic"]

        # --------------------------------
        # ORDER SUMMARY
        # --------------------------------
        if any(word in p for word in ["total", "orders today", "how many orders"]):
            self.context["last_topic"] = "orders"

            return f"""
📦 **Order Summary**

• Total Orders: **{total_orders}**  
• Delivered: **{delivered}**  
• Pending: **{pending}**

Let me know if you want deeper insights 🚀
"""

        # --------------------------------
        # PRIORITY ORDERS
        # --------------------------------
        if "priority" in p or "important" in p or "top" in p:
            self.context["last_topic"] = "priority"

            top_orders = self.df.head(5)[["Delivery Number", "Customer Name"]]

            return f"""
🔥 **Top Priority Orders**

{top_orders.to_string(index=False)}

These are ranked based on customer value and urgency.
"""

        # --------------------------------
        # CUSTOMER INSIGHTS
        # --------------------------------
        if "prime" in p:
            count = (self.df["customer_type"] == "PRIME").sum()
            return f"⭐ You have **{count}** prime customer orders today."

        if "non prime" in p:
            count = (self.df["customer_type"] == "NON-PRIME").sum()
            return f"⚪ You have **{count}** non-prime orders."

        if "most orders" in p or "top customer" in p:
            top_customer = (
                self.df.groupby("Customer Name")["Delivery Number"]
                .count()
                .idxmax()
            )
            return f"👑 **{top_customer}** has the highest number of orders."

        # --------------------------------
        # DELIVERY STATUS
        # --------------------------------
        if "delivered" in p:
            return f"✅ Delivered orders: **{delivered}**"

        if "pending" in p:
            return f"⏳ Pending orders: **{pending}**"

        # --------------------------------
        # EXPLANATION (GENERAL)
        # --------------------------------
        if "why" in p or "how" in p:
            return """
🤖 **How prioritization works:**

We calculate priority using:

• Customer business value (70%)  
• Number of past orders (30%)  
• Today's delivery load  

This ensures high-value and active customers are served first.
"""

        # --------------------------------
        # SMALL TALK (IMPORTANT FOR UX)
        # --------------------------------
        if any(word in p for word in ["hi", "hello", "hey"]):
            return "Hey! 👋 I'm your delivery assistant. Ask me anything about orders."

        if "thank" in p:
            return "You're welcome! 😊"

        if "who are you" in p:
            return "I'm your AI-powered delivery assistant 🤖 here to help you manage and understand your orders."

        # --------------------------------
        # FALLBACK (VERY IMPORTANT)
        # --------------------------------
        return """
🤖 I didn’t fully get that, but I can help with:

• 📦 Order status (total, pending, delivered)  
• 🔥 Priority orders  
• 👑 Customer insights  
• 📊 Order explanations  

Try asking:
👉 "Why is order 500123 prioritized?"  
👉 "Show top priority orders"  
👉 "How many pending?"  
👉 "Who is the top customer?"
"""