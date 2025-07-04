import streamlit as st
import pandas as pd
import pymysql

# Function to connect to database and fetch unique routes
def get_unique_routes():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='12345',
            database='AP_BUS_DETAILS'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT route_name FROM AP_bus ORDER BY route_name")
        routes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return routes
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return []

# Function to fetch bus data based on filters
def get_bus_data(route_name, search_text, min_rating, status_filter):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='12345',
            database='AP_BUS_DETAILS'
        )
        cursor = conn.cursor()
        query = """
            SELECT route_name, bus_name, bus_type, duration, price, rating, no_of_ratings, review_status
            FROM AP_bus
            WHERE route_name = %s
        """
        params = [route_name]
        
        if search_text:
            query += " AND bus_name LIKE %s"
            params.append('%' + search_text + '%')
        
        if min_rating is not None:
            query += " AND rating >= %s"
            params.append(min_rating)
        
        if status_filter != 'All':
            query += " AND review_status = %s"
            params.append(status_filter)
        
        query += " ORDER BY rating DESC, price ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[
            'Route Name', 'Bus Name', 'Bus Type', 'Duration', 'Price',
            'Rating', 'No. of Ratings', 'Review Status'
        ])
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching bus data: {str(e)}")
        return pd.DataFrame()

# Streamlit App Config
st.set_page_config(
    page_title="APSRTC Bus Reviews", 
    page_icon="🚌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .route-selection {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin: 2rem 0;
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div class="main-header">
    <h1>🚌 APSRTC Bus Reviews Dashboard</h1>
    <p>Discover the Best Government Bus Routes in Andhra Pradesh</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for route selection
if 'selected_route' not in st.session_state:
    st.session_state.selected_route = None

# Route Selection Section
st.markdown("## Please Select Your Route")

# Get available routes
routes = get_unique_routes()

if routes:
    # Route selection in main area (more prominent)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="route-selection">', unsafe_allow_html=True)
        st.markdown("### Choose your desired bus route")
        
        selected_route = st.selectbox(
            "Available Routes",
            options=["Select a route..."] + routes,
            key="route_selector"
        )
        
        if selected_route != "Select a route...":
            st.session_state.selected_route = selected_route
            st.success(f" Route selected: **{selected_route}**")
        else:
            st.session_state.selected_route = None
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Show features and data only after route selection
    if st.session_state.selected_route:
        st.markdown("---")
        st.markdown("## Customize Your Search")
        
        # Sidebar Filters (now visible only after route selection)
        st.sidebar.header("🔎 Search Filters")
        st.sidebar.markdown(f"**Selected Route:** {st.session_state.selected_route}")
        st.sidebar.markdown("---")
        
        # Filter options
        search_text = st.sidebar.text_input("🔍 Search Bus Name", placeholder="Enter bus name...")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            min_rating = st.sidebar.slider("⭐ Min Rating", 0.0, 5.0, 0.0, step=0.1)
        
        status_filter = st.sidebar.selectbox(
            "📊 Review Status",
            ['All', 'Excellent Service', 'Good Service', 'Average', 'Below Average']
        )
        
        # Add filter summary
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📋 Active Filters")
        if search_text:
            st.sidebar.markdown(f"🔍 Bus Name: *{search_text}*")
        if min_rating > 0:
            st.sidebar.markdown(f"⭐ Rating: *≥ {min_rating}*")
        if status_filter != 'All':
            st.sidebar.markdown(f"📊 Status: *{status_filter}*")
        
        # Clear filters button
        if st.sidebar.button("🗑️ Clear All Filters"):
            st.rerun()
        
        # Fetch and display data
        st.markdown("## 📊 Step 3: View Results")
        
        with st.spinner("🔄 Loading bus data..."):
            df = get_bus_data(
                st.session_state.selected_route,
                search_text,
                min_rating if min_rating > 0 else None,
                status_filter
            )
        
        if not df.empty:
            # Key Metrics
            st.markdown("### Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("🚌 Total Buses", len(df))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                avg_rating = df['Rating'].mean()
                st.metric("⭐ Avg Rating", f"{avg_rating:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                price_range = f"{df['Price'].min()} - {df['Price'].max()}" if len(df['Price'].unique()) > 1 else df['Price'].iloc[0]
                st.metric(" Price Range", price_range)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                top_rated = df.loc[df['Rating'].idxmax(), 'Bus Name'] if not df.empty else "N/A"
                st.metric("🏆 Top Rated", top_rated[:20] + "..." if len(str(top_rated)) > 20 else top_rated)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Data Display Options
            st.markdown("### 📋 Bus Details")
            
            # Display options
            col1, col2 = st.columns([3, 1])
            with col2:
                view_option = st.radio("View as:", ["Table", "Cards"])
            
            if view_option == "Table":
                # Enhanced table display
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rating": st.column_config.NumberColumn(
                            "Rating ",
                            format="%.2f"
                        ),
                        "Price": st.column_config.TextColumn(
                            "Price "
                        ),
                        "Review Status": st.column_config.TextColumn(
                            "Status "
                        )
                    }
                )
            else:
                # Card view
                for idx, row in df.iterrows():
                    with st.expander(f"🚌 {row['Bus Name']} - ⭐ {row['Rating']} - {row['Price']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Bus Type:** {row['Bus Type']}")
                            st.write(f"**Duration:** {row['Duration']}")
                            st.write(f"**Rating:** {row['Rating']} ⭐ ({row['No. of Ratings']} reviews)")
                        with col2:
                            st.write(f"**Price:** {row['Price']}")
                            st.write(f"**Status:** {row['Review Status']}")
                            st.write(f"**Route:** {row['Route Name']}")
            
            # Download option
            st.markdown("---")
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"apsrtc_buses_{st.session_state.selected_route.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("No buses found matching your criteria. Try adjusting your filters.")
            
            # Suggestions
            st.markdown("### 💡 Suggestions:")
            st.markdown("- Try reducing the minimum rating requirement")
            st.markdown("- Clear the bus name search filter") 
            st.markdown("- Select 'All' for review status")
    
    else:
        # Welcome message when no route is selected
        st.markdown("---")
        st.info("👆 Please select a route above to explore available buses and their details.")
        
        # Show some stats about available routes
        st.markdown("### 📊 Available Routes")
        st.markdown(f"**Total Routes Available:** {len(routes)}")
        
        # Show sample routes
        if len(routes) > 0:
            st.markdown("**Sample Routes:**")
            sample_routes = routes[:5] if len(routes) >= 5 else routes
            for route in sample_routes:
                st.markdown(f"• {route}")
            if len(routes) > 5:
                st.markdown(f"... and {len(routes) - 5} more routes")

else:
    st.error(" Unable to connect to the database. Please check your connection settings.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Developed with ❤️ by <strong>Yuvraj Dawande</strong></p>
</div>
""", unsafe_allow_html=True)