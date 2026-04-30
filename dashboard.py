import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Retail Performance Dashboard", layout="wide")

# --- CSS INJECTION: FORCING GRADIENT & UI SYNC ---
st.markdown("""
    <style>
    /* 1. Transparent Header for Toggle Button */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        border-bottom: none !important;
    }
    
    /* 2. FORCED Gradient Background */
    .stApp {
        background: linear-gradient(180deg, #021d52 0%, #050a14 45%, #000000 100%) !important;
        background-attachment: fixed !important;
    }

    /* 3. Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(38, 39, 48, 0.95) !important;
        backdrop-filter: blur(10px);
    }
    
    /* 4. Sidebar Text & Labels */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stWidgetLabel"] p {
        color: white !important;
    }

    /* 5. White Sidebar Collapse Arrow */
    [data-testid="stSidebarCollapseButton"] svg {
        fill: white !important;
        color: white !important;
    }

    /* 6. KPI Metric styling */
    [data-testid="stMetricValue"] { 
        color: #00d4ff !important; 
        font-weight: bold !important; 
    }
    
    /* 7. Clean up UI elements */
    [data-testid="stDecoration"] { display: none !important; }
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- STEP 1: DATA LOADING ---


@st.cache_data
def load_data():
    df = pd.read_csv('Book1.csv')
    df.columns = df.columns.str.strip()
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    df['Year'] = df['Order_Date'].dt.year
    df['Month_Name'] = df['Order_Date'].dt.month_name()

    numeric_cols = ['Net_Revenue', 'Gross_Profit',
                    'Discount_Amount', 'COGS', 'Shipping_Cost', 'Unit_Price']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Quantity'] = df['Quantity'].fillna(0).astype(int)
    df['Is_Returned_Bool'] = df['Is_Returned'].map({'Yes': 1, 'No': 0})
    return df


df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Dashboard Filters")
with st.sidebar.expander("🎯 Filter Options", expanded=True):
    years = sorted(df['Year'].unique())
    year_filter = st.sidebar.multiselect(
        "Select Year", options=years, default=years)

    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    available_months = [
        m for m in month_order if m in df['Month_Name'].unique()]
    month_filter = st.sidebar.multiselect(
        "Select Month", options=available_months, default=available_months)

    region_filter = st.sidebar.multiselect(
        "Select Region", options=df['Region'].unique(), default=df['Region'].unique())
    category_filter = st.sidebar.multiselect(
        "Select Category", options=df['Category'].unique(), default=df['Category'].unique())

# Apply Filters
filtered_df = df[
    (df['Year'].isin(year_filter)) &
    (df['Month_Name'].isin(month_filter)) &
    (df['Region'].isin(region_filter)) &
    (df['Category'].isin(category_filter))
].copy()

# --- MAIN CONTENT ---
st.title("📊 Retail Performance Insights")
st.markdown("---")

if filtered_df.empty:
    st.warning("No data available. Please adjust filters.")
else:
    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", f"${filtered_df['Net_Revenue'].sum():,.0f}")
    k2.metric("Gross Profit", f"${filtered_df['Gross_Profit'].sum():,.0f}")
    k3.metric("Total Orders", f"{len(filtered_df):,}")

    cust_orders = filtered_df.groupby('Customer_ID')['Order_ID'].count()
    rr = (cust_orders > 1).sum() / len(cust_orders) * \
        100 if len(cust_orders) > 0 else 0
    k4.metric("Repeat Customer %", f"{rr:.1f}%")

    st.markdown("---")

    def apply_dark_style(fig):
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#FAFAFA")
        )
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
        return fig

    # Charts Row
    col1, col2 = st.columns((3, 2))
    with col1:
        filtered_df['YearMonth'] = filtered_df['Order_Date'].dt.to_period(
            'M').astype(str)
        monthly_rev = filtered_df.groupby(
            'YearMonth')['Net_Revenue'].sum().reset_index()
        fig_trend = px.line(monthly_rev, x='YearMonth', y='Net_Revenue',
                            title="Monthly Revenue Trend", markers=True)
        st.plotly_chart(apply_dark_style(fig_trend), use_container_width=True)

    with col2:
        rev_cat = filtered_df.groupby('Category')['Net_Revenue'].sum(
        ).reset_index().sort_values('Net_Revenue')
        fig_cat = px.bar(rev_cat, x='Net_Revenue', y='Category', orientation='h', title="Revenue by Category",
                         color='Net_Revenue', color_continuous_scale='Viridis')
        st.plotly_chart(apply_dark_style(fig_cat), use_container_width=True)

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
