import pandas as pd
from Bio import Entrez
import json
import argparse
import sys
import re

def getMeSHHeadingList(pm):
    pm = [field for field in pm.split("/") if field][-1].split("?term=")[-1]
    handle = Entrez.efetch(db="PubMed", id=pm, retmode='xml', api_key=api_key)
    record = Entrez.read(handle)
    MeSH_list = record['PubmedArticle'][0]
    for key in ['MedlineCitation', 'MeshHeadingList']:
        MeSH_list = MeSH_list.get(key)
        if MeSH_list is None:
            return None
    MeSHs = []
    for heading in MeSH_list:
        desc = str(heading['DescriptorName'])
        MeSHs += [desc]
    return MeSHs

def getTreeNum(term):
    term_id = json.loads("".join(Entrez.esearch(db="MeSH", term=term+"[MeSH Terms]", retmode="json", api_key=api_key)\
                                 .readlines()))['esearchresult']['idlist']
    s = "".join(Entrez.efetch(db="MeSH", id=term_id, api_key=api_key).readlines())
    if len(term_id) != 0:
        tree_num = re.search(r'Tree Number\(s\): (.*?)\n', s).group(1)
        return tree_num
    else:
        return None

def getDiseaseTerms(head_list):
    if head_list is None:
        return []
    tree_list = [(getTreeNum(term), term) for term in head_list]
    result = []
    for ind, pair in enumerate(tree_list):
        if any([x.strip()[0] == 'C' for x in pair[0].split(',')]):
            result += [pair[1]]
    return result

def getStdNameAndUnkCUIFromMeSHList(mesh_list):
    if mesh_list == None:
        return ([],[])
    known_std = []
    unk_cui = []
    for mesh in mesh_list:
        cui = mesh_cui_map.get(mesh)
        std = cont_vocab_map.get(cui)
        if std:
            known_std += [std]
        else:
            unk_cui += [cui]
    return (known_std, unk_cui)

