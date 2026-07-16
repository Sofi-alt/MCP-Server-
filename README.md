# MCP Server (Currently works only on CKAN, version 1)

A simple MCP integration for querying CKAN-based open data portals (e.g. open.canada.ca, data.gov.uk, data.qld.gov.au), further be adjusted to also integrate DKAN, OpenDataSoft, Socrata.

## Tools (currently for CKAN)

### ckan_find_portal
Find a CKAN portal matching a topic or country.
- **query** (string) — search term, e.g. `"Canada open data"`

### ckan_portal_status
Check whether a CKAN portal is reachable.
- **portal_url** (string) — base URL of the portal

### ckan_package_search
Search for datasets on a portal.
- **portal_url** (string) — base URL of the portal
- **query** (string) — search term, e.g. `"weather"`
- **rows** (integer, optional, default 10) — number of results
- **start** (integer, optional, default 0) — pagination offset

### ckan_package_show
Get full details for a specific dataset.
- **dataset_id** (string) — dataset UUID or name
- **portal_url** (string) — base URL of the portal

### ckan_datastore_search
Query rows from a dataset's datastore resource (structured tabular data).
- **portal_url** (string) — base URL of the portal
- **resource_id** (string) — UUID of the datastore resource
- **q** (string, optional) — full-text search across all fields
- **filters** (object, optional) — exact-match filters, e.g. `{"country": "AT"}`
- **fields** (array, optional) — limit to specific columns
- **limit** (integer, optional, default 20, max 500) — rows to return
- **offset** (integer, optional, default 0) — pagination offset

## Typical workflow

1. ckan_find_portal — locate the right portal/s for the queried topic/country
2. ckan_package_search — search that portal for relevant datasets
3. ckan_package_show — inspect a dataset to find its resource IDs
4. ckan_datastore_search — pull actual rows of data from a resource

## Notes

- will also add the tool for metadata enrichment later one with custom module possibly as currently does not really makes sense with current module done
- mcp server (with current ckan implementation) fully works when added by developer settings in claude directly to the claude_desktop_config.json
- without Claude desktop version possible to use MCP Inspector v0.22.0 and connect to the server locally to test it
- possibly will be enlarged to also DKAN, OpenDataSoft, Socrata with inclusion of them via either separate functions based on the API..
