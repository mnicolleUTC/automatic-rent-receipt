#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 15:11:51 2022
Last modification : 30/12/2022
Version number : 1.0.3
@author: nicollemathieu
"""

import os
import sys
import pandas as pd
from quittance import save_rent_receipt


def extract_data_from_account_statement(file):
    """
    Read csv file containing account statement for a given year.
    Extract inf

    Parameters
    ----------
    file : str
        Relative path to the csv file containing account statement

    Returns
    -------
    yaml_content : dict
        Dictionary containing yaml file content
    """
    # Convert csv content into a dataframe
    df = pd.read_csv(file)
    return yaml_content

if __name__ == '__main__':
    # Define csv file corresponding to a year account statement
    csv_file = 'year2022.csv'
    # Fetch data from csv file
    extract_data_from_account_statement(csv_file)


