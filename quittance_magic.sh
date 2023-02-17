#!/bin/bash

# Instructions:
# using it with command: 
# sh quittance_magic.sh
# 1) Script must be into automatic_rent_receipt which is a clone of the git hub repo
# 2) csv file must be named input_file.csv and be located in quittances-auto-last-manual/
# 3) csv file must be extract from xls file where all data has been convert to string before except column date which must stay in date format

echo Transfert des fichiers non-anonymisé...
mkdir temp
mv template.tex temp
mv image temp
mv year2022.csv temp
cp -rf /home/recount/Documents/quittances-auto-last-manual/image .
cp -f /home/recount/Documents/quittances-auto-last-manual/template.tex .
cp -f /home/recount/Documents/quittances-auto-last-manual/input_file.csv .

echo Execution du script...
python pipeline_account_statement.py

echo Anonymisation du dossier
rm -rf image
rm -rf template.tex
mv -f temp/* .
rmdir temp

echo Fin du script
