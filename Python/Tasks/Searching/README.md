# Searching for Entities
The search snippets outline searching for entities in the system. Searching for entities uses the same mapped JSON data [specification](https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification-JSON-CSV-Mapping) as API calls such as addRecord to format the search request.

There are [considerations](https://senzing.zendesk.com/hc/en-us/articles/360007880814-Guidelines-for-Successful-Entity-Searching) to be aware of when searching.

## Snippets
* **Search5kFutures.py**
    * Read and search for records from a file using multiple threads
    * To see results first load records with [Add10KFutures.py](../Loading/Add10KFutures.py)
* **SearchRecords.py**
    * Basic iteration over a few records, searching for each one
    * To see results first load records with [AddTruthSetLoop.py](../Loading/AddTruthsetLoop.py)

