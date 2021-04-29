# Preliminaries
import pandas as pd
import argparse
import synapseclient
from synapseclient import Project, File, Folder
from synapseclient import Schema, Column, Table, build_table, Row, RowSet, as_table_columns
from pathlib import Path

def main():

    # Login to  Synapse
    syn = synapseclient.Synapse()
    syn.login()

    # Get Arguments - Synapse table id and file path
    parser = argparse.ArgumentParser(
        description='Get synapse table id and file path')
    parser.add_argument('table_id', type=str , help='Synapse Table id')
    parser.add_argument('path', type=Path, help='Path to file')
    
    args = parser.parse_args()
    
    table_id = args.table_id
    path = args.path  
    
    # Append terms to table
    # Make sure csv file does not have empty rows
    # Otherwise the empty rows will append as well
    table = syn.store(Table(table_id, f"{path}"))

    print("New terms appended to Master List in Synapse")

if __name__ == "__main__":
    main()