import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Retail Performance Dashboard", layout="wide")

# --- CSS INJECTION TO FORCE DARK THEME ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #262730; }
    [data-testid="stMetricValue"] { color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- STEP 1: DATA LOADING & CLEANING ---


@st.cache_data
def load_data():
    df = pd.read_csv('Book1.csv')
    df.columns = df.columns.str.strip()

    # 1. Convert to datetime
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])

    # 2. CREATE THE MISSING COLUMNS
    df['Year'] = df['Order_Date'].dt.year
    df['Month'] = df['Order_Date'].dt.month
    df['Month_Name'] = df['Order_Date'].dt.month_name()

    # 3. Standardize numeric columns
    numeric_cols = ['Net_Revenue', 'Gross_Profit', 'Discount_Amount',
                    'COGS', 'Shipping_Cost', 'Unit_Price']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Quantity'] = df['Quantity'].fillna(0).astype(int)
    df['Days_to_Ship'] = df['Days_to_Ship'].fillna(0).astype(int)
    df['Customer_Rating'] = pd.to_numeric(
        df['Customer_Rating'], errors='coerce')
    df['Is_Returned_Bool'] = df['Is_Returned'].map({'Yes': 1, 'No': 0})

    return df


df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Dashboard Filters")

years = sorted(df['Year'].unique())
year_filter = st.sidebar.multiselect(
    "Select Year", options=years, default=years)

month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
available_months = [m for m in month_order if m in df['Month_Name'].unique()]
month_filter = st.sidebar.multiselect(
    "Select Month", options=available_months, default=available_months)

region_filter = st.sidebar.multiselect(
    "Select Region", options=df['Region'].unique(), default=df['Region'].unique())
category_filter = st.sidebar.multiselect(
    "Select Category", options=df['Category'].unique(), default=df['Category'].unique())

# --- APPLY FILTERS ---
filtered_df = df[
    (df['Year'].isin(year_filter)) &
    (df['Month_Name'].isin(month_filter)) &
    (df['Region'].isin(region_filter)) &
    (df['Category'].isin(category_filter))
].copy()

# --- TOP KPI ROW ---
st.title("📊 Retail Performance Insights")
st.markdown("---")

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
else:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Revenue", f"${filtered_df['Net_Revenue'].sum():,.0f}")
    with kpi2:
        st.metric("Gross Profit", f"${filtered_df['Gross_Profit'].sum():,.0f}")
    with kpi3:
        st.metric("Total Orders", f"{len(filtered_df):,}")
    with kpi4:
        cust_orders = filtered_df.groupby('Customer_ID')['Order_ID'].count()
        repeat_rate = (cust_orders > 1).sum() / \
            len(cust_orders) * 100 if len(cust_orders) > 0 else 0
        st.metric("Repeat Customer %", f"{repeat_rate:.1f}%")

    st.markdown("---")

    # Helper function for chart styling - MOVED AND RE-INDENTED
    def apply_dark_style(fig):
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#FAFAFA")
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        return fig

    # ROW 1: Trend and Bar Chart
    col1, col2 = st.columns((3, 2))
    with col1:
        filtered_df['YearMonth'] = filtered_df['Order_Date'].dt.to_period(
            'M').astype(str)
        monthly_rev = filtered_df.groupby(
            'YearMonth')['Net_Revenue'].sum().reset_index()
        fig_trend = px.line(monthly_rev, x='YearMonth', y='Net_Revenue',
                            title="Monthly Revenue Trend", markers=True)
        st.plotly_chart(apply_dark_style(fig_trend), width='stretch')

    with col2:
        rev_cat = filtered_df.groupby('Category')['Net_Revenue'].sum(
        ).reset_index().sort_values('Net_Revenue')
        fig_cat = px.bar(rev_cat, x='Net_Revenue', y='Category', orientation='h',
                         title="Revenue by Category", color='Net_Revenue', color_continuous_scale='Viridis')
        st.plotly_chart(apply_dark_style(fig_cat), width='stretch')

    # ROW 2: Pie Charts
    col3, col4, col5 = st.columns(3)
    with col3:
        fig_reg = px.pie(filtered_df, values='Net_Revenue',
                         names='Region', hole=0.4, title="Revenue by Region")
        st.plotly_chart(apply_dark_style(fig_reg), width='stretch')
    with col4:
        fig_seg = px.pie(filtered_df, names='Customer_Segment',
                         title="Customer Distribution")
        st.plotly_chart(apply_dark_style(fig_seg), width='stretch')
    with col5:
        aov_seg = filtered_df.groupby('Customer_Segment')[
            'Net_Revenue'].mean().reset_index()
        fig_aov = px.bar(aov_seg, x='Customer_Segment',
                         y='Net_Revenue', title="Average Order Value")
        st.plotly_chart(apply_dark_style(fig_aov), width='stretch')

    # Operations Section
    st.markdown("### Operations & Logistics")
    col6, col7 = st.columns(2)
    with col6:
        return_rate = (filtered_df.groupby('Category')[
                       'Is_Returned_Bool'].mean() * 100).reset_index()
        fig_ret = px.bar(return_rate, x='Category', y='Is_Returned_Bool',
                         title="Return Rate (%) by Category", color_discrete_sequence=['#ef553b'])
        st.plotly_chart(apply_dark_style(fig_ret), width='stretch')
    with col7:
        ship_perf = filtered_df.groupby('Shipping_Method')[
            'Days_to_Ship'].mean().reset_index()
        fig_ship = px.bar(ship_perf, x='Shipping_Method',
                          y='Days_to_Ship', title="Average Days to Ship")
        st.plotly_chart(apply_dark_style(fig_ship), width='stretch')

    st.subheader("Shipping Performance Table")
    ship_analysis = filtered_df.groupby('Shipping_Method').agg(
        {'Shipping_Cost': 'sum', 'Net_Revenue': 'sum'}).reset_index()
    ship_analysis['Shipping_Perc'] = (
        ship_analysis['Shipping_Cost'] / ship_analysis['Net_Revenue']) * 100
    st.dataframe(ship_analysis.style.format(
        {'Shipping_Perc': '{:.2f}%', 'Shipping_Cost': '${:,.2f}', 'Net_Revenue': '${:,.2f}'}), width='stretch')

# --- FOOTER ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding: 10px;">
        <p style="margin-bottom: 2px; font-size: 13px;">Data analysis completed. Source: Book1.csv</p>
        <p style="color: #FAFAFA; font-weight: normal; font-size: 15px; margin-top: 0;">
            Analyzed with 🩶 by <span style="color: #00d4ff; font-weight: bold;">Jolayemi Boluwatife</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
