#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nicollemathieu
"""
import sys
from calendar import monthrange

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
    df = pd.read_csv(file, encoding="utf-8", sep=";")
    # Filtering space and uppercase from column names
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.lower()
    # Filtering rows beginning by "Loyer"
    df_rent = df[df["transaction"].str.contains("^Loyer")]
    # Dropping Expense row if contains only NaN values else exit program
    df_rent = df_rent.dropna(axis=1, how="all")
    if "expense" in df_rent.columns:
        print("Error in csv file. One rent is not classified as Income")
        sys.exit()
    # Dropping useless column (i.e Balance CC)
    df_rent.drop(["balancecc"], axis=1, inplace=True)
    # Change date column into datetime object pandas
    df_rent["date"] = pd.to_datetime(df_rent["date"], format="%d/%m/%Y")
    # Change column type of income to numeric
    df_rent["income"] = df_rent["income"].str.replace(",", ".")
    df_rent["income"] = pd.to_numeric(df_rent["income"])
    return df_rent


def extract_info_from_row(rent_info, dict_rent_info):
    """
    Extract from str containing information for rent receipt values which
    will be used in the global dictionary
    Parameters
    ----------
    rent_info : str
        String containing all information for rent receipt
    dict_rent_info :dict
        Dictionary containing base information on rent receipt.
        Will be complete by this function with information contained in
        rent_info string variable

    Returns
    -------
    dict_rent_info :dict
        Dictionary containing all information about rent receipt
    """
    # Detect if row contains "PRORATA keyword"
    if "PRORATA" in rent_info:
        # Extract info for a customized rent_receipt
        custom_info = rent_info[rent_info.find("(") + 1 : rent_info.find(")")]
        # Filter rent_info
        rent_info = rent_info[: rent_info.find("(")]
        # Create "customized" key into dict_rent_info with appropriate content
        dict_rent_info["customized"] = evaluate_prorata(
            custom_info, dict_rent_info
        )
    # Split row information with space
    split_text = rent_info.split()
    # Extract month for rent receipt and clean accent
    month = split_text[1]
    accent = {"\x9e": "û", "\x8e": "é"}
    for x, y in accent.items():
        month = month.replace(x, y)
    dict_rent_info["mois"] = [month]
    # Extract room number
    dict_rent_info["chambre"] = int(
        split_text[split_text.index("Chambre") + 1]
    )
    # Extract rental charge amount and calculate rent without charge
    dict_rent_info["charge"] = int(split_text[split_text.index("Charge") + 1])
    # Extract tenant's civility
    if split_text[2] in ["Mr", "Mme", "Mlle"]:
        index_end = split_text.index("Chambre")
        dict_rent_info["locataire"] = split_text[2:index_end]
    else:
        print(
            f"Error in csv file. Tenant civility cannot be identified for "
            f"line{rent_info}"
        )
        sys.exit()
    return dict_rent_info


def evaluate_prorata(prorata_info, base_info):
    """Prorata information extracted from dataframe row need to be processed
    by this function before adding dict key 'customized' to dict_rent_info
    Input format = PRORATA XX/XX --> or PRORATA --> XX/XX
    Output format = XX/XX/XX YY/YY/YY ZZZ with X beginning date, y end date and
    Z amount in euros for this period.

    Args:
        prorata_info (str):
        String containing information about prorata period extracted from
        dataframe row.
        base_info (dict):
        Dictionnary containing info about year and rent amount. Correspond to
        object dict_rent_info that contains info sent to latex.
    Returns:
        prorate_value (str):
        Information processed and ready to be add into dict_rent_info with key
        'customized'
    """
    # Detect arrow position compare to prorata date
    prorata_split = prorata_info.split()
    arrow = "-->"
    year_value = str(base_info["annee"])[-2:]
    if not len(prorata_split) == 3:
        print("Error in csv file. Prorata rent do not respect format")
        sys.exit()
    if prorata_split.index(arrow) == 1:
        # Case when arrow is before date. Means rent is from beginning of month
        # till the date
        begin_date = "01/" + prorata_split[2][-2:] + "/" + year_value
        end_date = prorata_split[2] + "/" + year_value
    elif prorata_split.index(arrow) == 2:
        # Case when arrow is after date. Means rent is from date till the end
        # of month
        number_last = monthrange(
            int(base_info["annee"]), int(prorata_split[1][-2:])
        )[1]
        begin_date = prorata_split[1] + "/" + year_value
        end_date = (
            str(number_last) + "/" + prorata_split[1][-2:] + "/" + year_value
        )
    else:
        # Other case which will not be supported
        print("Error in csv file. Prorata rent do not respect format")
        sys.exit()
    # Concatening info in one line
    prorata_value = " ".join([begin_date, end_date, str(base_info["loyer"])])
    return prorata_value


def define_rent_receipt_dictionary(date, rent_info, amount):
    """
    Create a dictionary for save_rent_receipt function based on date and
    transaction value of a dataframe row

    Parameters
    ----------
    date : pandas.timestamps
        Date of payment in datetime format
    rent_info: str
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
    rent_receipt["annee"] = date.year
    rent_receipt["date_paiement"] = [str(date.strftime("%d/%m/%Y"))]
    # Adding dictionary value based on rent amount
    rent_receipt["loyer"] = float(amount)
    # Adding dictionary values based on rent_info value
    rent_receipt = extract_info_from_row(rent_info, rent_receipt)
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
        dict_rent_receipt = define_rent_receipt_dictionary(
            rows["date"], rows["transaction"], rows["income"]
        )
        list_dict_rent_receipt.append(dict_rent_receipt)
    return list_dict_rent_receipt


def compute_sum_rent_receipt(file):
    """
    Return sum of rent receipt from csv file.

    Parameters
    ----------
    file : str
        Relative path to the csv file containing account statement

    Returns
    -------
    income : str
        Str corresponding to income relative to rent receipt.
    """
    # Convert csv file content into a dataframe
    df = pd.read_csv(file, encoding="utf-8", sep=";")
    # Filtering space and uppercase from column names
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.lower()
    # Filtering dataframe
    df = df[df["transaction"].str.contains("^Loyer")]
    df = df["income"].str.replace(",", ".")
    # Compute sum of rent receipt as income
    income = str(df.astype("float").sum())
    return income


if __name__ == "__main__":
    # Define csv file corresponding to a year account statement
    csv_file = "used_files/input_file.csv"
    # Fetch data from csv file
    all_rent_receipt = extract_data_from_account_statement(csv_file)
    # Creating rent receipt for each dictionary in the list
    for rr in all_rent_receipt:
        save_rent_receipt(rr)
    # Log rent receipt sum
    sum_rent_receipt = compute_sum_rent_receipt(csv_file)
    print(f"\nInformation: Sum rent receipt is = {sum_rent_receipt} €\n")
