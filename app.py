import streamlit as st
import requests
import pandas as pd

def fetch_woocommerce_orders():
    base_url = st.secrets["woo"]["base_url"]  # F.eks. "https://.../wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    # Henter maks 10 ordrer per side (eksempel). Kan økes.
    params = {"per_page": 10}
    response = requests.get(
        f"{base_url}/orders",
        params=params,
        auth=(ck, cs)
    )
    response.raise_for_status()
    return response.json()

def flatten_orders_to_lineitems(orders, max_lines=100):
    """
    Tar en liste med ordrer og returnerer inntil max_lines ordrelinjer
    i en 'flat' liste. Hver rad representerer en enkelt line_item.
    """
    flattened_rows = []
    for order in orders:
        order_number = order["number"]
        first_name = order["billing"]["first_name"]
        last_name = order["billing"]["last_name"]
        customer_name = f"{first_name} {last_name}"

        line_items = order["line_items"]  # liste av produktene i denne ordren
        for item in line_items:
            product_name = item["name"]
            quantity = item["quantity"]
            # Ofte er "total" en streng. Vi kan konvertere til float for klar
