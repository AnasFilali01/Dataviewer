import streamlit as st
import pandas as pd
from io import BytesIO

# Streamlit title and description
st.title("Enhanced Data Viewer")
st.write("Upload your Excel file and scroll through the data below.")

# File uploader to upload Excel file
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

# Initialize session state for row index, filter text, and global row index
if 'row_index' not in st.session_state:
    st.session_state.row_index = 0
if 'filter_text' not in st.session_state:
    st.session_state.filter_text = ""
if 'global_row_index' not in st.session_state:
    st.session_state.global_row_index = 0

# Define valid price level categories, evaluation options, and comment options
valid_price_levels = ['$', '$-$$', '$$', '$$-$$$', '$$$', '$$$-$$$$', '$$$$', 'Default']
evaluation_options = ['Initial Value', 'High-end', 'Mid-end', 'Low-end']
comment_options = [
    "Key Account", "No Website", "Bad Website", "Good Quality", "High Prices",
    "Low Engagement", "Strong Presence", "Innovative Concept", "Outdated Design",
    "Industrial", "Limited Reach", "Premium Packaging"
]

# Function to prepend "+" to a phone number starting with "9"
def prepend_plus_to_phone(phone):
    if pd.isna(phone):
        return phone
    phone = str(phone)
    if phone.startswith("9"):
        phone = "+" + phone
    return phone

# Function to download the DataFrame as an Excel file
def download_dataframe_as_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

# Required columns
required_columns = ['company', 'Activity', 'Adress', 'city', 'phone', 'priceLevel', 'webUrl', 'Valrhona Yes/No']

