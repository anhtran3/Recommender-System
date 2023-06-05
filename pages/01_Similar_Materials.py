"""
Page 1: Find similar materials to selected materials

The 01_Similar_Materials.py page allows users to discover similar materials based on a selected product. 
It provides an intuitive interface where users can input a product and receive recommendations for similar materials
"""

import pandas as pd
import streamlit as st


from io import BytesIO


import utils


PAGE_TITLE = "Find Similar Materials"
st.set_page_config(layout="wide", page_title=PAGE_TITLE)

MODEL = utils.load_model()
MATERIAL_IX = utils.load_material_index()

def page():
    """ Create the Streamlit interface for this page. """
    st.title(PAGE_TITLE)

    # Let the user select a sales org to determine which products should
    # be included in the recommendation.
    org = st.selectbox(
        "Select Sales Organisation", utils.load_salesorg_list()
    )

    with st.form(key="similar_materials"):
        avail_items = utils.load_salesorg_items(org)
        avail_items_ix = MATERIAL_IX[
            avail_items.intersection(MATERIAL_IX.index)
        ]
        descriptions = {a: b for a,b in zip(
            avail_items, utils.load_material_descriptions(avail_items)
        )}
        selected_materials = st.multiselect(
            "Select Materials", avail_items,
            format_func=lambda x: "{} - {}".format(x, descriptions.get(x, x))
        )
        no_recs = st.slider(
            "Number of Products to Recommend", min_value=10,
            max_value=100, value=20
        )
        material_submit = st.form_submit_button("Generate Recommendations")

    if material_submit and len(selected_materials) != 0:
        selected_materials_id = MATERIAL_IX[selected_materials]
        ids, scores = MODEL.similar_items(
            selected_materials_id, N=no_recs+len(selected_materials),
            items=avail_items_ix
        )
        # Create a data frame with the materials and scores for each
        # of the materials the user selected, combine the data frames
        # and take the average score for each recommended material to
        # generate the list we show to the user.
        rec_frames = []
        for material_ids, material_scores in zip(ids, scores):
            rec_materials = MATERIAL_IX.index[material_ids]
            df = pd.DataFrame({
                "Material": rec_materials,
                "Description": utils.load_material_descriptions(rec_materials),
                "Score": material_scores
            })
            # Remove the materials the user selected.
            rec_frames.append(df[~df["Material"].isin(selected_materials)])
    
        df = pd.concat(rec_frames, ignore_index=True)
        df = df.groupby(["Material", "Description"]).mean()
        df = df.sort_values(by="Score", ascending=False).reset_index()
        df = df[["Material", "Description"]].iloc[:no_recs, :]
        st.table(df)
        output = BytesIO()
        df.to_excel(output, sheet_name="Recommendations", index=False)
        st.download_button(
            label="Download as Excel", data=output.getvalue(),
            file_name="recommendations.xlsx",
            mime="application/vnd.ms-excel"
        )

    # If page loads with no selection, return nothing.
    else:
        return

page()
