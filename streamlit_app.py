import streamlit as st
import pandas as pd
from datetime import datetime, timezone

import math
import os
import shutil

INITIAL_WAIT_MS = 3_000
PRICE_TIMEOUT_MS = 20_000
NAVIGATION_TIMEOUT_MS = 45_000
# Scope this to the main product, excluding prices in related-product cards.
PRICE_SELECTOR = (
    ".add-to-cart-area [id^='product-price-'][data-price-amount]"
)


class PriceFetchError(RuntimeError):
    """A complete, usable set of current prices could not be retrieved."""


def get_price(url, page):
    """Navigate with JavaScript enabled, wait three seconds, then read the price."""
    response = page.goto(
        url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS
    )
    if response is not None and response.status >= 400:
        raise PriceFetchError(f"Product page returned HTTP {response.status}: {url}")

    # Unlike sleeping after requests.get(), this lets page JavaScript and
    # automatic redirects run while the browser retains the site's cookies.
    page.wait_for_timeout(INITIAL_WAIT_MS)
    price_node = page.locator(PRICE_SELECTOR).first
    price_node.wait_for(state="visible", timeout=PRICE_TIMEOUT_MS)

    try:
        price = float(price_node.get_attribute("data-price-amount"))
    except (TypeError, ValueError) as exc:
        raise PriceFetchError(f"The product price was invalid: {url}") from exc
    if not math.isfinite(price) or price <= 0:
        raise PriceFetchError(f"The product price was invalid: {url}")
    return price


def fetch_prices(urls):
    """Use one isolated browser session for the whole portfolio; return no partial set."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    executable = os.environ.get("PMCALC_CHROMIUM_EXECUTABLE")
    if not executable:
        executable = shutil.which("chromium") or shutil.which("chromium-browser")
    launch_options = {"headless": True}
    if executable:
        launch_options["executable_path"] = executable

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch_options)
            try:
                context = browser.new_context(locale="de-AT")
                try:
                    page = context.new_page()
                    prices = []
                    for url in urls:
                        try:
                            prices.append(get_price(url, page))
                        except PlaywrightError as exc:
                            # A check can occasionally require human interaction.
                            # Do not click verification controls or fabricate prices.
                            try:
                                title = page.title().casefold()
                            except PlaywrightError:
                                title = ""
                            if "sicherheitsprüfung" in title:
                                raise PriceFetchError(
                                    "Goldvorsorge's security check did not finish "
                                    "automatically. Please try again later."
                                ) from exc
                            raise PriceFetchError(
                                f"Could not load the current product price: {url}"
                            ) from exc
                    return prices
                finally:
                    context.close()
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise PriceFetchError(
            "The price browser could not start or complete the request. "
            "Please try again later."
        ) from exc


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
    data['Price'] = fetch_prices(data['URL'])
    
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
    
    # Keep the last complete result if a later refresh fails.
    for key, default in (
        ("total", None), ("df", None), ("prices_updated_at", None),
        ("price_error", None),
    ):
        st.session_state.setdefault(key, default)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        refresh = st.button(
            "Recalculate Total Value", use_container_width=True, type="primary"
        )

    if refresh or st.session_state.total is None:
        with st.spinner("Loading product pages and waiting for current prices..."):
            try:
                total, df = calculate_total()
            except PriceFetchError as exc:
                st.session_state.price_error = str(exc)
            else:
                st.session_state.total = total
                st.session_state.df = df
                st.session_state.prices_updated_at = datetime.now(timezone.utc)
                st.session_state.price_error = None

    if st.session_state.price_error:
        st.error(st.session_state.price_error)
        if st.session_state.total is not None:
            st.warning("Showing the last successfully fetched prices.")

    if st.session_state.total is None:
        st.info("No complete price set is available yet. Use the button above to retry.")
        st.stop()

    if st.session_state.prices_updated_at is not None:
        st.caption(
            "Prices last updated: "
            + st.session_state.prices_updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        )

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
