import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json


def get_price(url):
    """
    Fetch and extract the price from a URL.
    
    Args:
        url: The webpage URL
        
    Returns:
        float: The price (e.g., 2182.70)
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    json_ld = soup.find('script', type='application/ld+json')
    data = json.loads(json_ld.string)
    
    return float(data['offers']['price'])


def calculate_total():
    """
    Fetch prices from URLs and calculate the total value.
    
    Returns:
        tuple: (total_value, dataframe)
    """
    # Define the data
    data = {
        'Name': [
            "1oz Gold Kangaroo",
            "100g Gold Bar",
            "20g Gold Bar",
            "10 Gulden Gold Coin",
            "1kg Silver Kookaburra Coin",
            "1oz Silver Kangaroo",
            "1oz Palladium Bar"
        ],
        'URL': [
            "https://ankauf.goldvorsorge.at/1-oz-gold-australian-kanguru-nugget.html",
            "https://ankauf.goldvorsorge.at/100g-goldbarren-argor-heraeus.html",
            "https://ankauf.goldvorsorge.at/20g-goldbarren-argor-heraeus.html",
            "https://ankauf.goldvorsorge.at/10-gulden-gold-wilhelmina.html",
            "https://ankauf.goldvorsorge.at/1kg-silbermunze-kookaburra.html",
            "https://ankauf.goldvorsorge.at/1-oz-silber-kanguru.html",
            "https://ankauf.goldvorsorge.at/1-oz-palladium-diverse-hersteller.html"
        ],
        'Quantity': [13, 3, 9, 1, 3, 655, 1],
        'Price': []
    }
    
    # Fetch prices from URLs
    prices = []
    for url in data['URL']:
        price = get_price(url)
        prices.append(price)
    
    data['Price'] = prices
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate subtotal for each item
    df['Subtotal'] = df['Quantity'] * df['Price']
    
    # Calculate total
    total = df['Subtotal'].sum()
    
    return total, df


def main():
    st.set_page_config(page_title="Total Value Calculator", layout="wide")
    
    st.title("Precious Metals Portfolio Value Calculator")
    
    # Initialize session state to store results
    if 'total' not in st.session_state:
        st.session_state.total = None
        st.session_state.df = None
    
    # Calculate on first page load
    if st.session_state.total is None:
        with st.spinner('Fetching current prices...'):
            st.session_state.total, st.session_state.df = calculate_total()
    
    # Center the button using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("Recalculate Total Value", use_container_width=True, type="primary"):
            # Recalculate when button is clicked
            with st.spinner('Fetching current prices...'):
                st.session_state.total, st.session_state.df = calculate_total()
            st.rerun()
    
    # Display the total (always shown)
    st.markdown("---")
    st.subheader(f"Total Portfolio Value: €{st.session_state.total:,.2f}")
    
    # Create display DataFrame with clickable links
    display_df = st.session_state.df[['Name', 'URL', 'Quantity', 'Price', 'Subtotal']].copy()
    
    # Create HTML anchor tags for the Name column
    display_df['Name'] = display_df.apply(lambda row: f'<a href="{row["URL"]}" target="_blank">{row["Name"]}</a>', axis=1)
    
    # Format currency columns
    display_df['Price'] = display_df['Price'].apply(lambda x: f"€{x:,.2f}")
    display_df['Subtotal'] = display_df['Subtotal'].apply(lambda x: f"€{x:,.2f}")
    
    # Drop URL column as it's now embedded in Name
    display_df = display_df[['Name', 'Quantity', 'Price', 'Subtotal']]
    
    st.markdown("### Portfolio Breakdown")
    st.markdown("*Click on product names to view source pages*")
    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
