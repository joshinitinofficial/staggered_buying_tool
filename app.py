import streamlit as st
import pandas as pd

# ---------------- CORE LOGIC ---------------- #

def required_staggered_capital(
    spot_price,
    final_buy_price,
    steps,
    initial_leg_percent,
    breakeven,
    required_shares,
):
    first_leg_percent = initial_leg_percent / 100
    rows = []

    step_gap = (final_buy_price - spot_price) / (steps - 1)
    total_qty = 0
    total_cost = 0

    # Start with large enough capital (will stop early)
    capital_guess = required_shares * spot_price * 1.5

    first_leg = int(capital_guess * first_leg_percent)
    remaining = capital_guess - first_leg

    for i in range(steps):
        price = spot_price + i * step_gap
        cap = first_leg if i == 0 else remaining // (steps - 1)

        qty = int(round(cap / price))
        actual_capital = qty * price

        total_qty += qty
        total_cost += actual_capital

        rows.append({
            "Step": i + 1,
            "Buy Price": round(price, 2),
            "Quantity": qty,
            "Capital Used (₹)": int(actual_capital)
        })

        # ✅ STOP once covered
        if total_qty >= required_shares:
            break

    avg_price = total_cost / total_qty
    return rows, total_qty, avg_price, int(total_cost)


# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(page_title="Staggered Buying Tool", layout="centered")

st.title("📊 Staggered Buying Calculator")
st.caption("Covered Call & Hedged Staggered Buying Tool")

st.divider()

spot_price = st.number_input("Current Spot Price", value=1500.0)
lot_size = st.number_input("Lot Size (per option)", value=500)
option_lots = st.number_input("Number of Option Lots Executed", min_value=1, value=1)

required_shares = lot_size * option_lots

st.subheader("📌 Call Details")
call_sell_strike = st.number_input("Call SELL Strike", value=1535.0)
call_sell_price = st.number_input("Call SELL Premium", value=15.0)

call_buy_strike = st.number_input("Call BUY Strike", value=1800.0)
call_buy_price = st.number_input("Call BUY Premium", value=1.0)

# 🔹 Covered Call Toggle
manual_covered_call = st.checkbox("Covered Call Mode (ignore spread risk)")

# 🔹 Auto detect covered call
auto_covered_call = call_buy_strike >= call_sell_strike * 1.10
covered_call_mode = manual_covered_call or auto_covered_call

st.subheader("📌 Execution Plan")
steps = st.slider("Maximum Buy Steps", min_value=2, max_value=10, value=5)
initial_leg_percent = st.slider("Initial Leg %", 0, 100, 40)

st.divider()

if st.button("🚀 Calculate"):

    breakeven = call_sell_strike + (call_sell_price - call_buy_price)

    if covered_call_mode:
        option_loss = 0
    else:
        spread_width = abs(call_sell_strike - call_buy_strike)
        net_credit = call_sell_price - call_buy_price
        option_loss = int((spread_width - net_credit) * required_shares)

    # -------- METRICS --------
    st.subheader("📈 Option & Capital Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Required Shares", required_shares)
    c2.metric("Breakeven Price", round(breakeven, 2))
    c3.metric("Max Option Loss", f"₹{option_loss}")

    if covered_call_mode:
        st.success("Covered Call Mode ACTIVE")

    st.divider()

    # -------- STAGGERED BUY PLAN --------
    st.markdown("## 📋 **STAGGERED BUY PLAN**")

    rows, total_qty, avg_price, capital_used = required_staggered_capital(
        spot_price,
        call_sell_strike,
        steps,
        initial_leg_percent,
        breakeven,
        required_shares,
    )

    df = pd.DataFrame(rows)

    styled_df = df.style\
        .hide(axis="index")\
        .applymap(lambda x: "color: green; font-weight: bold;", subset=["Buy Price"])\
        .applymap(lambda x: "color: #003366; font-weight: bold;", subset=["Capital Used (₹)"])

    st.dataframe(styled_df, use_container_width=True)

    st.divider()

    # -------- FINAL VALIDATION --------
    st.subheader("✅ Final Validation")

    f1, f2, f3 = st.columns(3)
    f1.metric("Avg Buy Price", f"₹{round(avg_price,2)}")
    f2.metric("Total Shares Bought", total_qty)
    f3.metric("Total Capital Used", f"₹{capital_used}")

    if total_qty >= required_shares:
        st.success("Position fully COVERED ✔️")
    else:
        st.warning("Position not fully covered ❗")
