import streamlit as st
import requests
import pandas as pd
import openai

def fetch_woocommerce_orders():
    base_url = st.secrets["woo"]["base_url"]  # "https://din-side.no/wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    params = {"per_page": 10}
    response = requests.get(f"{base_url}/orders", params=params, auth=(ck, cs))
    response.raise_for_status()
    return response.json()

def flatten_orders_to_lineitems(orders, max_lines=100):
    flattened_rows = []
    for order in orders:
        order_number = order["number"]
        first_name = order["billing"]["first_name"]
        last_name = order["billing"]["last_name"]
        customer_name = f"{first_name} {last_name}"

        line_items = order["line_items"]
        for item in line_items:
            product_name = item["name"]
            quantity = item["quantity"]
            line_total = float(item["total"]) if item["total"] else 0.0

            row = {
                "Order Number": order_number,
                "Customer Name": customer_name,
                "Product Name": product_name,
                "Quantity": quantity,
                "Line Total": line_total
            }
            flattened_rows.append(row)

            if len(flattened_rows) >= max_lines:
                break
        if len(flattened_rows) >= max_lines:
            break
    return flattened_rows

def analyze_line_items_with_gpt(line_items_df):
    """
    Eksempel på hvordan vi kaller ChatGPT for å tolke oppsummert data.
    """
    openai.api_key = st.secrets["openai"]["api_key"]

    # Lag en enkel oppsummering for prompt
    product_count = line_items_df["Product Name"].nunique()
    total_revenue = line_items_df["Line Total"].sum()
    total_lines = len(line_items_df)

    # Bygg en prompt
    prompt = f"""
    Jeg har en liste med {total_lines} ordrelinjer, fordelt på {product_count} unike produkter.
    Den totale omsetningen (sum av alle 'Line Total') er {total_revenue} NOK.

    Gi en kort analyse av salget, mulige årsaker til resultatet, samt forslag til hvordan vi
    kan øke salget videre. Gjerne kommentér om du ser trender i produktnavn eller antall solgte varer.
    Svar på norsk.
    """

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=250,
        temperature=0.7
    )

    answer = response.choices[0].text.strip()
    return answer

st.title("StoreIQ - WooCommerce + ChatGPT")

# Knapper og logikk i Streamlit
if st.button("Hent ordrelinjer"):
    try:
        orders = fetch_woocommerce_orders()
        line_data = flatten_orders_to_lineitems(orders, max_lines=100)

        if len(line_data) == 0:
            st.write("Ingen ordrelinjer funnet.")
        else:
            df = pd.DataFrame(line_data)
            st.write(f"Viser {len(df)} ordrelinjer (max 100).")
            st.dataframe(df)

            # Knapp for AI-analyse
            if st.button("Analyser med ChatGPT"):
                result = analyze_line_items_with_gpt(df)
                st.subheader("AI-analyse:")
                st.write(result)

    except Exception as e:
        st.error(f"Noe gikk galt: {e}")
