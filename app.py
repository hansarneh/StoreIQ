import streamlit as st

st.title("StoreIQ - Proof of Concept")
st.write("Hei, verden! Dette er min første Streamlit-app i skyen.")

import requests

st.title("StoreIQ - WooCommerce Demo")

# Eksempel på en funksjon for å hente ordre
def fetch_woocommerce_orders():
    base_url = st.secrets["woo"]["base_url"]
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    # WooCommerce API-endepunkt for ordrer
    endpoint = f"{base_url}/orders"

    # Her definerer vi parametere, for eksempel antall ordrer per side
    params = {
        "per_page": 10  # henter 10 ordrer
    }

    # Legger ved auth i requests (WooCommerce krever basic auth med ck/cs)
    response = requests.get(endpoint, params=params, auth=(ck, cs))
    response.raise_for_status()  # kaster feil hvis status != 200

    data = response.json()  # dette er en liste med ordre-dict
    return data

# Legger til en knapp i Streamlit for å trigge datainnhenting
if st.button("Hent ordre fra WooCommerce"):
    try:
        orders = fetch_woocommerce_orders()
        st.write(f"Fant {len(orders)} ordre.")
        # Vi kan vise ordredetaljer
        st.json(orders)  # Viser JSON i en utvidbar boks
    except Exception as e:
        st.error(f"Noe gikk galt: {e}")
