import synapseclient
from synapseclient import Table, Schema
import argparse


def main():
    # login to synapse
    syn = synapseclient.login(silent=True)

    # Get arguments for table id, column, old annotation, new annotation
    parser = argparse.ArgumentParser(
        description='Get synapse table id, column, old annotaiton, and new annotation')
    parser.add_argument('table_id', type=str , help='Synapse Table id')
    parser.add_argument('column', type=str, help='Name of column to reference')
    parser.add_argument('old_annotation', type=str, help='Old annotation to change')
    parser.add_argument('new_annotation', type=str, help="New annotation to change old annotation to")
    
    args = parser.parse_args()
    
    table_id = args.table_id
    column = args.column
    old_annotation = args.old_annotation
    new_annotation = args.new_annotation 


    # Put together a query using f strings
    # A type of query you can plug and chug
    query = (f"SELECT publicationId, pubMedId, {column} FROM {table_id} "
             f"WHERE (({column} HAS ('{old_annotation}')))")

    # query the table with tableQuery() and convert the
    # results into a data frame. If the query is correct,
    # we should get 529 rows back.
    publication_view = syn.tableQuery(query).asDataFrame()
    print(f"Number of results: {len(publication_view)}")
    print(publication_view)
    
    # change old annotation to new annotation
    for i, row in publication_view.iterrows():
        annots = row[column]
        new_annots = [new_annotation if x ==
                      old_annotation else x for x in annots]
        publication_view.at[i, column] = new_annots
    print(publication_view)

    # store row changes in Synapse. Uncomment below when ready to change!
    #syn.store(Table(table_id, publication_view))

    # If you uncomment the line above and requery the table, we should
    # now get back 0 rows
    publication_view2 = syn.tableQuery(query).asDataFrame()
    print(f"Number of results: {len(publication_view2)}")


if __name__ == "__main__":
    main()
