import streamlit as st

# ---------------- CORE LOGIC ---------------- #

def required_staggered_capital(
    base_capital,
    spot_price,
    final_buy_price,
    steps,
    initial_leg_percent,
    breakeven,
    option_loss,
    coverage_ratio=0.70,
    max_iter=300
):
    capital = base_capital

    for _ in range(max_iter):
        first_leg = capital * (initial_leg_percent / 100)
        remaining = capital - first_leg

        step_gap = (final_buy_price - spot_price) / (steps - 1)

        total_qty = 0
        total_cost = 0

        for i in range(steps):
            price = spot_price + i * step_gap
            cap = first_leg if i == 0 else remaining / (steps - 1)

            qty = int(round(cap / price))
            actual_capital = qty * price

            total_qty += qty
            total_cost += actual_capital

        if total_qty == 0:
            capital *= 1.05
            continue

        avg_price = total_cost / total_qty
        equity_profit = (breakeven - avg_price) * total_qty

        if equity_profit >= coverage_ratio * option_loss:
            return capital, equity_profit, avg_price, total_qty

        capital *= 1.02

    return capital, equity_profit, avg_price, total_qty


# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(page_title="Staggered Buying Tool", layout="centered")

st.title("📊 Staggered Buying Calculator")
st.caption("Auto capital sizing for hedged staggered buying")

st.divider()

share_name = st.text_input("Share / Symbol", value="RELIANCE")
spot_price = st.number_input("Current Spot Price", value=1500.0)
lot_size = st.number_input("Lot Size", value=500)

st.subheader("📌 Call Spread Details")
call_sell_strike = st.number_input("Call SELL Strike", value=1535.0)
call_sell_price = st.number_input("Call SELL Premium", value=15.0)

call_buy_strike = st.number_input("Call BUY Strike", value=1545.0)
call_buy_price = st.number_input("Call BUY Premium", value=10.0)

st.subheader("📌 Execution Plan")
steps = st.slider("Total Buy Steps", min_value=2, max_value=10, value=5)
initial_leg_percent = st.slider("Initial Leg %", min_value=0, max_value=100, value=40)

coverage_ratio = st.slider("Required MTM Coverage (%)", 50, 100, 70) / 100

st.divider()

if st.button("🚀 Calculate"):
    net_credit = call_sell_price - call_buy_price
    spread_width = abs(call_sell_strike - call_buy_strike)
    option_loss = (spread_width - net_credit) * lot_size

    breakeven = call_sell_strike + net_credit
    distance_percent = (breakeven - spot_price) / spot_price

    if distance_percent <= 0:
        st.error("Breakeven must be above spot price")
    else:
        base_capital = option_loss / distance_percent

        staggered_capital, profit_at_be, avg_price, total_qty = required_staggered_capital(
            base_capital,
            spot_price,
            call_sell_strike,
            steps,
            initial_leg_percent,
            breakeven,
            option_loss,
            coverage_ratio
        )

        st.subheader("📈 Option & Capital Metrics")
        st.write(f"**Max Option Loss:** ₹{round(option_loss,2)}")
        st.write(f"**Breakeven Price:** {round(breakeven,2)}")
        st.write(f"**Capital (Lump Sum):** ₹{round(base_capital,2)}")
        st.write(f"**Capital (Staggered):** ₹{round(staggered_capital,2)}")

        st.subheader("🧮 Staggered Buy Plan")

        first_leg = staggered_capital * (initial_leg_percent / 100)
        remaining = staggered_capital - first_leg
        step_gap = (call_sell_strike - spot_price) / (steps - 1)

        for i in range(steps):
            price = spot_price + i * step_gap
            cap = first_leg if i == 0 else remaining / (steps - 1)
            qty = int(round(cap / price))

            st.write(
                f"Step {i+1} → Price: {round(price,2)}, "
                f"Qty: {qty}, Capital: ₹{round(qty * price,2)}"
            )

        st.subheader("✅ Final Validation @ Breakeven")
        st.write(f"**Average Buy Price:** ₹{round(avg_price,2)}")
        st.write(f"**Total Quantity:** {total_qty}")
        st.write(f"**Equity MTM @ BE:** ₹{round(profit_at_be,2)}")

        if profit_at_be >= coverage_ratio * option_loss:
            st.success("MTM Positive at Breakeven ✔️")
        else:
            st.warning("Hedge insufficient ❗")
