#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 15:11:51 2022
Last modification : 31/12/2022
Version number : 1.0.4
@author: nicollemathieu
"""

import sys
import pandas as pd
from quittance import save_rent_receipt


def read_and_clean_csv_file(file):
    """
    Read and clean csv file containing account statement for a given year.

    Parameters
    ----------
    file : str
        Relative path to the csv file containing account statement

    Returns
    -------
    df_rent : pandas.dataframe
        Dataframe containing only data relative to rent receipt.
    """
    # Convert csv file content into a dataframe
    df = pd.read_csv(file, encoding='latin1', sep=";")
    # Filtering space and uppercase from column names
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.lower()
    # Filtering rows beginning by "Loyer"
    df_rent = df[df["transaction"].str.contains("^Loyer")]
    # Dropping Expense row if contains only NaN values else exit program
    df_rent = df_rent.dropna(axis=1, how='all')
    if "expense" in df_rent.columns:
        print("Error in csv file. One rent is not classified as Income")
        sys.exit()
    # Dropping useless column (i.e Balance CC)
    df_rent.drop(["balancecc"], axis=1, inplace=True)
    # Change date column into datetime object pandas
    df_rent['date'] = pd.to_datetime(df_rent['date'], format="%d/%m/%Y")
    # Change column type of income to numeric
    df_rent['income'] = df_rent['income'].str.replace(',', '.')
    df_rent['income'] = pd.to_numeric(df_rent['income'])
    return df_rent


def extract_info_from_row(rent_info):
    """
    Extract from str containing information for rent receipt values which
    will be used in the global dictionary
    Parameters
    ----------
    rent_info : str
        String containing all information for rent receipt

    Returns
    -------
    dict_rent_info :dict
        Dictionary containing information which were extracted from the input
        string
    """
    # Initiate dictionary
    dict_rent_info = dict()
    # Split row information with space
    split_text = rent_info.split()
    # Extract month for rent receipt and clean accent
    month = split_text[1]
    accent = {'\x9e': 'û', '\x8e': 'é'}
    for x, y in accent.items():
        month = month.replace(x, y)
    dict_rent_info["mois"] = [month]
    # Extract room number
    dict_rent_info['chambre'] = int(split_text[split_text.index("Chambre") + 1])
    # Extract rental charge amount
    dict_rent_info['charge'] = int(split_text[split_text.index("Charge") + 1])
    # Extract tenant's civility
    if split_text[2] in ["Mr", "Mme", "Mlle"]:
        index_end = split_text.index("Chambre")
        dict_rent_info['locataire'] = split_text[2:index_end]
    else:
        print(f"Error in csv file. Tenant civility cannot be identified for "
              f"line{rent_info}")
        sys.exit()
    return dict_rent_info


def define_rent_receipt_dictionary(date, rent_info, amount):
    """
    Create a dictionary for save_rent_receipt function based on date and
    transaction value of a dataframe row

    Parameters
    ----------
    date : pandas.timestamps
        Date of payment in datetime format
    rent_info : str
        String containing all information for rent receipt
    amount : str
        Amount for rent receipt

    Returns
    -------
    rent_receipt : dict
        Dictionary that contains data to establish rent receipt based on
        save_rent_receipt function
    """
    # Initiate rent receipt dictionary
    rent_receipt = dict()
    # Adding dictionary values based on payment date value
    rent_receipt['annee'] = date.year
    rent_receipt['date_paiement'] = [str(date.strftime("%d/%m/%Y"))]
    # Adding dictionary value based on rent amount
    rent_receipt['montant'] = amount
    # Adding dictionary values based on rent_info value
    rent_info = extract_info_from_row(rent_info)
    # Dictionary merge
    rent_receipt = {**rent_receipt, **rent_info}
    return rent_receipt


def extract_data_from_account_statement(file):
    """
    Extract information from csv file and gather it into a list of dictionaries
    each of which correspond to a rent receipt
    Parameters
    ----------
    file : str
        Relative path to the csv file containing account statement

    Returns
    -------
    list_dict_rent_receipt : list
        List containing all dictionaries, each of which correspond to a rent
        receipt
    """
    # Read and clean account statement data
    df = read_and_clean_csv_file(file)
    # Create a list of dictionary each corresponding to a rent receipt
    list_dict_rent_receipt = list()
    for index, rows in df.iterrows():
        dict_rent_receipt = define_rent_receipt_dictionary(rows["date"],
                            rows["transaction"], rows["income"])
        list_dict_rent_receipt.append(dict_rent_receipt)
    return list_dict_rent_receipt


if __name__ == '__main__':
    # Define csv file corresponding to a year account statement
    csv_file = 'year2022.csv'
    # Fetch data from csv file
    all_rent_receipt = extract_data_from_account_statement(csv_file)
    # Creating rent receipt for each dictionary in the list
    for rr in all_rent_receipt:
        save_rent_receipt(rr)
