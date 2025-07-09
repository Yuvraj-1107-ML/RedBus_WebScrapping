import streamlit as st
import pandas as pd
import psycopg2

# Function to connect to Postgres database and fetch unique routes
def get_unique_routes():
    try:
        conn = psycopg2.connect(
            host='dpg-d1n3hkfdiees73emhn6g-a.oregon-postgres.render.com',
            database='db_apbus',
            user='db_apbus_user',
            password='ypJsjZYMOMqsy5wd2nX0Tm4WqWRuZj3t',
            port=5432
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
        conn = psycopg2.connect(
            host='dpg-d1n3hkfdiees73emhn6g-a.oregon-postgres.render.com',
            database='db_apbus',
            user='db_apbus_user',
            password='ypJsjZYMOMqsy5wd2nX0Tm4WqWRuZj3t',
            port=5432
        )
        cursor = conn.cursor()
        query = """
            SELECT route_name, bus_name, bus_type, duration, price, rating, no_of_ratings, review_status
            FROM AP_bus
            WHERE route_name = %s
        """
        params = [route_name]
        
        if search_text:
            query += " AND bus_name ILIKE %s"
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

# --------------------------- Streamlit App ---------------------------

st.set_page_config(
    page_title="APSRTC Bus Reviews", 
    page_icon="🚌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Header
st.markdown("""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; border-radius: 10px; margin-bottom: 2rem;">
    <h1>🚌 APSRTC Bus Reviews Dashboard</h1>
    <p>Discover the Best Government Bus Routes in Andhra Pradesh</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_route' not in st.session_state:
    st.session_state.selected_route = None

# Route Selection
st.markdown("## Please Select Your Route")
routes = get_unique_routes()

if routes:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; text-align: center; margin: 2rem 0;">', unsafe_allow_html=True)
        st.markdown("### Choose your desired bus route")
        
        selected_route = st.selectbox(
            "Available Routes",
            options=["Select a route..."] + routes,
            key="route_selector"
        )
        
        if selected_route != "Select a route...":
            st.session_state.selected_route = selected_route
            st.success(f"Route selected: **{selected_route}**")
        else:
            st.session_state.selected_route = None
        
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.selected_route:
        st.markdown("---")
        st.markdown("## Customize Your Search")
        
        st.sidebar.header("🔎 Search Filters")
        st.sidebar.markdown(f"**Selected Route:** {st.session_state.selected_route}")
        st.sidebar.markdown("---")
        
        search_text = st.sidebar.text_input("🔍 Search Bus Name", placeholder="Enter bus name...")
        min_rating = st.sidebar.slider("⭐ Min Rating", 0.0, 5.0, 0.0, step=0.1)
        status_filter = st.sidebar.selectbox(
            "📊 Review Status",
            ['All', 'Excellent Service', 'Good Service', 'Average', 'Below Average']
        )
        
        if st.sidebar.button("🗑️ Clear All Filters"):
            st.rerun()
        
        st.markdown("## View Results")
        with st.spinner("🔄 Loading bus data..."):
            df = get_bus_data(
                st.session_state.selected_route,
                search_text,
                min_rating if min_rating > 0 else None,
                status_filter
            )
        
        if not df.empty:
            st.markdown("### Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🚌 Total Buses", len(df))
            with col2:
                st.metric("⭐ Avg Rating", f"{df['Rating'].mean():.2f}")
            with col3:
                price_range = f"{df['Price'].min()} - {df['Price'].max()}" if len(df['Price'].unique()) > 1 else df['Price'].iloc[0]
                st.metric("💰 Price Range", price_range)
            with col4:
                top_rated = df.loc[df['Rating'].idxmax(), 'Bus Name'] if not df.empty else "N/A"
                st.metric("🏆 Top Rated", top_rated)
            
            st.markdown("### 📋 Bus Details")
            view_option = st.radio("View as:", ["Table", "Cards"])
            
            if view_option == "Table":
                st.dataframe(df, use_container_width=True)
            else:
                for idx, row in df.iterrows():
                    with st.expander(f"🚌 {row['Bus Name']} - ⭐ {row['Rating']} - {row['Price']}"):
                        st.write(f"**Bus Type:** {row['Bus Type']}")
                        st.write(f"**Duration:** {row['Duration']}")
                        st.write(f"**Rating:** {row['Rating']} ⭐ ({row['No. of Ratings']} reviews)")
                        st.write(f"**Status:** {row['Review Status']}")
                        st.write(f"**Route:** {row['Route Name']}")
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"apsrtc_buses_{st.session_state.selected_route.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No buses found matching your criteria. Try adjusting your filters.")
else:
    st.error("Unable to connect to the database. Please check your connection settings.")

# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Developed with ❤️ by <strong>Yuvraj Dawande</strong></p>
</div>
""", unsafe_allow_html=True)
