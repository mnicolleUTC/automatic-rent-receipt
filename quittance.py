#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 21:11:51 2022

@author: nicollemathieu
"""

from jinja2.loaders import FileSystemLoader
from latex.jinja2 import make_env
from latex import build_pdf
import os
import sys
import yaml
import dateparser
import locale
import datetime
from num2words import num2words
from calendar import monthrange

def read_yaml(yamlfile):
    """Read yaml file and return a dict"""
    #Opening and fetching content
    with open(yamlfile, encoding="utf-8") as stream:
        yaml_dict = yaml.safe_load(stream)
    #Converting dict key month and tenant into list
    yaml_dict['mois'] = yaml_dict['mois'].split()
    yaml_dict['date_paiement'] = yaml_dict['date_paiement'].split()
    #Comparing length of both list. If not equal sys.exit
    if len(yaml_dict['mois']) != len(yaml_dict['date_paiement']):
        print("Erreur dans fichier yaml.\nNombre valeur pour mois = {}\n"\
              "Nombre valeur pour date_paiement = {}\nVeuillez un le meme "\
              "nombre de valeur pour ces listes"\
              .format(str(len(yaml_dict['mois'])),\
                      str(len(yaml_dict['date_paiement']))))
        sys.exit()
    return yaml_dict
        
def latex_to_pdf(latex_dict,file_path):
    """Convert the template.tex to a pdf file with filled value 
    given in latex_dict"""
    env = make_env(loader=FileSystemLoader('.'))
    tpl = env.get_template('template.tex')
    latex_file = tpl.render(**latex_dict)
    pdf = build_pdf(latex_file,builder = None)
    pdf.save_to(file_path)
    print(f"Enregistrement {file_path} --> SUCCESS")
    
def processing_yaml(input_dict):
    """Process information in yaml dict into an output_dict with all the
    variable to fill latex file"""
    #Initiation du dictionnaire
    output_dict = dict()
    #Recuperation de l'itération en cours
    i = input_dict['iteration']
    #Ajout du mois avec personnalisation de la préposition de ou d'
    output_dict["mois"] = de_elision(input_dict["mois"][i].capitalize())
    #Ajout du nom du locataire au format Mr et Monsieur
    output_dict["locataire_entete"] = input_dict["locataire"]
    output_dict["locataire_texte"] = convert_civility(input_dict["locataire"])
    #Ajout date signature document (au 15 du mois de la quittance)
    output_dict["date_signature"] = signed_day(input_dict["mois"][i],\
                                             str(input_dict["annee"]))
    #Ajout date paiement du loyer, récupérer directement du yaml
    output_dict["date_paiement"] = receipt_day(input_dict)  
    #Ajout montant loyer, provision et différence
    output_dict["montant_loyer"] = str(input_dict['loyer'] - 
                                       input_dict['charge'])
    output_dict["montant_charge"] = str(input_dict['charge'])
    output_dict["montant_total"] = str(input_dict['loyer'])
    output_dict["montant_total_texte"] = num2words(input_dict['loyer'],\
                                                   lang='fr')
    #Ajout date début et fin de période au format Texte
    output_dict["debut_periode"],output_dict["fin_periode"] = first_last_day(\
                                                              yaml_dict)
    #Ajout des liens absolu vers les signatures
    cwd = os.getcwd()
    proprietaire1 = 'image/Signature_proprietaire1.jpg'
    proprietaire2 = 'image/Signature_proprietaire2.jpg'
    output_dict["signature_proprietaire1"] = os.path.join(cwd,proprietaire1)
    output_dict["signature_proprietaire2"] = os.path.join(cwd,proprietaire2)
    #Verification de l'option customized pour quittances au prorata
    if "customized" in input_dict.keys():
        output_dict = option_customized(output_dict,yaml_dict["customized"])
    #Fin des ajouts nécéssaires au latex fin de focntion 
    return output_dict

def option_customized(output_dict,info):
    """Establish receipt for a non full occupied month"""
    begin, end, amount = info.split()
    #Verifing format
    begin = dateparser.parse(begin,languages=['fr']).strftime("%d/%m/%Y")
    end = dateparser.parse(end,languages=['fr']).strftime("%d/%m/%Y")
    #Computing corresponding charges
    ratio = round(float(amount),2)/int(output_dict["montant_total"])
    loyer = round(ratio * int(output_dict["montant_loyer"]),2)
    charges = round(round(float(amount),2) - loyer,2)
    #Replacing output_dict values
    day_payed = dateparser.parse(output_dict["date_paiement"],languages=['fr'])
    day_signed = day_payed + datetime.timedelta(days=2)
    output_dict["date_signature"] = day_signed.strftime("%d/%m/%Y")
    #Ajout montant loyer, provision et différence
    output_dict["montant_loyer"] = str(loyer).replace(".",",")
    output_dict["montant_charge"] = str(charges).replace(".",",")
    output_dict["montant_total"] = str(amount).replace(".",",")
    output_dict["montant_total_texte"] = num2words(amount,lang='fr')
    #Ajout date début et fin de période au format Texte
    output_dict["debut_periode"] = dateparser.parse(begin).strftime("%d %B %Y")
    output_dict["fin_periode"] = dateparser.parse(begin).strftime("%d %B %Y")
    return output_dict
    
def saving_path(yalm_dict,num_loc):
    """Prepare the saving path of pdf file"""
    #Recuperation de l'itération en cours
    i = yaml_dict['iteration']
    #Format output file = YYYY_MM_locX_name_locataire.pdf
    month = dateparser.parse(yaml_dict["mois"][i]).strftime('%m')
    year = str(yalm_dict["annee"])
    name = "_".join(yaml_dict["locataire"].split()[1:])
    name_file = "{0}_{1}_loc{2}_{3}.pdf".format(year,month,str(num_loc),name)
    namedir = "quittances_out"
    if not os.path.exists(namedir):
        os.makedirs(namedir)
    #Création du lien d'enregistrement
    file_path = os.path.join(namedir, name_file)
    return file_path

def signed_day(month,year):
    """Convert month and year of the receipt in the format day XX/XX/XX""" 
    day = 15
    return dateparser.parse("{0} {1} {2}".format(str(day),month,year),\
                            languages=['fr']).strftime("%d/%m/%y")
                                         
def receipt_day(yaml_dict):
    """Verify and convert if neeeded the format of receipt day in yaml file"""
    day = yaml_dict["date_paiement"][yaml_dict['iteration']]
    return dateparser.parse(day,languages=['fr']).strftime("%d/%m/%Y")

                                
def first_last_day(yaml_dict):
    """Infer the first and last day of the renting month"""
    #Recuperation de l'itération en cours
    i = yaml_dict['iteration']
    #Deducing the number of the month ase on a string
    number_month = dateparser.parse(yaml_dict["mois"][i]).month
    #Determining the number of days of this month given the year
    number_last = monthrange(yaml_dict["annee"],number_month)[1]
    #Creation of output variable
    first = "1er {0} {1}".format(yaml_dict["mois"][i],str(yaml_dict["annee"]))
    last = "{0} {1} {2}".format(str(number_last),yaml_dict["mois"][i],\
                                str(yaml_dict["annee"]))
    return first,last
    
def convert_civility(person):
    """Convert Mr or Mme or Mlle into Monsieur, Madame ou Mademoiselle"""
    title = person.split()[0].lower()
    name = " ".join(person.split()[1:])
    dict_title = {
        "mr":"Monsieur",
        "mme":"Madame",
        "mlle":"Mademoiselle",
        }
    output = "{0} {1}".format(dict_title[title],name)
    return output
    
def de_elision(word):
    """Prepend word with "d'" or "de" according to first letter"""
    if word[0].lower() in ('a', 'e', 'o', 'u', 'y'):
        return "d'" + word
    else:
        return "de " + word

if __name__ == '__main__':
    #Configuration of locale language
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
    #Choose yaml file to read
    file_yaml = "quittance_chambre1.yml"
    #Line to use builder latexmk
    os.environ["PATH"]=os.environ["PATH"]+":/Library/TeX/texbin"
    #Reading input data with yaml_format
    yaml_dict = read_yaml(file_yaml)
    for i, mois in enumerate(yaml_dict["mois"]):
        yaml_dict['iteration'] = i
        #Extrapoling informations for latex variables
        latex_dict = processing_yaml(yaml_dict)
        #Definition of saving file and folder 
        #int(file_yaml[-5]) correspond au numéro de chambre
        output_path = saving_path(yaml_dict,int(file_yaml[-5]))
        #Latex to PDF processing
        latex_to_pdf(latex_dict,output_path)
    
