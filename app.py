import streamlit as st
import requests
import pandas as pd
import openai

# 1. Funksjon for å hente ordre fra WooCommerce
def fetch_woocommerce_orders(per_page=10):
    """
    Henter inntil 'per_page' ordrer fra WooCommerce REST API.
    Du kan utvide om du vil ha flere sider (eksempel).
    """
    base_url = st.secrets["woo"]["base_url"]  # "https://din-butikk.no/wp-json/wc/v3"
    ck = st.secrets["woo"]["consumer_key"]
    cs = st.secrets["woo"]["consumer_secret"]

    params = {"per_page": per_page}
    response = requests.get(f"{base_url}/orders", params=params, auth=(ck, cs))
    response.raise_for_status()
    return response.json()

# 2. Funksjon for å "flate ut" ordrer til ordrelinjer
def flatten_orders_to_lineitems(orders, max_lines=100):
    """
    Returnerer maks 'max_lines' linjer.
    Hver rad representerer en line_item i ordren.
    """
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
            # 'total' er ofte en streng, konverter til float om du vil summere
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

            # Hvis vi når max_lines, stopper vi
            if len(flattened_rows) >= max_lines:
                break

        if len(flattened_rows) >= max_lines:
            break

    return flattened_rows

# 3. Funksjon for å sende data til ChatGPT
def analyze_line_items_with_gpt(df_line_items):
    """
    Bruker OpenAI API for å analysere data. Prompten er ganske enkel nå.
    Du kan utvide denne etter behov.
    """
    openai.api_key = st.secrets["openai"]["api_key"]

    # Eksempel: Lag en enkel oppsummering i promptet
    total_lines = len(df_line_items)
    product_count = df_line_items["Product Name"].nunique()
    total_revenue = df_line_items["Line Total"].sum()

    prompt = f"""
    Jeg har {total_lines} ordrelinjer fra en WooCommerce-butikk,
    fordelt på {product_count} ulike produkter.
    Total omsetning blant disse linjene er {total_revenue} NOK.

    Kan du gi en kort analyse på norsk av dette salget,
    mulige årsaker til resultatet, og noen tips for å øke salget videre?
    """

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].text.strip()


########################
# BRUK AV st.session_state
########################

# Sørg for at vi har 'df_line_items' og 'analysis_result' i session_state.
if "df_line_items" not in st.session_state:
    st.session_state["df_line_items"] = None

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# Tittel på appen
st.title("StoreIQ - WooCommerce + ChatGPT")

# Vis en knapp for å hente ordrelinjer
if st.button("Hent ordrelinjer"):
    try:
        # Henter ordrer
        orders = fetch_woocommerce_orders(per_page=10)
        # Flatter dem til ordrelinjer
        flattened = flatten_orders_to_lineitems(orders, max_lines=100)

        if len(flattened) == 0:
            st.warning("Fant ingen ordrelinjer.")
            st.session_state["df_line_items"] = None
        else:
            # Konverter til DataFrame og lagre i session_state
            df = pd.DataFrame(flattened)
            st.session_state["df_line_items"] = df
            st.success(f"Hentet {len(df)} linjer (max 100).")
            st.session_state["analysis_result"] = None  # tilbakestille gammel analyse
    except Exception as e:
        st.error(f"Feil ved henting av data: {e}")

# Hvis vi har data i session_state, vis tabellen
if st.session_state["df_line_items"] is not None:
    st.dataframe(st.session_state["df_line_items"])

    # Knapp for å analysere med ChatGPT
    if st.button("Analyser med ChatGPT"):
        try:
            df_lines = st.session_state["df_line_items"]
            analysis_result = analyze_line_items_with_gpt(df_lines)
            st.session_state["analysis_result"] = analysis_result
            st.success("Analyse ferdig!")
        except Exception as e:
            st.error(f"Feil ved ChatGPT-analyse: {e}")

    # Hvis vi har en analyse lagret, vis den
    if st.session_state["analysis_result"]:
        st.subheader("ChatGPT-analyse:")
        st.write(st.session_state["analysis_result"])
else:
    st.info("Ingen ordrelinjer å vise. Klikk på 'Hent ordrelinjer' først.")
