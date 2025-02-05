import streamlit as st
import requests
import pandas as pd

def fetch_woocommerce_orders():
    base_url = st.secrets["woo"]["base_url"]  # f.eks. "https://nettside.no/wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    endpoint = f"{base_url}/orders"
    params = {
        "per_page": 10  # henter 10 ordrer
    }

    response = requests.get(endpoint, params=params, auth=(ck, cs))
    response.raise_for_status()
    return response.json()  # en liste med ordredikt

st.title("StoreIQ - WooCommerce Orders")

if st.button("Hent ordre fra WooCommerce"):
    try:
        orders = fetch_woocommerce_orders()
        st.write(f"Fant {len(orders)} ordre.")

        # Bygg en liste av dicts som blir til en tabell
        data_rows = []
        for order in orders:
            order_number = order["number"]  # "number" er ofte det "synlige" ordrenummeret
            first_name = order["billing"]["first_name"]
            last_name = order["billing"]["last_name"]
            total = order["total"]  # Merk: ofte en streng. Du kan evt. konvertere til float

            data_rows.append({
                "Order Number": order_number,
                "Customer Name": f"{first_name} {last_name}",
                "Total Amount": total
            })

        # Lag en DataFrame av dataene
        df = pd.DataFrame(data_rows)

        # Vis tabellen i Streamlit
        st.dataframe(df)
    except Exception as e:
        st.error(f"Noe gikk galt: {e}")
