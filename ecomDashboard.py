import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Custom color palette and theme for consistent visualization
plotly_template = {
    'layout': {
        'plot_bgcolor': '#2c2f33',
        'paper_bgcolor': '#2c2f33',
        'font': {'color': '#ffffff'},
        'title': {'font': {'color': '#ffffff', 'size': 24}},
        'xaxis': {
            'gridcolor': '#40444b',
            'linecolor': '#40444b',
            'tickfont': {'color': '#ffffff'}
        },
        'yaxis': {
            'gridcolor': '#40444b',
            'linecolor': '#40444b',
            'tickfont': {'color': '#ffffff'}
        }
    }
}

# Custom color palette
custom_colors = ['#7289da', '#43b581', '#faa61a', '#f04747', '#b9bbbe',
                '#00b0f4', '#8ea1e1', '#eb459e', '#2ecc71', '#e91e63']

# Get current time for greeting
current_time = datetime.now()
hour = current_time.hour

# Determine greeting based on time of day
if 4 <= hour < 12:
    greeting = "Good morning!"
elif 12 <= hour < 18:
    greeting = "Good afternoon!"
else:
    greeting = "Good evening!"

# Get today's date
today_date = current_time.strftime("%B %d, %Y")

# Page configuration
st.set_page_config(
    page_title="Platform Sales Dashboard - All Channels",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page title and welcome section
st.title("Platform Sales Dashboard - All Channels")

# Welcome section with dynamic greeting and date
st.markdown(f"""
    ### {greeting}
    #### Today is {today_date}
    
    Welcome to our comprehensive sales analytics dashboard. This tool provides detailed insights 
    into our e-commerce performance across all sales channels. The data presented here is sourced 
    from our platform's sales reports and is updated regularly to ensure accurate decision-making 
    and performance tracking.
""")

# Add a visual separator
st.markdown("---")

# Function to load and clean data
@st.cache_data
def load_data():
    try:
        # Read CSV with low_memory=False to handle mixed types
        df = pd.read_csv("data/Amazon Sale Report.csv", low_memory=False)
        
        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # First, ensure the Date column contains string values
        df['Date'] = df['Date'].astype(str)
        
        # Convert Date with explicit format (adjust format string if needed)
        df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%y', errors='coerce')
        
        # Drop any rows where Date conversion failed
        df = df.dropna(subset=['Date'])
        
        # Convert numeric columns
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')
        
        # Fill missing values using proper pandas methods
        df = df.assign(**{
            'ship-postal-code': df['ship-postal-code'].astype(str).replace('nan', 'Unknown'),
            'promotion-ids': df['promotion-ids'].fillna('No Promotion')
        })
        
        return df
    
    except Exception as e:
        st.error(f"Error in data loading: {str(e)}")
        raise e

# Load the data
try:
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header('Filters')
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [df['Date'].min(), df['Date'].max()]
    )
    
    # Category filter
    categories = ['All'] + list(df['Category'].unique())
    selected_category = st.sidebar.selectbox('Select Category', categories)
    
    # Region filter
    regions = ['All'] + list(df['ship-state'].unique())
    selected_region = st.sidebar.selectbox('Select Region', regions)
    
    # Apply filters
    mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
    filtered_df = df[mask]
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['ship-state'] == selected_region]
    
    # 1. Sales Performance Metrics
    st.header('Sales Performance')
    st.markdown("*Key metrics showing overall sales performance, orders, and product category analysis*")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = filtered_df['Amount'].sum()
        st.metric("Total Sales", f"${total_sales:,.2f}")
    
    with col2:
        total_orders = filtered_df['Order ID'].nunique()
        st.metric("Number of Orders", f"{total_orders:,}")
    
    with col3:
        aov = total_sales / total_orders if total_orders > 0 else 0
        st.metric("Average Order Value", f"${aov:,.2f}")
    
    with col4:
        total_units = filtered_df['Qty'].sum()
        st.metric("Total Units Sold", f"{total_units:,}")
    
    # Revenue by Category
    st.subheader('Revenue by Product Category')
    category_sales = filtered_df.groupby('Category')['Amount'].sum().reset_index()
    fig_category = px.bar(
        category_sales,
        x='Category',
        y='Amount',
        title='Sales by Category',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_category, use_container_width=True)

    # 2. Fulfillment Metrics
    st.header('Fulfillment Metrics')
    st.markdown("*Analysis of order status, fulfillment methods, and shipping service preferences*")
    col1, col2 = st.columns(2)
    
    with col1:
        # Order Status Breakdown
        status_dist = filtered_df['Status'].value_counts()
        fig_status = px.pie(
            values=status_dist.values,
            names=status_dist.index,
            title='Order Status Distribution',
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        st.plotly_chart(fig_status)
    
    with col2:
        # Fulfillment Method Distribution
        fulfillment_dist = filtered_df['fulfilled-by'].value_counts()
        fig_fulfillment = px.pie(
            values=fulfillment_dist.values,
            names=fulfillment_dist.index,
            title='Fulfillment Method Distribution',
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        st.plotly_chart(fig_fulfillment)

    # Shipping Service Level
    shipping_dist = filtered_df['ship-service-level'].value_counts()
    fig_shipping = px.bar(
        x=shipping_dist.index,
        y=shipping_dist.values,
        title='Shipping Service Level Usage',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_shipping, use_container_width=True)

    # 3. Geographic Metrics
    st.header('Geographic Metrics')
    st.markdown("*Distribution of sales and orders across different states and cities*")
    
    # Sales by State
    state_sales = filtered_df.groupby('ship-state')['Amount'].sum().reset_index()
    state_sales = state_sales.sort_values('Amount', ascending=False)
    
    fig_state = px.bar(
        state_sales.head(10),
        x='ship-state',
        y='Amount',
        title='Top 10 States by Sales',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_state, use_container_width=True)

    # Top Cities
    city_orders = filtered_df.groupby('ship-city').size().reset_index(name='count')
    city_orders = city_orders.sort_values('count', ascending=False)
    
    fig_city = px.bar(
        city_orders.head(10),
        x='ship-city',
        y='count',
        title='Top 10 Cities by Number of Orders',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_city, use_container_width=True)

    # 4. Customer Insights
    st.header('Customer Insights')
    st.markdown("*Understanding customer segments and ordering patterns through B2B/B2C split and order sizes*")
    col1, col2 = st.columns(2)
    
    with col1:
        # B2B vs B2C Split
        b2b_split = filtered_df['B2B'].value_counts()
        fig_b2b = px.pie(
            values=b2b_split.values,
            names=b2b_split.index,
            title='B2B vs B2C Orders',
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        st.plotly_chart(fig_b2b)
    
    with col2:
        # Order Size Distribution
        fig_order_size = px.histogram(
            filtered_df,
            x='Qty',
            title='Order Size Distribution',
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        st.plotly_chart(fig_order_size)

    # 5. Operational Efficiency
    st.header('Operational Efficiency')
    st.markdown("*Key performance indicators for business operations including cancellations and promotions*")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cancelled = filtered_df[filtered_df['Status'] == 'Cancelled']['Order ID'].nunique()
        cancellation_rate = (cancelled / total_orders) * 100
        st.metric("Cancellation Rate", f"{cancellation_rate:.2f}%")
    
    with col2:
        promotion_usage = filtered_df[filtered_df['promotion-ids'] != 'No Promotion']['Order ID'].nunique()
        promotion_rate = (promotion_usage / total_orders) * 100
        st.metric("Promotion Usage Rate", f"{promotion_rate:.2f}%")
    
    with col3:
        avg_qty_per_order = filtered_df['Qty'].mean()
        st.metric("Avg Units Per Order", f"{avg_qty_per_order:.2f}")

    # 6. Trends Over Time
    st.header('Trends Over Time')
    st.markdown("*Historical analysis of daily sales and order volume patterns*")
    
    # Daily sales trend
    daily_sales = filtered_df.groupby('Date')['Amount'].sum().reset_index()
    fig_trend = px.line(
        daily_sales,
        x='Date',
        y='Amount',
        title='Daily Sales Trend',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Order volume trend
    daily_orders = filtered_df.groupby('Date')['Order ID'].nunique().reset_index()
    fig_orders = px.line(
        daily_orders,
        x='Date',
        y='Order ID',
        title='Daily Order Volume',
        template=plotly_template,
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig_orders, use_container_width=True)

    # Month-over-Month Growth Analysis
    # Create monthly sales dataframe
    monthly_sales = filtered_df.groupby(filtered_df['Date'].dt.to_period('M'))['Amount'].sum()
    monthly_sales_df = pd.DataFrame(monthly_sales).reset_index()
    monthly_sales_df['Date'] = monthly_sales_df['Date'].astype(str)
    
    # Calculate MoM growth rate
    monthly_sales_df['MoM Growth Rate'] = monthly_sales_df['Amount'].pct_change() * 100
    
    # Create a figure with dual y-axes
    fig_mom = go.Figure()
    
    # Add monthly sales bars
    fig_mom.add_trace(
        go.Bar(
            x=monthly_sales_df['Date'],
            y=monthly_sales_df['Amount'],
            name='Monthly Sales',
            yaxis='y'
        )
    )
    
    # Add MoM growth rate line
    fig_mom.add_trace(
        go.Scatter(
            x=monthly_sales_df['Date'],
            y=monthly_sales_df['MoM Growth Rate'],
            name='MoM Growth Rate (%)',
            yaxis='y2',
            line=dict(color='red')
        )
    )
    
    # Update layout for dual axes
    fig_mom.update_layout(
        title='Monthly Sales and Growth Rate',
        yaxis=dict(title='Sales Amount ($)', side='left'),
        yaxis2=dict(
            title='MoM Growth Rate (%)',
            side='right',
            overlaying='y',
            tickformat='.1f'
        ),
        showlegend=True,
        template=plotly_template,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font={'color': '#2c3e50'}
    )
    
    st.plotly_chart(fig_mom, use_container_width=True)

    # Display monthly performance metrics
    st.subheader("Monthly Performance Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        avg_growth = monthly_sales_df['MoM Growth Rate'].mean()
        st.metric(
            "Average Monthly Growth Rate",
            f"{avg_growth:.1f}%",
            delta=f"{monthly_sales_df['MoM Growth Rate'].iloc[-1]:.1f}% (Last Month)"
        )
    
    with col2:
        highest_month = monthly_sales_df.loc[monthly_sales_df['Amount'].idxmax()]
        st.metric(
            "Best Performing Month",
            f"${highest_month['Amount']:,.2f}",
            delta=highest_month['Date']
        )

    # 7. Sales Velocity Analysis
    st.header('Sales Velocity Analysis')
    st.markdown("*Analysis of sales speed and product movement patterns across categories*")

    # Calculate daily sales velocity metrics
    velocity_df = filtered_df.copy()
    
    # Group by date and category to get daily sales per category
    daily_category_sales = velocity_df.groupby(['Date', 'Category']).agg({
        'Qty': 'sum',
        'Amount': 'sum',
        'Order ID': 'nunique'
    }).reset_index()

    # Calculate rolling 7-day average for smoother trends
    category_velocity = daily_category_sales.groupby('Category').agg({
        'Qty': lambda x: x.rolling(7, min_periods=1).mean().mean(),  # Average daily units sold
        'Amount': lambda x: x.rolling(7, min_periods=1).mean().mean(),  # Average daily revenue
        'Order ID': lambda x: x.rolling(7, min_periods=1).mean().mean()  # Average daily orders
    }).reset_index()

    # Calculate velocity score (normalized composite score)
    category_velocity['Velocity Score'] = (
        (category_velocity['Qty'] / category_velocity['Qty'].max()) * 0.4 +
        (category_velocity['Amount'] / category_velocity['Amount'].max()) * 0.4 +
        (category_velocity['Order ID'] / category_velocity['Order ID'].max()) * 0.2
    ) * 100

    # Sort by velocity score
    category_velocity = category_velocity.sort_values('Velocity Score', ascending=False)

    # Display velocity metrics
    col1, col2 = st.columns(2)

    with col1:
        # Velocity score by category
        fig_velocity = px.bar(
            category_velocity,
            x='Category',
            y='Velocity Score',
            title='Product Category Velocity Scores',
            labels={'Velocity Score': 'Velocity Score (0-100)'},
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        fig_velocity.update_traces(marker_color='lightseagreen')
        st.plotly_chart(fig_velocity, use_container_width=True)

    with col2:
        # Daily units movement by category
        fig_units = px.bar(
            category_velocity,
            x='Category',
            y='Qty',
            title='Average Daily Units Sold by Category',
            labels={'Qty': 'Units per Day'},
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        fig_units.update_traces(marker_color='coral')
        st.plotly_chart(fig_units, use_container_width=True)

    # Display top performing categories
    st.subheader("Category Performance Insights")
    col1, col2, col3 = st.columns(3)

    with col1:
        top_velocity = category_velocity.iloc[0]
        st.metric(
            "Fastest Moving Category",
            top_velocity['Category'],
            f"Score: {top_velocity['Velocity Score']:.1f}"
        )

    with col2:
        top_units = category_velocity.loc[category_velocity['Qty'].idxmax()]
        st.metric(
            "Highest Volume Category",
            top_units['Category'],
            f"{top_units['Qty']:.1f} units/day"
        )

    with col3:
        top_revenue = category_velocity.loc[category_velocity['Amount'].idxmax()]
        st.metric(
            "Highest Revenue Category",
            top_revenue['Category'],
            f"${top_revenue['Amount']:.2f}/day"
        )

    # Add detailed velocity table with sorting
    st.subheader("Detailed Velocity Metrics")
    st.markdown("*Click on columns to sort by different metrics*")
    
    # Format the detailed metrics table
    detailed_velocity = category_velocity.copy()
    detailed_velocity['Qty'] = detailed_velocity['Qty'].round(1)
    detailed_velocity['Amount'] = detailed_velocity['Amount'].round(2)
    detailed_velocity['Order ID'] = detailed_velocity['Order ID'].round(1)
    detailed_velocity['Velocity Score'] = detailed_velocity['Velocity Score'].round(1)
    
    # Rename columns for better readability
    detailed_velocity.columns = ['Category', 'Avg Daily Units', 'Avg Daily Revenue', 
                               'Avg Daily Orders', 'Velocity Score']
    
    st.dataframe(
        detailed_velocity,
        hide_index=True,
        use_container_width=True
    )

    # 8. Promotion Analysis
    st.header('Promotion Analysis')
    st.markdown("*Analysis of promotional campaign effectiveness and impact on sales*")

    # Create promotion analysis dataframe
    promo_df = filtered_df.copy()
    
    # Group by promotion ID
    promo_analysis = promo_df.groupby('promotion-ids').agg({
        'Order ID': 'nunique',  # Number of orders
        'Amount': 'sum',        # Total revenue
        'Qty': 'sum'           # Total units sold
    }).reset_index()
    
    # Calculate average order value for each promotion
    promo_analysis['Avg Order Value'] = promo_analysis['Amount'] / promo_analysis['Order ID']
    
    # Calculate average units per order
    promo_analysis['Avg Units per Order'] = promo_analysis['Qty'] / promo_analysis['Order ID']
    
    # Sort by revenue
    promo_analysis = promo_analysis.sort_values('Amount', ascending=False)

    # Display promotion metrics
    col1, col2 = st.columns(2)

    with col1:
        # Top promotions by revenue
        fig_promo_rev = px.bar(
            promo_analysis.head(10),
            x='promotion-ids',
            y='Amount',
            title='Top 10 Promotions by Revenue',
            labels={'promotion-ids': 'Promotion ID', 'Amount': 'Revenue ($)'},
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        fig_promo_rev.update_traces(marker_color='teal')
        st.plotly_chart(fig_promo_rev, use_container_width=True)

    with col2:
        # Average order value by promotion
        fig_promo_aov = px.bar(
            promo_analysis.head(10),
            x='promotion-ids',
            y='Avg Order Value',
            title='Average Order Value by Promotion',
            labels={'promotion-ids': 'Promotion ID', 'Avg Order Value': 'AOV ($)'},
            template=plotly_template,
            color_discrete_sequence=custom_colors
        )
        fig_promo_aov.update_traces(marker_color='coral')
        st.plotly_chart(fig_promo_aov, use_container_width=True)

    # Promotion performance metrics
    st.subheader("Promotion Performance Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        top_promo = promo_analysis.iloc[0]
        st.metric(
            "Best Performing Promotion",
            top_promo['promotion-ids'],
            f"${top_promo['Amount']:,.2f} Revenue"
        )

    with col2:
        highest_aov = promo_analysis.loc[promo_analysis['Avg Order Value'].idxmax()]
        st.metric(
            "Highest AOV Promotion",
            highest_aov['promotion-ids'],
            f"${highest_aov['Avg Order Value']:,.2f}"
        )

    with col3:
        highest_units = promo_analysis.loc[promo_analysis['Avg Units per Order'].idxmax()]
        st.metric(
            "Highest Units/Order Promotion",
            highest_units['promotion-ids'],
            f"{highest_units['Avg Units per Order']:.1f} Units"
        )

    # Detailed promotion metrics table
    st.subheader("Detailed Promotion Metrics")
    st.markdown("*Click on columns to sort by different metrics*")
    
    # Format the detailed metrics table
    detailed_promos = promo_analysis.copy()
    detailed_promos['Amount'] = detailed_promos['Amount'].round(2)
    detailed_promos['Avg Order Value'] = detailed_promos['Avg Order Value'].round(2)
    detailed_promos['Avg Units per Order'] = detailed_promos['Avg Units per Order'].round(1)
    
    # Rename columns for better readability
    detailed_promos.columns = ['Promotion ID', 'Number of Orders', 'Total Revenue', 
                             'Total Units', 'Avg Order Value', 'Avg Units per Order']
    
    st.dataframe(
        detailed_promos,
        hide_index=True,
        use_container_width=True
    )

    # Add custom CSS for consistent styling
    st.markdown("""
        <style>
        /* Main content and background styling */
        .main {
            background-color: #36393f;
            color: #ffffff;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #2f3136;
        }
        
        /* Metric containers */
        div[data-testid="stMetric"] {
            background-color: #2c2f33;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #40444b;
        }
        
        /* Metric labels */
        div[data-testid="stMetricLabel"] {
            font-size: 1rem;
            color: #dcddde;
        }
        
        /* Metric values */
        div[data-testid="stMetricValue"] {
            color: #7289da;
        }
        
        /* Section headers */
        h1, h2, h3 {
            color: #ffffff;
            font-weight: 600;
            padding-top: 1rem;
        }
        
        /* Chart containers */
        div[data-testid="stPlotlyChart"] > div {
            background-color: #2c2f33;
            border-radius: 0.5rem;
            border: 1px solid #40444b;
            padding: 1rem;
        }
        
        /* DataFrame styling */
        .dataframe {
            background-color: #2c2f33;
            color: #ffffff;
        }
        
        /* Text and markdown */
        .markdown-text-container {
            color: #dcddde;
            font-size: 0.9rem;
            font-style: italic;
        }
        
        /* Streamlit base elements */
        .stTextInput > div > div > input {
            background-color: #40444b;
            color: #ffffff;
        }
        
        .stSelectBox > div > div > select {
            background-color: #40444b;
            color: #ffffff;
        }
        
        /* Links */
        a {
            color: #00b0f4;
        }
        
        /* Sidebar text */
        .css-pkbazv {
            color: #ffffff;
        }
        
        /* Make sure text inputs and selectors are visible */
        .stDateInput, .stSelectbox {
            background-color: #40444b;
            color: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
