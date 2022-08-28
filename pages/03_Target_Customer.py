"""
Page 3: Find target customers for a selected products
"""
import streamlit as st
import pandas as pd


from io import BytesIO


import utils

PAGE_TITLE = "Identify Target Customers for a Product"
st.set_page_config(layout="wide", page_title=PAGE_TITLE)

MODEL = utils.load_material_model()
MATRIX = utils.load_material_matrix()
MATERIAL_IX = utils.load_material_index()
SOLDTO_IX = utils.load_customer_index()
MATERIALS_LOOKUP = utils.load_material_description_list()

def page():
    """ Create the Streamlit interface for this page. """
    st.title(PAGE_TITLE)

    org_col, materials_col = st.columns(2)
    org = org_col.selectbox(
        "Select Sales Organization", utils.load_salesorg_list()
    )
    with st.form(key="target_customers"):
        avail_items = utils.load_salesorg_items(org)
        selected_materials = materials_col.multiselect(
            "Select Materials", avail_items, 
            format_func= lambda x: "{} - {}".format(
            x, MATERIALS_LOOKUP.get(x,x)
            )
        )
        
        # Parameters for the recommendations.
        no_cus = st.slider(
            "Number of Recommended Customers", min_value = 10, max_value = 50,
            value = 20
        )

        material_submit = st.form_submit_button("Generate Recommemdations")
    
    if material_submit and len(selected_materials) != 0:
        selected_materials_ix = MATERIAL_IX[selected_materials]
        # Show target customers.
        ids, scores = MODEL.recommend(
            selected_materials_ix, MATRIX[selected_materials_ix], 
            filter_already_liked_items = True,
            N = no_cus 
        )
        rec_frames = []
        for customer_ids, customer_scores in zip(ids, scores):
            rec_customers = SOLDTO_IX.index[customer_ids]
            df = pd.DataFrame({
                "Customer": rec_customers,
                "Name": utils.load_customer_name(rec_customers),
                "Country": utils.load_customer_country(rec_customers),
                "Score": customer_scores
            })
            rec_frames.append(df)
        df = pd.concat(rec_frames, ignore_index= True)
        df = df.sort_values(by = "Score", ascending= False).reset_index()
        df = df[["Customer", "Name", "Country"]]
        st.table(df)

        # Create output in IO
        output = BytesIO()
        df.to_excel(output, sheet_name = "Target_Customer", index = False)
        st.download_button(
            label = "Download as Excel", data = output.getvalue(), 
            file_name = "target-customer-{}.xlsx".format(selected_materials),
            mime = "application/vnd.ms-excel"
        )

    # If user do not make any selection, return nothing.
    else:
        return 

page()