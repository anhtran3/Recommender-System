"""
Utility functions used in multiple pages of the app.
"""

import pandas as pd
import pickle
import streamlit as st

@st.cache
def load_customer_data():
    """ Load the customer data file.

    Returns
    -------
    pd.DataFrame
        The data stored in the customer info file.
    """
    return pd.read_feather("data/customer_info.feather")


@st.cache
def load_country_list():
    """ Get a list of the countries in the customer data.
    
    Returns
    -------
    pd.Series
        Unique list of the countries.
    """
    df = load_customer_data()
    return df["country"].drop_duplicates().sort_values()


@st.cache
def load_customers_for_country(country):
    """ Get the customers that are in a given country.
    
    Parameters
    ----------
    country: str
        The name of the country to filter on.
    
    Returns
    -------
    dict
        { soldto number: customer name }
    """
    df = load_customer_data()
    df = df.loc[
        (df["country"] == country) & (df["deletion_flag"] == "#") &
        (df["salesorgs"].notnull()),
        ["soldto", "soldto_name"]
    ]
    df = df.sort_values(by="soldto").drop_duplicates().set_index("soldto")
    return df["soldto_name"].to_dict()


@st.cache
def load_customer_name(customers):
    """ Get names for a list of customers. 
    
    The returned list of names will be in the same order as the list
    of customer numbers provided in the customers parameter.  If we
    can't find a name for a given customer number we use the number in
    its place.

    Parameters
    ----------
    customers: iterable
        The list of customer numbers to get names for.

    Returns
    -------
    list
        The names that correspond with the customer numbers.
    """
    df = load_customer_data()
    name = df.set_index("soldto")["soldto_name"].to_dict()
    return [name.get(c, c) for c in customers]


@st.cache
def load_customer_country(customers):
    """ Get the countries of the customers in the given list.
    
    The returned list will be in the same order as the list of customer
    numbers provided in the customers parameter.  If we can't find a
    country an empty string is used in its place.

    Parameters
    ----------
    customers: iterable
        The list of customer numbers to get names for.
    
    Returns
    -------
    list
        The countries that correspond with the customer numbers.
    """
    df = load_customer_data()
    name = df.set_index("soldto")["country"].to_dict()
    return [name.get(c, c) for c in customers]


@st.cache
def load_customer_salesorgs(customer):
    """ Get the sales organisations a customer exists in. 
    
    Parameters
    ----------
    customer: str
        The soldto number of the customer.

    Returns
    -------
    list
        The sales organisations that the customer exists in.
    """
    df = load_customer_data()
    return df.loc[df["soldto"] == customer, "salesorgs"].values[0]


@st.cache
def load_material_data():
    """ Load the material data file.
    
    Returns
    -------
    pd.DataFrame
        The data stored in the material info file.
    """
    return pd.read_parquet("data/material_info.parquet")


@st.cache
def load_material_descriptions(materials):
    """ Get descriptions for the provided list of materials.
    
    The returned list of descriptions will be in the same order as the
    part numbers in the materials parameter.  If a description can't
    be found the part number will be used in its place.

    Parameters
    ----------
    materials: iterable
        The list of part numbers to get descriptions for.

    Returns
    -------
    list
        The descriptions.
    """
    df = load_material_data()
    descriptions = df["description"].to_dict()
    return [descriptions.get(m, m) for m in materials]


def load_material_description_list():
    """ Load description dictionary for materials.

    Returns
    -------
    dict
        The descriptions
    """
    df = pd.read_parquet("data/material_info.parquet")
    return df["description"].to_dict()


@st.cache
def load_material_types(materials):
    """ Get product lines for the provided list of materials.

    The returned list of product lines will be in the same order
    as the part number in the materials parameter. The provided list
    of materials are filtered with original part numbers.

    Parameters
    ----------
    materials: pd.Index
        The list of part numbers to get product lines for.
    
    Returns
    -------
    list
        The product lines that correspond with materials indices.
    """
    df = load_material_data()
    product_lines = df.loc[
        materials.intersection(df.index), "product_line"
    ].drop_duplicates()
    return product_lines


@st.cache
def load_materials_for_product_line(lines):
    """ Get list of materials for the provided product lines.

    Parameters
    ----------
    lines: iterable
        The list of product lines to filter on.

    Returns
    -------
    pd.Index
        The material index list that correspond to product lines.
    """
    df = load_material_data()
    return df[df["product_line"].isin(lines)].index


@st.cache
def load_material_availability():
    """ Load the material availability file. 
    
    Returns
    -------
    pd.DataFrame
        Dataframe with materials as the index, sales organisations as
        the columns and 1 or 0 for values (with 1 indicating the
        material is available in the sales organisation).
    """
    return pd.read_parquet("data/material_availability.parquet")


@st.cache
def load_salesorg_items(salesorg):
    """ Get list of materials available in a given sales organisation.
    
    Parameters
    ----------
    salesorg: str
        The sales organisation to filter on.
    
    Returns
    -------
    pd.Index
        The materials available in that sales organisation.
    """
    df = load_material_availability()
    # Remove the first row 
    df = df.iloc[1:, :]
    return df[df[salesorg] == 1].index


@st.cache
def load_salesorg_list():
    """ Get a list of sales organisations.
    
    Returns
    -------
    list
        Sales organisations the user can choose from.
    """
    df = load_material_availability()
    return sorted(df.columns.drop_duplicates())


@st.cache(allow_output_mutation=True)
def load_model():
    """ Load the trained model of customers - materials.
    
    Returns
    -------
    implicit.bpr.BayesianPersonalizedRanking
        The trained model.
    """
    with open("data/model.pickle", "rb") as f:
        return pickle.load(f)


@st.cache(allow_output_mutation=True)
def load_material_model():
    """ Load the trained model of materials - customers.
    
    Returns
    -------
    implicit.bpr.BayesianPersonalizedRanking
        The trained model of materials - customers.
    """
    with open("data/material_model.pickle", "rb") as f:
        return pickle.load(f)


@st.cache
def load_matrix():
    """ Load the sparse matrix that was used to train Recommender model.
    
    Returns
    -------
    scipy.sparse.csr_matrix
        Sparse matrix with customers for rows and materials for
        columns.
    """
    with open("data/matrix.pickle", "rb") as f:
        return pickle.load(f)


@st.cache(allow_output_mutation = True)
def load_material_matrix():
    """ Load the sparse matrix that was used to train Target Customer model.
    
    Returns
    -------
    scipy.sparse.csr_matrix
        Sparse matrix with materials for rows and customers for
        columns.
    """
    with open("data/material_matrix.pickle", "rb") as f:
        return pickle.load(f)


@st.cache(allow_output_mutation = True)
def load_year_matrix():
    """ Load the sparse matrix of latest order year.

    Returns 
    -------
    scipy.sparse.csr_matrix
        Sparse matrix with customers for rows and materials for
        columns.
    """
    with open ("data/year_matrix.pickle", "rb") as f:
        return pickle.load(f)


@st.cache
def load_material_index():
    """ Load the materials index used to construct the matrix.
    
    Returns
    -------
    pd.Series
        Part numbers as the index, position in the matrix as the
        values.
    """
    with open("data/material_ix.pickle", "rb") as f:
        return pickle.load(f)


@st.cache
def load_customer_index():
    """ Load the customer index used to construct the matrix.
    
    Returns
    -------
    pd.Series
        Customer numbers as the index, position in the matrix as the
        values.
    """
    with open("data/soldto_ix.pickle", "rb") as f:
        return pickle.load(f)
