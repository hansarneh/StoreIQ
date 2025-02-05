import streamlit as st
import requests
import pandas as pd

def fetch_woocommerce_orders():
    base_url = st.secrets["woo"]["base_url"]  # "https://.../wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    endpoint = f"{base_url}/orders"
    params = {"per_page": 10}
    response = requests.get(endpoint, params=params, auth=(ck, cs))
    response.raise_for_status()
    return response.json()

st.title("StoreIQ - WooCommerce Orders with Line Items")

if st.button("Hent ordre"):
    try:
        orders = fetch_woocommerce_orders()
        st.write(f"Fant {len(orders)} ordre.")

        # Lag en tabell med grunninfo om alle ordrer
        data_rows = []
        for order in orders:
            data_rows.append({
                "Order Number": order["number"],
                "Customer Name": f"{order['billing']['first_name']} {order['billing']['last_name']}",
                "Total": order["total"]
            })
        df_orders = pd.DataFrame(data_rows)
        st.dataframe(df_orders)

        # Deretter viser vi detaljene ordre for ordre, med expanders
        st.write("## Ordredetaljer")
        for order in orders:
            order_no = order["number"]
            first_name = order["billing"]["first_name"]
            last_name = order["billing"]["last_name"]
            total = order["total"]
            
            # Viser en kort overskrift for hver ordre
            st.subheader(f"Ordre {order_no}: {first_name} {last_name} - Total: {total}")

            # Med en expander for å vise linjeelementene
            with st.expander("Vis ordrelinjer"):
                line_items = order["line_items"]  # liste med varenavn, antall, beløp
                line_rows = []
                for item in line_items:
                    line_rows.append({
                        "Produkt": item["name"],
                        "Antall": item["quantity"],
                        "Linjetotal": item["total"]
                    })
                
                df_line_items = pd.DataFrame(line_rows)
                st.dataframe(df_line_items)
    except Exception as e:
        st.error(f"Noe gikk galt: {e}")
