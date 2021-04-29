import synapseclient
from synapseclient import Table, Schema

def main():
    # login to synapse
    syn=synapseclient.login(silent=True)

    # synapse table id for publications - merged
    table_id = "syn21868591"

    # synapse expect column names in double quotes
    column = "tumorType"

    # filter the rows that contain incorrect annotations
    # "" (empty strings)
    # "Unspecified"
    annotations = "Unspecified"

    # Put together a query using f strings
    # A type of query you can plug and chug
    query = (f"SELECT publicationId, pubMedId, tumorType FROM {table_id} "
                f"WHERE (({column} HAS ('{annotations}')))")

    # query the table with tableQuery() and convert the
    # results into a data frame. If the query is correct,
    # we should get 529 rows back.
    publication_view = syn.tableQuery(query).asDataFrame()
    publication_view['tumorType'] = "Leukemia, unspecified"
    
    
    # store row changes in Synapse
    syn.store(Table(table_id, publication_view))

    # If you uncomment the line above and requery the table, we should
    # now get back 0 rows
    publication_view2 = syn.tableQuery(query).asDataFrame()
    print(f"Number of results: {len(publication_view2)}")

if __name__ == "__main__":
    main()