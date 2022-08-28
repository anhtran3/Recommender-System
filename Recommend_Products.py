"""
Main page: Recommend Products for a specific customer.
"""

import pandas as pd
import streamlit as st
import numpy as np 


from io import BytesIO


import utils


PAGE_TITLE = "Recommend Products"
st.set_page_config(layout="wide", page_title=PAGE_TITLE)

MODEL = utils.load_model()
MATRIX = utils.load_matrix()
SOLDTO_IX = utils.load_customer_index()
MATERIAL_IX = utils.load_material_index()
YEAR_MATRIX = utils.load_year_matrix()

def page():
    """ Create the Streamlit interface for this page. """
    st.title(PAGE_TITLE)

    # The customer selector.
    country_col, customer_col, org_col = st.columns(3)
    country = country_col.selectbox(
        "Select Country", utils.load_country_list()
    )
    customer_list = utils.load_customers_for_country(country)
    if len(customer_list) == 0:
        customer_col.write("No customers for this country.")
        return
    customer = customer_col.selectbox(
        "Select Customer", customer_list.keys(),
        format_func=lambda x: "{} - {}".format(x, customer_list[x])
    )
    org = org_col.selectbox(
        "Select Sales Organisation",
        utils.load_customer_salesorgs(customer)
    )
    
    customer_id = SOLDTO_IX[customer]
    avail_items = utils.load_salesorg_items(org)
    avail_items = avail_items.intersection(MATERIAL_IX.index)

    # Parameters for the recommendations.
    no_recs = st.slider(
        "Number of Products to Recommend", min_value=10,
        max_value=100, value=20
    )

    # Get the order year of selected customer.
    customer_years_matrix = YEAR_MATRIX[customer_id]
    customer_years_list = np.array(customer_years_matrix[customer_years_matrix.nonzero()])[0]

    # Order year selector.
    order_year = st.selectbox(
        "Filter by Order Year", 
        sorted(set(np.append(customer_years_list,"None")))
    )
    if order_year != "None":
        year_fil_items = (customer_years_matrix.nonzero()[1][customer_years_list >= int(order_year)]).astype(str)
        # Select items that are purchased before selected year. 
        avail_items = avail_items.difference(year_fil_items)
        avail_items_ix  = MATERIAL_IX[avail_items]
    else:
        avail_items_ix = MATERIAL_IX[avail_items]

    # Load product lines for available items.
    material_types = sorted(set(utils.load_material_types(avail_items)))

    # Product line selector.
    product_line = st.multiselect(
        "Filter by Product Line", material_types
    )
    if product_line:
        line_fil_items = utils.load_materials_for_product_line(product_line)
        # Filter the available items with product line filter
        avail_items = avail_items.intersection(line_fil_items)
        avail_items_ix = MATERIAL_IX[avail_items]
    else:
        avail_items_ix = MATERIAL_IX[avail_items]
    

    similar_customers_col, rec_col = st.columns(2)

    # Show a list of customers that are similar to the selected one.
    with similar_customers_col:
        ids, _ = MODEL.similar_users(customer_id, N=21)
        st.subheader("Similar Customers")
        rec_customers = SOLDTO_IX.index[ids]
        df = pd.DataFrame({
            "Soldto": rec_customers,
            "Name": utils.load_customer_name(rec_customers),
            "Country": utils.load_customer_country(rec_customers)
        })
        df = df.loc[1:]
        st.table(df)

    # Show the product recommendations.
    with rec_col:
        ids, _ = MODEL.recommend(
            customer_id, MATRIX[customer_id],
            filter_already_liked_items= False,
            N=no_recs, items=avail_items_ix
        )
        st.subheader("Product Recommendations")
        rec_materials = MATERIAL_IX.index[ids]
        df = pd.DataFrame({
            "Material": rec_materials,
            "Description": utils.load_material_descriptions(rec_materials)
        })
        st.table(df)

        # Create an output in IO.
        output = BytesIO()
        df.to_excel(output, sheet_name="Recommendations")
        st.download_button(
            label="Download as Excel", data=output.getvalue(),
            file_name="recommendations-{}.xlsx".format(customer),
            mime="application/vnd.ms-excel"
        )

page()
