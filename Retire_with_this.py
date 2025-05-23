import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Retirement Corpus Calculator", layout="centered")

# Custom CSS styling
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        h1 {
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Smart SWP Planner: Inflation-Proof")
st.markdown("Choose whether you want to **calculate required investment** or **check how long your current investment will last**.")

# Formatter for Indian currency style
def indian_number_format(number):
    num_str = str(int(round(number)))
    if len(num_str) <= 3:
        return num_str
    last_three = num_str[-3:]
    rest = num_str[:-3]
    rest_with_commas = ''
    while len(rest) > 2:
        rest_with_commas = ',' + rest[-2:] + rest_with_commas
        rest = rest[:-2]
    rest_with_commas = rest + rest_with_commas
    return rest_with_commas + ',' + last_three

# Radio selector
mode = st.radio("Select Mode", ["Calculate Required Investment", "Calculate Investment Duration"], horizontal=True)

# === MODE 1: CALCULATE REQUIRED INVESTMENT ===
if mode == "Calculate Required Investment":
    duration_years = st.number_input("Investment Duration (Years)", value=100, step=1)
    final_balance = st.number_input("Final Balance Desired (₹)", value=0, step=100000)
    monthly_withdrawal = st.number_input("Monthly Withdrawal (₹)", value=63200, step=1000)

    annual_r = st.number_input("Expected Annual Return (%)", value=6.1, step=0.1, format="%.2f")
    annual_g = st.number_input("Annual Increase in Withdrawal (%)", value=6.0, step=0.1, format="%.2f")

    # Convert to monthly rates
    monthly_r = (1 + annual_r / 100) ** (1 / 12) - 1
    monthly_g = (1 + annual_g / 100) ** (1 / 12) - 1

    if st.button("Calculate Investment Required"):
        total_months = int(duration_years * 12)
    
        # Present Value of growing annuity (SWP)
        pv_annuity = monthly_withdrawal * (1 - ((1 + monthly_g) / (1 + monthly_r)) ** total_months) / (monthly_r - monthly_g)
    
        # Present Value of final balance goal
        pv_final = final_balance / ((1 + annual_r / 100) ** duration_years)
    
        # Total investment required today
        total_investment = pv_annuity + pv_final
    
        # Future Value of the investment (for verification)
        future_value = total_investment * ((1 + annual_r / 100) ** duration_years)
    
        # Future Value of SWP withdrawals
        fv_annuity = monthly_withdrawal * (((1 + monthly_r) ** total_months - (1 + monthly_g) ** total_months) / (monthly_r - monthly_g))
    
        st.success(f"""
        You need to invest ₹{total_investment / 10000000:.2f} Crores today.
    
        """)

        # Plotting
        months = np.arange(1, total_months + 1)
        years = months / 12
        withdrawal_series = monthly_withdrawal * ((1 + monthly_g) ** months)
        balance_series = []
        balance = total_investment

        for w in withdrawal_series:
            balance_series.append(balance)
            balance = balance * (1 + monthly_r) - w

        step = max(1, int(total_months / 100))
        frames = [
            go.Frame(
                data=[
                    go.Scatter(x=years[:k], y=np.array(balance_series[:k]) / 1e7, mode='lines', name='Investment Balance', yaxis="y1"),
                    go.Scatter(x=years[:k], y=np.array(withdrawal_series[:k]) / 1e5, mode='lines', name='Monthly Withdrawal', yaxis="y2")
                ]
            )
            for k in range(1, total_months, step)
        ]

        fig = go.Figure(
            data=[
                go.Scatter(x=[], y=[], mode='lines', name='Investment Balance', yaxis="y1"),
                go.Scatter(x=[], y=[], mode='lines', name='Monthly Withdrawal', yaxis="y2")
            ],
            layout=go.Layout(
                title="Investment & Withdrawal Over Time",
                xaxis=dict(title="Year"),
                yaxis=dict(title="Investment Balance (₹ Cr)", side="left"),
                yaxis2=dict(title="Withdrawal (₹ Lakh)", side="right", overlaying="y"),
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    buttons=[dict(
                        label="Play",
                        method="animate",
                        args=[None, {"frame": {"duration": 100, "redraw": True},
                                     "fromcurrent": True,
                                     "transition": {"duration": 0}}]
                    )]
                )]
            ),
            frames=frames
        )

        st.plotly_chart(fig, use_container_width=True)

# === MODE 2: CALCULATE INVESTMENT DURATION ===
elif mode == "Calculate Investment Duration":
    monthly_withdrawal = st.number_input("Initial Monthly Withdrawal (₹)", value=63200, step=1000)
    inflation_rate = st.number_input("Annual Inflation Rate (%)", value=6.0, step=0.1)
    return_rate = st.number_input("Expected Annual Return (%)", value=3.0, step=0.1)

    current_investment_lakhs = st.number_input(
        "Current Investment (₹ in Lakhs)",
        min_value=0.0,
        value=20.0,
        step=1.0,
        format="%.2f"
    )

    monthly_r = (1 + return_rate / 100) ** (1 / 12) - 1
    monthly_g = (1 + inflation_rate / 100) ** (1 / 12) - 1

    current_investment_rupees = current_investment_lakhs * 100000
    formatted_investment = indian_number_format(current_investment_rupees)
    st.write(f"Current Investment in Rupees: ₹{formatted_investment}")

    if st.button("Calculate Duration"):
        balance = current_investment_rupees
        months = 0

        while balance > 0:
            withdrawal = monthly_withdrawal * ((1 + monthly_g) ** months)
            balance = balance * (1 + monthly_r) - withdrawal
            if balance < 0:
                break
            months += 1

        years = months // 12
        rem_months = months % 12
        st.success(f"Your investment will last for {years} years and {rem_months} months.")
