"""
Page 2: Recommend products for new customer 

Users can select the sale organization, country, and similar customers for a new customer.
Based on these inputs, the code generates personalized product recommendations, 
considering factors such as previously purchased products

Users have the option to download them as an Excel file.

"""

import streamlit as st
import pandas as pd


from io import BytesIO


import utils


PAGE_TITLE = "Suggest Initial Order for New Customer"
st.set_page_config(layout="wide", page_title=PAGE_TITLE)

rec_output = []
MODEL = utils.load_model()
MATRIX = utils.load_matrix()
SOLDTO_IX = utils.load_customer_index()
MATERIAL_IX = utils.load_material_index()

def page():
    """ Create the Streamlit interface for this page. """
    st.title(PAGE_TITLE)

    # The customer selector.
    org = st.selectbox(
        "Select Sale Organization of the New Customer",
        utils.load_salesorg_list()
    )
    country_col, customer_col = st.columns(2)
    country = country_col.selectbox(
        "Select Country", utils.load_country_list()
    )
    
    # Parameters for the recommendations.
    already_purchased = st.checkbox(
    "Remove previously purchased products", value=True
    )
    no_recs = st.slider(
        "Number of Products to Suggest", min_value=10,
        max_value=100, value=20
    )

    with st.form(key = "suggest_new_customer"):
        customer_list = utils.load_customers_for_country(country)
        customer = customer_col.multiselect(
            "Similar Customers", customer_list.keys(),
            format_func=lambda x: "{} - {}".format(x, customer_list[x])
        )
        submitted = st.form_submit_button("Generate Recommendation")

        if submitted and len(customer) != 0:
            customer_id = SOLDTO_IX[customer]
            avail_items = utils.load_salesorg_items(org)
            avail_items_ix = MATERIAL_IX[avail_items.intersection(MATERIAL_IX.index)]

            # Show the product recommendations.
            ids, scores = MODEL.recommend(
                customer_id, MATRIX[customer_id], 
                filter_already_liked_items = already_purchased, 
                N = no_recs,
                items = avail_items_ix
            )
            rec_frames = []
            for material_ids, material_scores in zip(ids, scores):
                rec_materials = MATERIAL_IX.index[material_ids]
                df = pd.DataFrame({
                    "Material": rec_materials,
                    "Description": utils.load_material_descriptions(rec_materials),
                    "Score": material_scores
                })
                rec_frames.append(df)
            df = pd.concat(rec_frames, ignore_index= True)
            df = df.groupby(["Material", "Description"]).mean()
            df = df.sort_values(by = "Score", ascending= False).reset_index()
            df = df[["Material", "Description"]]
            st.table(df)
            rec_output.append(df)
        
        # If page loads with no selection, return nothing.
        else:
            return

    # Create output in IO.
    df = pd.concat(rec_output)
    output = BytesIO()
    df.to_excel(output, sheet_name = "New_Customer", index = False)
    st.download_button(
    label = "Download as Excel", data = output.getvalue(), 
    file_name = "new_customer.xlsx",
    mime = "application/vnd.ms-excel"
    )
   
page()