def getUniqueDiseaseTerms(head_list, keep_nested = False):
    if head_list is None:
        return []
    tree_list = [(getTreeNum(term), term) for term in head_list]
    diseases = []
    for ind, pair in enumerate(tree_list):
        if any([x.strip()[0] == 'C' for x in pair[0].split(',')]):
            diseases += [pair]
    if keep_nested:
        return [pair[1] for pair in diseases]
    result = []
    for ind, pair in enumerate(diseases):
        redund = False
        for alt_pair in [x for i, x in enumerate(diseases) if i != ind]:
            if any([any([sup.strip().startswith(sub.strip()) for sup in alt_pair[0].split(',')]) for sub in pair[0].split(',')]):
                redund = True
                break
        if not redund:
            result += [pair[1]]
    return result

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("data_path", help="location for file containing manifest data. Assumed to be in CSV \
		form with a header row.")
	parser.add_argument("output_path", help="location for output file, will be a CSV with a header row. It will be \
		identical to the input CSV, with an added column containing a String for each row/publication, with the String \
		containing semicolon-separated (if there is more than one) disease annotations. The column will be named either \
		'Disease' or the value of the -output_column option.")
	parser.add_argument("cont_vocab_path", help="location for controlled vocabulary file. It is required to have \
		a column 'UMLS_CUI' containing Concept Unique IDs (from the Unified Medical Language System metathesaurus) \
		and a column 'standard_name' containing a standard term to annotate the input table with if a publication \
		is mapped to the corresponding CUI")
	parser.add_argument("-i", "-input_column", type=str, help="column name containing PubMed IDs (for example, '31442407') of the query articles. \
		Can also contain links to PubMed articles (for example, 'https://www.ncbi.nlm.nih.gov/pubmed/31442407', as the script will extract the PubMed ID from the URL. Will default to 'PubMed'")	
	parser.add_argument("-o", "-output_column", type=str, help="column name for the disease annotation. Will be a \
		semicolon-separated string containing disease annotation(s) for each row/publication. Will default to 'Disease'")
	parser.add_argument("-m", "-meshtocui_map_path", type=str, help="relative path of CSV with two columns, one containing \
		possible MeSH terms in a column called 'STR', and their corresponding Concept Unique IDs (according to UMLS \
		metathesaurus) in a column called 'CUI'. Will default to '../data/mesh_cui_map_total.csv'")
	parser.add_argument("-c", "-cuitoterms_map_path", type=str, help="relative path of CSV with (at least) two columns, \
		one containing Concept Unique IDs (CUIs) we may encounter in a column called 'CUI', one containing possible \
		terms for our controlled vocabulary in a columns called 'term'. Any additional columns or structure can be \
		added include information  which will be output in the case that there are CUIs which do not have standard \
		names in our controlled  vocabulary. This CSV will be filtered for those CUIs and output to the location of \
		the option 'needed_cuis'. The default for '-cuitoterms_map' is '../data/concept_map.csv', and it contains \
		columns for 'pref_name', or the most preferred name for a CUI (according to UMLS), 'edit_score' or the edit \
		score between a possible term and the pref_name, 'ont_source' which tells the ontology providing the term to \
		be considered. The terms have been filtered for those in ICD10CM and NCI thesaurus ontologies, and ordered by\
		edit score from the most preferred term")
	parser.add_argument("-n", "-needed_cuis", type=str, help="relative path for possible output, if there are Concept \
		Unique IDs without a standard name in the controlled vocabulary. Defaults to 'needed_cuis.csv'")
	parser.add_argument("-a", "-api_key", type=str, help="API key for Entrez. Increases the rate limit from 3 requests \
		per second of the E-utilities (used to retrieve PubMed data) to 10 requests per second. Users can obtain an API \
		key from the settings page of an NCBI account at https://www.ncbi.nlm.nih.gov/account/settings/")
	parser.add_argument("-e", "-email", type=str, help="Email of individual running script, to be passed to Entrez in \
		order to access E-utilities. Will be  used if NCBI observes requests that violate their policies. Will give \
		a warning if omitted, and an IP address can be blocked by NCBI if a violating request is made without an email \
		address included")
	#parser.add_argument("-k", "-keep_nested", type=bool, help="Whether or not to keep less specific nested mesh terms \
	#	(i.e. one being a more specific term for another, such as 'Cancer' and 'Breast Cancer'. Default is to remove")
	args = parser.parse_args()
	pub_data = pd.read_csv(args.data_path)
	if args.i is None:
		args.i = "PubMed"
	if args.o is None:
		args.o = "Disease"
	if args.m is None:
		args.m = "../data/mesh_cui_map_total.csv"
	if args.c is None:
		args.c = "../data/concept_map.csv"
	if args.n is None:
		args.n = "needed_cuis.csv"
	if args.e is not None:
		Entrez.email = args.e
	if args.e is not None:
		api_key = args.a
	else:
		api_key = None
	cont_vocab_df = pd.read_csv(args.cont_vocab_path)
	print(cont_vocab_df.head())
	cont_vocab_map = dict(zip(cont_vocab_df.UMLS_CUI, cont_vocab_df.standard_name))
	del cont_vocab_df

	mesh_cui_df = pd.read_csv(args.m)
	print(mesh_cui_df.head())
	mesh_cui_map = dict(zip(mesh_cui_df.STR, mesh_cui_df.CUI))
	del mesh_cui_df

	cui_pref_terms_df = pd.read_csv(args.c)
	print(cui_pref_terms_df.head())
	mesh_series = pub_data[args.i].apply(lambda x: [field for field in x.split("/") if field][-1].split("?term=")[-1])\
		.apply(getMeSHHeadingList)
	disease_series = mesh_series.apply(getUniqueDiseaseTerms)
	translated = disease_series.apply(getStdNameAndUnkCUIFromMeSHList).apply(pd.Series)
	known_std = translated[0]
	unk_cui = set(translated[1].sum())
	if len(unk_cui) > 0:
		print("There are MeSH terms corresponding to Concept Unique IDs (CUIs) which do not \
have defined standard names in your controlled vocabulary. They are the following \
(with a possible term for that CUI aside): ")
		pd.set_option('display.max_rows', None)
		print(cui_pref_terms_df[cui_pref_terms_df['CUI'].apply(lambda x: x in unk_cui)]\
			[['CUI', 'term']].drop_duplicates(subset='CUI').to_string(index=False))
		pd.set_option('display.max_rows', 10)

		affirmatives = ["y", "Y"]
		negatives = ["", "n", "N"]
		go_on = "Q"
		while go_on not in affirmatives + negatives:
			go_on = input("Should we ignore these unknown CUIs and continue? (y/N)")

		if go_on in negatives:
			print("Please add these CUIs to " + args.cont_vocab_path)
			cui_pref_terms_df[cui_pref_terms_df['CUI'].apply(lambda x: x in unk_cui)].to_csv(args.n, index=False)
			print("Writing the table of possible terms to " + args.n)
			exit()
	pub_data[args.o] = known_std.apply(lambda x: ";".join([anno for anno in x if not (len(x) > 1 and anno == 'Not Specified')]))
	pub_data.to_csv(args.output_path, index=False)


