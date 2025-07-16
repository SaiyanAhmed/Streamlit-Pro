import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Initialize default values
default_toa = None
default_avg_per = None
default_gm_week = None

# --- Sidebar Input with keys ---
with st.sidebar:
    st.header("📊 THP Staffing")

    # Reset button
    if st.button("🔄 Reset Inputs"):
        # Reset the session state values
        st.session_state['toa'] = default_toa
        st.session_state['avg_per'] = default_avg_per
        st.session_state['gm_week'] = default_gm_week

    toa = st.number_input("Insert Number of TOA", value=st.session_state.get('toa', default_toa), 
                          key='toa', placeholder="Ex. 15")
    avg_per = st.number_input("Insert AVG (%)", value=st.session_state.get('avg_per', default_avg_per), 
                              key='avg_per', placeholder="Ex. 16%")
    gm_week = st.number_input("Insert GM/Week ($)", value=st.session_state.get('gm_week', default_gm_week), 
                              key='gm_week', placeholder="Ex. $400")
    
# --- Validation ---
if toa is None or avg_per is None or gm_week is None:
    st.warning("Please fill in all the inputs in the sidebar.")
    st.stop()

if toa <= 0 or avg_per < 0 or gm_week <= 0:
    st.error("Inputs must be positive numbers. TOA and GM/Week must be greater than 0.")
    st.stop()

# --- Commission Logic ---
monthly_gp = (gm_week * 4.3) * toa

def get_margin_commission(margin):
    if margin < 10.00:
        return 0.00
    elif margin < 17.00:
        return 3.00
    elif margin < 17.51:
        return 3.25
    elif margin < 18.00:
        return 3.50
    elif margin < 18.51:
        return 3.75
    elif margin < 19.00:
        return 4.00
    elif margin < 19.51:
        return 4.25
    elif margin < 20.00:
        return 4.50
    elif margin < 20.51:
        return 4.75
    elif margin < 21.00:
        return 5.00
    elif margin < 21.51:
        return 5.25
    elif margin < 22.00:
        return 5.50
    elif margin < 22.51:
        return 5.75
    elif margin < 23.00:
        return 6.00
    elif margin < 23.51:
        return 6.25
    elif margin < 24.00:
        return 6.50
    elif margin < 24.51:
        return 6.75
    elif margin < 25.00:
        return 7.00
    else:
        return 7.25

def get_nurse_commission(nurse_count):
    if nurse_count < 11:
        return 2.00
    elif nurse_count < 13:
        return 2.25
    elif nurse_count < 16:
        return 2.50
    elif nurse_count < 18:
        return 2.75
    elif nurse_count < 21:
        return 3.00
    elif nurse_count < 24:
        return 3.25
    elif nurse_count < 27:
        return 3.50
    elif nurse_count < 30:
        return 3.75
    else:
        return 4.00

marg_comm = get_margin_commission(avg_per)
toa_comm = get_nurse_commission(toa)
monthly_comm = monthly_gp * (marg_comm + toa_comm) / 100

# --- Create a single entry DataFrame ---
df = pd.DataFrame([{
    "TOA": toa,
    "AVG %": avg_per,
    "GM $/Week": gm_week,
    "Monthly GP ($)": monthly_gp,
    "Margin %": marg_comm,
    "TOA %": toa_comm,
    "Monthly Commission ($)": monthly_comm
}])

# --- Styled DataFrame ---
styled_df = df.style \
    .format({
        "TOA": "{:.2f}",
        "AVG %": "{:.2f}%",
        "GM $/Week": "${:,.2f}",
        "Monthly GP ($)": "${:,.2f}",
        "Margin %": "{:.2f}%",
        "TOA %": "{:.2f}%",
        "Monthly Commission ($)": "${:,.2f}"
    }) \
    .background_gradient(subset=["Monthly GP ($)", "Monthly Commission ($)"], cmap="Greens") \
    .set_properties(**{"text-align": "center", "font-size": "16px"}) \
    .set_table_styles([{
        'selector': 'th',
        'props': [('font-size', '16px'), ('text-align', 'center')]
    }])

# --- Export to Excel Function ---
def to_excel_with_formatting(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Summary', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        for i, col in enumerate(df.columns):
            col_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, col_len)

        money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
        percent_fmt = workbook.add_format({'num_format': '0.00%'})
        worksheet.set_column('D:D', None, money_fmt)  # Monthly GP
        worksheet.set_column('G:G', None, money_fmt)  # Monthly Commission
        worksheet.set_column('B:B', None, percent_fmt)  # AVG %
        worksheet.set_column('E:E', None, percent_fmt)  # Margin %
        worksheet.set_column('F:F', None, percent_fmt)  # TOA %

    output.seek(0)
    return output

excel_file = to_excel_with_formatting(df)

# --- Display Output ---
st.title("💰 Commission Calculator")
st.markdown("Here is your calculated commission:")
st.dataframe(styled_df, use_container_width=True)

# Prepare data for bar chart
bar_df = pd.melt(df, value_vars=["Monthly Commission ($)"],
                 var_name="Metric", value_name="Amount")

# Plot horizontal bar chart
fig = px.bar(
    bar_df,
    y="Metric",
    x="Amount",
    orientation='h',
    text_auto='.2s',
    title="Monthly Commission",
    color="Metric",
    color_discrete_map={
        "Monthly Commission ($)": "steelblue"
    }
)

fig.update_layout(yaxis_title="", xaxis_title="Amount ($)", showlegend=False)
st.subheader("📊 Monthly Commission")
st.plotly_chart(fig, use_container_width=True)

# --- Download Option ---
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download This Results as CSV",
    data=csv,
    file_name='commission_result.csv',
    mime='text/csv'
)