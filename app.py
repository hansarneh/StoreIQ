import streamlit as st
import requests
import pandas as pd
import openai

# 1. Funksjon for å hente ordre fra WooCommerce
def fetch_woocommerce_orders(per_page=10):
    base_url = st.secrets["woo"]["base_url"]  # "https://din-butikk.no/wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    params = {"per_page": per_page}
    response = requests.get(f"{base_url}/orders", params=params, auth=(ck, cs))
    response.raise_for_status()
    return response.json()

# 2. Funksjon for å "flate ut" ordrer til en liste med ordrelinjer
def flatten_orders_to_lineitems(orders, max_lines=100):
    flattened_rows = []
    for order in orders:
        order_number = order["number"]
        first_name = order["billing"]["first_name"]
        last_name = order["billing"]["last_name"]
        customer_name = f"{first_name} {last_name}"

        line_items = order.get("line_items", [])
        for item in line_items:
            product_name = item["name"]
            quantity = item["quantity"]
            line_total_str = item.get("total", "0")
            line_total = float(line_total_str) if line_total_str else 0.0

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

# 3. Funksjon for å bruke ChatGPT (ChatCompletion) på ordrelinjene
def analyze_line_items_with_gpt(df_line_items):
    openai.api_key = st.secrets["openai"]["api_key"]

    total_lines = len(df_line_items)
    product_count = df_line_items["Product Name"].nunique()
    total_revenue = df_line_items["Line Total"].sum()

    # Vi lager en prompt vi sender til ChatCompletion
    prompt = f"""
    Vi har hentet {total_lines} ordrelinjer fra WooCommerce, fordelt på {product_count} unike produkter.
    Totalsummen for disse linjene er {total_revenue} NOK.

    Kan du gi en kort analyse på norsk av dette salget,
    mulige årsaker til resultatet, og noen tips for å øke salget videre?
    """

    # Selve kallet til ChatCompletion (GPT-3.5-turbo)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du er en nyttig dataanalytiker med fokus på e-commerce."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )

    # Hent svar-tekst
    answer = response["choices"][0]["message"]["content"]
    return answer.strip()


#################################
# Oppsett av session_state
#################################

if "df_line_items" not in st.session_state:
    st.session_state["df_line_items"] = None

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None


#################################
# Streamlit-app
#################################

st.title("StoreIQ - WooCommerce + ChatGPT (ChatCompletion)")

# Knapper og logikk
if st.button("Hent ordrelinjer"):
    try:
        orders = fetch_woocommerce_orders(per_page=10)
        flattened = flatten_orders_to_lineitems(orders, max_lines=100)

        if len(flattened) == 0:
            st.warning("Fant ingen ordrelinjer.")
            st.session_state["df_line_items"] = None
        else:
            df = pd.DataFrame(flattened)
            st.session_state["df_line_items"] = df
            st.session_state["analysis_result"] = None
            st.success(f"Hentet {len(df)} linjer (maks 100).")
    except Exception as e:
        st.error(f"Feil ved henting av data: {e}")

# Hvis vi har data, vis den
if st.session_state["df_line_items"] is not None:
    st.dataframe(st.session_state["df_line_items"])

    # Knapp for å analysere med ChatCompletion
    if st.button("Analyser med ChatGPT"):
        try:
            df_lines = st.session_state["df_line_items"]
            result = analyze_line_items_with_gpt(df_lines)
            st.session_state["analysis_result"] = result
            st.success("Analyse ferdig!")
        except Exception as e:
            st.error(f"Feil ved analyse: {e}")

    # Viser eventuelt siste analyse
    if st.session_state["analysis_result"]:
        st.subheader("ChatGPT-analyse:")
        st.write(st.session_state["analysis_result"])
else:
    st.info("Ingen ordrelinjer å vise. Klikk 'Hent ordrelinjer' først.")
