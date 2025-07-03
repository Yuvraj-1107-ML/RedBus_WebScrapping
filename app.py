import streamlit as st
import pandas as pd
import pymysql

# Function to connect to database and fetch data
def get_bus_data(search_text, min_rating, status_filter):
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='12345',
        database='Bus_Details'
    )
    cursor = conn.cursor()

    # Query with filters
    query = """
        SELECT bus_name, operator_name, duration, price, rating, no_of_ratings, review_status
        FROM AP
        WHERE bus_name LIKE %s
    """

    params = ['%' + search_text + '%']

    if min_rating is not None:
        query += " AND rating >= %s"
        params.append(min_rating)

    if status_filter != 'All':
        query += " AND review_status = %s"
        params.append(status_filter)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=['Bus Name', 'Operator Name', 'Duration', 'Price', 'Rating', 'No. of Ratings', 'Review Status'])

    cursor.close()
    conn.close()

    return df

# Streamlit App Layout
st.set_page_config(page_title="APSRTC Bus Reviews", page_icon="🚌", layout="wide")

# App Title
st.title("🚌 APSRTC Bus Reviews Dashboard")
st.subheader("Hyderabad ➔ Vijayawada | Government Buses")

st.markdown("---")

# Sidebar Filters
st.sidebar.header("Search & Filters")
search_text = st.sidebar.text_input("🔍 Bus Name Contains:", "")

# Rating filter
min_rating = st.sidebar.slider("⭐ Minimum Rating:", 0.0, 5.0, 0.0, step=0.1)

# Review status filter
status_filter = st.sidebar.selectbox("📊 Review Status:", ['All','Excellent Service', 'Good Service', 'Average', 'Below Average'])

# Fetch data with filters
df = get_bus_data(search_text, min_rating if min_rating > 0 else None, status_filter)

# Display metrics
st.markdown("### Key Metrics")
col1, col2, col3 = st.columns(3)

col1.metric("Total Buses Found", len(df))
col2.metric("Average Rating", f"{df['Rating'].mean():.2f}" if not df.empty else "N/A")
col3.metric("Filter Applied", status_filter)

st.markdown("---")

# Display DataFrame
if not df.empty:
    st.write("### 📝 Filtered Results")
    st.dataframe(df)  
else:
    st.warning("No matching buses found with current filters.")

# Footer
st.markdown("---")
st.caption("Developed by @Yuvraj Dawande")