# Check if a file has been uploaded
if uploaded_file:
    # Read the Excel file into a DataFrame
    if 'df' not in st.session_state:
        df = pd.read_excel(uploaded_file)
        # Fill NaN values with a default message or handle nulls appropriately
        df.fillna("N/A", inplace=True)
        # Add an incremental ID column
        df.insert(0, 'ID', range(1, len(df) + 1))

        # Add missing required columns with default values
        for col in required_columns:
            if col not in df.columns:
                df[col] = "N/A"

        # Add "Status" column if it doesn't exist, with the default value "Not Verified"
        if 'Status' not in df.columns:
            df['Status'] = "Not Verified"

        # Add 'Evaluating' column if not present
        if 'Evaluating' not in df.columns:
            df['Evaluating'] = "Initial Value"

        # Add 'Comment' column if not present
        if 'Comment' not in df.columns:
            df['Comment'] = "No comment"

        st.session_state.df = df  # Store the DataFrame in session state
    else:
        df = st.session_state.df

    # Sidebar filters and statistics
    st.sidebar.title("Filters and Statistics")

    # Add data statistics
    st.sidebar.subheader("Overall Data Statistics")
    total_companies = len(df)
    unique_activities = df['Activity'].nunique()
    unique_cities = df['city'].nunique()
    price_level_distribution = df['priceLevel'].value_counts()

    st.sidebar.write(f"Total Companies: {total_companies}")
    st.sidebar.write(f"Unique Activities: {unique_activities}")
    st.sidebar.write(f"Unique Cities: {unique_cities}")
    st.sidebar.write("Price Level Distribution:")
    for price_level, count in price_level_distribution.items():
        st.sidebar.write(f"  {price_level}: {count}")

    # Filter for Activity
    activity_options = ['All'] + list(df['Activity'].unique())
    selected_activity = st.sidebar.selectbox("Filter by Activity", activity_options)

    # Filter for Price Level
    price_options = ['All'] + valid_price_levels
    selected_price = st.sidebar.selectbox("Filter by Price Level", price_options)

    # Filter for City
    city_options = ['All'] + list(df['city'].unique())
    selected_city = st.sidebar.selectbox("Filter by City", city_options)

    # Filter for "Valrhona Yes/No"
    valrhona_options = ['All'] + list(df['Valrhona Yes/No'].unique())
    selected_valrhona = st.sidebar.selectbox("Filter by Valrhona Yes/No", valrhona_options)

    # Filter by Company or Activity (Text Input)
    st.session_state.filter_text = st.sidebar.text_input("Search by Company or Activity", st.session_state.filter_text)

    # Apply filters based on sidebar selections
    filtered_df = df.copy()  # Create a filtered DataFrame
    if st.session_state.filter_text:
        filtered_df = filtered_df[filtered_df['company'].str.contains(st.session_state.filter_text, case=False) |
                                  filtered_df['Activity'].str.contains(st.session_state.filter_text, case=False)]

    if selected_activity != 'All':
        filtered_df = filtered_df[filtered_df['Activity'] == selected_activity]

    if selected_price != 'All':
        filtered_df = filtered_df[filtered_df['priceLevel'] == selected_price]

    if selected_city != 'All':
        filtered_df = filtered_df[filtered_df['city'] == selected_city]

    if selected_valrhona != 'All':
        filtered_df = filtered_df[filtered_df['Valrhona Yes/No'] == selected_valrhona]

    # Display filtered data statistics
    st.sidebar.subheader("Filtered Data Statistics")
    st.sidebar.write(f"Filtered Companies: {len(filtered_df)}")
    st.sidebar.write(f"Unique Activities (Filtered): {filtered_df['Activity'].nunique()}")
    st.sidebar.write(f"Unique Cities (Filtered): {filtered_df['city'].nunique()}")

    if not filtered_df.empty:
        # Ensure row index is within the bounds of the filtered DataFrame
        if st.session_state.row_index >= len(filtered_df):
            st.session_state.row_index = len(filtered_df) - 1
        elif st.session_state.row_index < 0:
            st.session_state.row_index = 0

        # Get the current row based on the filtered DataFrame
        row = filtered_df.iloc[st.session_state.row_index]
        original_idx = df.index[filtered_df.index[st.session_state.row_index]]

        # Read-only display (view-only section)
        with st.expander("View Data", expanded=True):
            st.text(f"ID: {row['ID']}")
            st.text(f"Company: {row['company']}")
            st.text(f"Activity: {row['Activity']}")
            st.text(f"Address: {row['Adress']}")
            st.text(f"Phone: {prepend_plus_to_phone(row['phone'])}")
            st.text(f"City: {row['city']}")
            st.text(f"Valrhona Yes/No: {row['Valrhona Yes/No']}")

            # Display the URL
            st.write("### URL")
            if row['webUrl'] == "N/A" or pd.isna(row['webUrl']):
                st.warning("This company does not have a valid URL.")
            else:
                st.markdown(f'<a href="{row["webUrl"]}" target="_blank">{row["webUrl"]}</a>', unsafe_allow_html=True)

        # Status Checkbox
        st.write("### Status")
        status_verified = st.checkbox("Verified", value=row['Status'] == "Verified")
        if status_verified:
            df.at[original_idx, 'Status'] = "Verified"
        else:
            df.at[original_idx, 'Status'] = "Not Verified"

        # Evaluation Dropdown
        st.write("### Evaluation")
        selected_evaluation = st.selectbox(
            "Evaluate this Company",
            evaluation_options,
            index=evaluation_options.index(row['Evaluating']) if row['Evaluating'] in evaluation_options else 0
        )
        df.at[original_idx, 'Evaluating'] = selected_evaluation

        # Comment Multi-Select and Text Area
        st.write("### Comments")
        # If 'No comment' or empty, initialize with an empty list
        default_comments = [] if row['Comment'] == "No comment" or row['Comment'] == "" else row['Comment'].split(", ")
        selected_comments = st.multiselect("Select Comments", comment_options, default=default_comments)
        df.at[original_idx, 'Comment'] = ', '.join(selected_comments)

        st.session_state.df = df  # Store the updated DataFrame back in session state

        # Add buttons for manual scrolling (Previous/Next based on ID)
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Previous"):
                # Use global index for smooth row navigation
                if st.session_state.global_row_index > 0:
                    st.session_state.global_row_index -= 1
                st.session_state.row_index = st.session_state.global_row_index

        with col2:
            if st.button("Next"):
                # Use global index for smooth row navigation
                if st.session_state.global_row_index < len(df) - 1:
                    st.session_state.global_row_index += 1
                st.session_state.row_index = st.session_state.global_row_index

        with col3:
            if st.button("Reset Filter"):
                st.session_state.filter_text = ""
                st.session_state.row_index = 0  # Reset to first row
                st.session_state.global_row_index = 0  # Reset global row index

        # Download button to download the modified DataFrame
        st.download_button(
            label="Download Data",
            data=download_dataframe_as_excel(st.session_state.df),
            file_name="data.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.warning("No results match your filter criteria.")
else:
    st.write("Please upload an Excel file to proceed.")
