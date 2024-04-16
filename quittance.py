#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 21:11:51 2022
Last modification : 30/12/2022
Version number : 1.0.2
@author: nicollemathieu
"""
import datetime
import locale
import os
import sys
from calendar import monthrange

import dateparser
import yaml
from jinja2.loaders import FileSystemLoader
from latex import build_pdf
from latex.jinja2 import make_env
from num2words import num2words


def read_yaml(yaml_file):
    """
    Read yaml file and return the content in a dictionary

    Parameters
    ----------
    yaml_file : str
        Relative path to the yaml file

    Returns
    -------
    yaml_content : dict
        Dictionary containing yaml file content
    """
    # Opening and fetching content
    with open(yaml_file, encoding="utf-8") as stream:
        yaml_content = yaml.safe_load(stream)
    # Converting dict key month and tenant into list
    yaml_content["mois"] = yaml_content["mois"].split()
    yaml_content["date_paiement"] = yaml_content["date_paiement"].split()
    # Adding room number based on file name
    yaml_content["chambre"] = int(yaml_file[-5])
    # Comparing length of both list. If not equal sys.exit
    if len(yaml_content["mois"]) != len(yaml_content["date_paiement"]):
        print(
            "Erreur dans fichier yaml.\nNombre valeur pour mois = {}\n"
            "Nombre valeur pour date_paiement = {}\nVeuillez un le meme "
            "nombre de valeur pour ces listes".format(
                str(len(yaml_content["mois"])),
                str(len(yaml_content["date_paiement"])),
            )
        )
        sys.exit()
    return yaml_content


def latex_to_pdf(latex_info, file_path):
    """
    With information contained in latex_dict, fill latex template to create
    the rent receipt in pdf format.

    Parameters
    ----------
    latex_info : dict
        Dictionary containing information for customized rent receipt
    file_path : str
        Relative path for saving the output rent receipt
    """
    env = make_env(loader=FileSystemLoader("."))
    tpl = env.get_template("used_files/template.tex")
    latex_file = tpl.render(**latex_info)
    pdf = build_pdf(latex_file, builder=None)
    pdf.save_to(file_path)
    print(f"Enregistrement {file_path} --> SUCCESS")


def processing_yaml(input_dict):
    """
    Process information in yaml_dict (which were extracted from yaml_file) into
    an output_dict with all requisite variable to fill latex file

    Parameters
    ----------
    input_dict : dict
        Dictionary containing yaml file content

    Returns
    -------
    output_dict : dict
        Dictionary containing information for customized rent receipt
    """
    # Initiate output dictionary
    output_dict = dict()
    # Fetch current iteration
    i = input_dict["iteration"]
    # Adding room number
    output_dict["chambre"] = str(input_dict["chambre"])
    # Adding month with customized elision and year
    output_dict["mois"] = de_elision(input_dict["mois"][i].capitalize())
    output_dict["annee"] = str(input_dict["annee"])
    # Adding tenant name with civility
    output_dict["locataire_entete"] = " ".join(input_dict["locataire"])
    output_dict["locataire_texte"] = convert_civility(input_dict["locataire"])
    # Adding signing date of rent receipt
    output_dict["date_signature"] = signed_day(
        input_dict["mois"][i], str(input_dict["annee"])
    )
    # Adding payment date of the rent by the tenant
    output_dict["date_paiement"] = receipt_day(input_dict)
    # Adding rent and rental charge amount
    # If no customized option we consider integer
    output_dict["montant_loyer"] = str(
        int(input_dict["loyer"]) - int(input_dict["charge"])
    )
    output_dict["montant_charge"] = str(int(input_dict["charge"]))
    output_dict["montant_total"] = str(int(input_dict["loyer"]))
    output_dict["montant_total_texte"] = (
        num2words(input_dict["loyer"], lang="fr") + " euros"
    )
    # Adding date of the rent
    output_dict["debut_periode"], output_dict["fin_periode"] = first_last_day(
        input_dict
    )
    # Adding absolute path to signature image
    cwd = os.getcwd()
    owner1 = "used_files/image/Signature_proprietaire1.jpg"
    owner2 = "used_files/image/Signature_proprietaire2.jpg"
    output_dict["signature_proprietaire1"] = os.path.join(cwd, owner1)
    output_dict["signature_proprietaire2"] = os.path.join(cwd, owner2)
    # Customized option if specified in yaml file
    if "customized" in input_dict.keys():
        output_dict = option_customized(output_dict, input_dict["customized"])
    return output_dict


def option_customized(output_dict, info):
    """
    Customized latex dictionary for a non full occupied month

    Parameters
    ----------
    output_dict : dict
        Dictionary containing information for customized rent receipt without
        date customisation in case of a non full occupied month.
    info : str
        String containing information about dates of non full occupied month.

    Returns
    -------
    output_dict : dict
        Dictionary containing information for customized rent receipt with
        date customisation in case of a non full occupied month.
    """
    begin, end, amount = info.split()
    # Computing ratio between rent and charges
    number_of_days = int(end[:2]) - int(begin[:2]) + 1
    total_of_days = monthrange(int("20" + end[-2:]), int(end[3:5]))[1]
    full_month_rent = int((total_of_days / number_of_days) * float(amount))
    ratio_charges = int(output_dict["montant_charge"]) / full_month_rent
    charges = round(ratio_charges * float(amount), 2)
    loyer = round(float(amount) - charges, 2)
    # Verifying format of input date
    begin = dateparser.parse(begin, languages=["fr"]).strftime("%d/%m/%Y")
    end = dateparser.parse(end, languages=["fr"]).strftime("%d/%m/%Y")
    # Replacing output_dict values
    day_payed = dateparser.parse(
        output_dict["date_paiement"], languages=["fr"]
    )
    day_signed = day_payed + datetime.timedelta(days=2)
    output_dict["date_signature"] = day_signed.strftime("%d/%m/%Y")
    # Adding rent and rental charge amount
    output_dict["montant_loyer"] = str(loyer).replace(".", ",")
    output_dict["montant_charge"] = str(charges).replace(".", ",")
    output_dict["montant_total"] = str(amount).replace(".", ",")
    # For amount in text format, determine before if it is a float
    if "," in output_dict["montant_total"]:
        euros = output_dict["montant_total"].split(",")[0]
        cents = output_dict["montant_total"].split(",")[1]
        # flake8: noqa: W503
        text = (
            num2words(euros, lang="fr")
            + " euros et "
            + num2words(cents, lang="fr")
            + " centimes"
        )
        output_dict["montant_total_texte"] = text
    else:
        output_dict["montant_total_texte"] = (
            num2words(amount, lang="fr") + " euros"
        )
    # Adding date of the rent
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
    begin_letter_list = (
        dateparser.parse(begin, languages=["fr"]).strftime("%d %B %Y").split()
    )
    end_letter_list = (
        dateparser.parse(end, languages=["fr"]).strftime("%d %B %Y").split()
    )
    # Capitalize month letter
    month_letter = dateparser.parse(end, languages=["fr"]).strftime("%B")
    month_letter_cap = month_letter.capitalize()
    begin_letter_list[1] = month_letter_cap
    end_letter_list[1] = month_letter_cap
    # Add to output dictionnary
    output_dict["debut_periode"] = " ".join(begin_letter_list)
    output_dict["fin_periode"] = " ".join(end_letter_list)
    return output_dict


def saving_path(yaml_dict):
    """
    Define name of rent receipt in pdf format.
    Format output file = YYYY_MM_locX_name_locataire.pdf where :
        YYYY = Year in 4 digits format
        MM = Month in 2 digits format
        X = Number of the room in the apartement

    Parameters
    ----------
    yaml_dict : dict
        Dictionary containing yaml file content.

    Returns
    -------
    file_path : str
        Relative path for saving the output rent receipt.
    """
    # Fetch current iteration
    i = yaml_dict["iteration"]
    # Format output file = YYYY_MM_locX_name_locataire.pdf
    month = dateparser.parse(yaml_dict["mois"][i]).strftime("%m")
    year = str(yaml_dict["annee"])
    name = "_".join(yaml_dict["locataire"][1:])
    num_loc = yaml_dict["chambre"]
    name_file = "{0}_{1}_loc{2}_{3}.pdf".format(
        year, month, str(num_loc), name
    )
    current_dir = os.getcwd()
    namedir = os.path.join(current_dir, "quittances_out")
    if not os.path.exists(namedir):
        os.makedirs(namedir)
    # Defining relative path of the output rent receipt
    file_path = os.path.join(namedir, name_file)
    return file_path


def signed_day(month, year):
    """
    Convert month and year of rent receipt in the format XX/XX/XX in order to
    define rent receipt signature which is always the 15th of the month.

    Parameters
    ----------
    month : str
        String containing month in letter of rent receipt
    year : str
        String containing year of rent receipt

    Returns
    -------
    date_formatted : str
        String of rent receipt signature in format "XX/XX/XX"
    """
    day = 15
    date_formatted = dateparser.parse(
        "{0} {1} {2}".format(str(day), month, year), languages=["fr"]
    ).strftime("%d/%m/%y")
    return date_formatted


def receipt_day(yaml_info):
    """
    Convert month and year of rent receipt in the format XX/XX/XX in order to
    define rent receipt payment day.

    Parameters
    ----------
    yaml_info : dict
        Dictionary containing yaml file content.

    Returns
    -------
    date_formatted : str
        String of rent receipt signature in format "XX/XX/XX"
    """
    day = yaml_info["date_paiement"][yaml_info["iteration"]]
    date_formatted = dateparser.parse(day, languages=["fr"]).strftime(
        "%d/%m/%Y"
    )
    return date_formatted


def first_last_day(yaml_info):
    """
    Deduce first and last day of the renting month based on calendar library
    given month and year of the renting period.

    Parameters
    ----------
    yaml_info : dict
        Dictionary containing yaml file content.

    Returns
    -------
    first : str
        First day of renting period in format dd MMMM yyyy
    last : str
        Last day of renting period in format dd MMMM yyyy
    """
    # Fetch current iteration
    i = yaml_info["iteration"]
    # Deducing month number based on a string
    number_month = dateparser.parse(yaml_info["mois"][i]).month
    # Determining number of days of this month given the year
    number_last = monthrange(yaml_info["annee"], number_month)[1]
    # Define output variables
    first = "1er {0} {1}".format(yaml_info["mois"][i], str(yaml_info["annee"]))
    last = "{0} {1} {2}".format(
        str(number_last), yaml_info["mois"][i], str(yaml_info["annee"])
    )
    return first, last


def convert_civility(person):
    """
    Convert civility acronym into civility full word

    Parameters
    ----------
    person : str
        Acronym for civility contained in yaml file

    Returns
    -------
    full_civility : str
        Sentence containing civility and name without acronym.
    """
    # Uncomment this line when using for single rent receipt
    # person = person.split()
    title = person[0].lower()
    name = " ".join(person[1:])
    dict_title = {
        "mr": "Monsieur",
        "mme": "Madame",
        "mlle": "Mademoiselle",
    }
    full_civility = "{0} {1}".format(dict_title[title], name)
    return full_civility


def de_elision(word):
    """
    Prepend word with "d'" or "de" according to first letter

    Parameters
    ----------
    word : str
        Word which will be added the preposition "de" or "d'"

    Returns
    -------
    word_prep : str
        Word with the right preposition ("de" or "d'")
    """
    if word[0].lower() in ("a", "e", "o", "u", "y"):
        word_prep = "d'" + word
    else:
        word_prep = "de " + word
    return word_prep


def save_rent_receipt(input_dict):
    """
    Main function of this program. Based on an input dict with minimal
    information create rent receipt in pdf format.

    Parameters
    ----------
    input_dict : dict
        Dictionary containing necessary information to establish rent receipt.

    Returns
    -------
    None
    """
    for number, mois in enumerate(input_dict["mois"]):
        input_dict["iteration"] = number
        # Fetch information for latex variables
        latex_dict = processing_yaml(input_dict)
        # Definition of saving file and folder
        output_path = saving_path(input_dict)
        # Latex to PDF processing
        latex_to_pdf(latex_dict, output_path)


if __name__ == "__main__":
    # Choose yaml file to read
    file_yaml = "used_files/quittance_chambre1.yml"
    # Reading input data with yaml_format
    yaml_dict = read_yaml(file_yaml)
    # Creating rent receipt based on yaml dictionary
    save_rent_receipt(yaml_dict)
