"""
CKAN MCP Server, basic prototype i did some time ago
exposes several tools for querying CKAN open-data portals.
Run with:  fastmcp run server.py (on my macbook)
based on the following documentation i used: https://modelcontextprotocol.io/docs/develop/build-server
"""

import httpx
from fastmcp import FastMCP
import json
# from enrich import enrich as _enrich_dataset -> not sure will exclude for now

mcp = FastMCP("ckan-mcp")

_DEFAULT_TIMEOUT = 15


def _base(portal_url: str) -> str:
    return portal_url.rstrip("/") + "/api/3/action"


async def _get(url: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, follow_redirects=True) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def ckan_portal_status(portal_url: str) -> dict:
    #to check whether a CKAN portal is reachable and return its dataset count.

    data = await _get(f"{_base(portal_url)}/package_search", {"rows": 0})
    count = data["result"]["count"]
    return {"status": "ok", "portal": portal_url, "dataset_count": count}


@mcp.tool()
async def ckan_package_search(portal_url: str ,query: str ,rows: int = 10 , start: int = 0) -> dict:
    #to search datasets on a CKAN portal by keyword, as argument also include rows eg number of results to return (max 1000).

    rows = min(rows, 1000)
    data = await _get(
        f"{_base(portal_url)}/package_search",
        {"q": query, "rows": rows, "start": start}
    )
    result = data["result"]
    return {
        "total": result["count"],
        "returned": len(result["results"]),
        "datasets": [
            {"id": d["id"],
                "name": d["name"],
                "title": d.get("title", ""),
                "notes": (d.get("notes") or "")[:300],
                "num_resources": d.get("num_resources", 0),
                "tags": [t["name"] for t in d.get("tags", [])]}
            for d in result["results"]] }


@mcp.tool()
async def ckan_package_show(portal_url: str, dataset_id: str) -> dict:
    #to retrieve full metadata for a specific dataset, possibly automatically enriched.
    import asyncio
    # Run enrichment in executor (sync), returns raw + enriched in one call
    #loop = asyncio.get_event_loop()
    #try:
    #    enriched = await loop.run_in_executor(
    #       None, _enrich_dataset, portal_url, dataset_id, False
    #    )
    #except Exception:
     #   enriched = {}

    data = await _get(f"{_base(portal_url)}/package_show", {"id": dataset_id})
    d = data["result"]

    return {
        "id": d["id"],
        "name": d["name"],
        "title": d.get("title", ""),
        "notes": d.get("notes", ""),
        "license": d.get("license_title", ""),
        "organization": (d.get("organization") or {}).get("title", ""),
        "metadata_created": d.get("metadata_created", ""),
        "metadata_modified": d.get("metadata_modified", ""),
        "tags": [t["name"] for t in d.get("tags", [])],
        "resources": [
            {
                "id": r["id"],
                "name": r.get("name", ""),
                "format": r.get("format", ""),
                "url": r.get("url", ""),
                "datastore_active": r.get("datastore_active", False)}
            for r in d.get("resources", [])
        ],
        # Enrichment fields, automatically added
        #"quality": enriched.get("quality"),
        #"columns": enriched.get("columns", []),
        #"summary": enriched.get("summary", ""),
        #"cached": enriched.get("cached", False),
    }


@mcp.tool()
async def ckan_datastore_info(portal_url: str, resource_id: str) -> dict:
    # schema information (column names and types) for a datastore resource.

    data = await _get(
        f"{_base(portal_url)}/datastore_info", {"id": resource_id}
    )
    info = data["result"]
    return {
        "resource_id": resource_id,
        "total_records": info.get("meta", {}).get("count", None),
        "fields": [
            {"id": f["id"], "type": f.get("type", "unknown")}
            for f in info.get("fields", [])
            if f["id"] != "_id"
        ],
    }


@mcp.tool()
async def ckan_datastore_search(portal_url: str, resource_id: str, filters: dict | None = None, q: str | None = None, limit: int = 20, offset: int = 0, fields: list[str] | None = None ) -> dict:
    """to query rows from a CKAN datastore resource.

    Args (based on the anthropic methodology how to document tools):
        portal_url: Base URL of the CKAN portal.
        resource_id: UUID of the datastore resource.
        filters: Dict of exact-match column filters, e.g. {"country": "AT"}.
        q: Full-text search string across all fields.
        limit: Number of rows to return (max 500).
        offset: Row offset for pagination.
        fields: List of column names to include (None = all columns).
    """
    limit = min(limit, 500)
    params: dict = {"resource_id": resource_id, "limit": limit, "offset": offset}
    if filters:
        params["filters"] = json.dumps(filters)
    if q:
        params["q"] = q
    if fields:
        params["fields"] = ",".join(fields)

    data = await _get(f"{_base(portal_url)}/datastore_search", params)
    result = data["result"]
    return {
        "total": result.get("total", None),
        "returned": len(result["records"]),
        "records": result["records"]}


#@mcp.tool()
#async def ckan_enrich_metadata( portal_url: str, dataset_id: str, force: bool = False) -> dict:
    # to enrich a dataset's metadata with quality scoring and column profiles, based on my custom module but idk,
    # also adds summaries that based on research improve findability of the relevant data, results in the metadata_index.json localy

    #import asyncio
    #loop = asyncio.get_event_loop()
    #return await loop.run_in_executor(None, _enrich_dataset, portal_url, dataset_id, force)


# some CKAN portals 
_KNOWN_PORTALS = [
    {"url": "https://open.canada.ca/data",      "country": "Canada",         "tags": ["canada", "government"]},
    {"url": "https://data.gov.uk",               "country": "UK",             "tags": ["uk", "britain", "government"]},
    {"url": "https://data.gov",                  "country": "USA",            "tags": ["usa", "america", "us", "government"]},
    {"url": "https://data.europa.eu/data",       "country": "EU",             "tags": ["europe", "eu", "european"]},
    {"url": "https://www.data.qld.gov.au",       "country": "Australia",      "tags": ["australia", "queensland"]},
    {"url": "https://data.humdata.org",          "country": "Global",         "tags": ["humanitarian", "hdx", "global"]},
    {"url": "https://open.africa",               "country": "Africa",         "tags": ["africa"]},
    {"url": "https://data.london.gov.uk",        "country": "UK",             "tags": ["london", "uk"]},
    {"url": "https://data.gov.ie",               "country": "Ireland",        "tags": ["ireland"]},
    {"url": "https://data.overheid.nl",          "country": "Netherlands",    "tags": ["netherlands", "dutch", "holland"]}
]


@mcp.tool()
async def ckan_find_portal(query: str) -> dict:
    # to find relevant CKAN portals for a given topic or country query.
    import asyncio

    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Score each portal by keyword match
    scored = []
    for p in _KNOWN_PORTALS:
        score = sum(1 for tag in p["tags"] if tag in query_lower)
        score += 1 if p["country"].lower() in query_lower else 0
        scored.append((score, p))

    # Sort, to try portals with any match first, then all others
    scored.sort(key=lambda x: -x[0])

    # Check top portals (up to 5) concurrently
    candidates = [p for _, p in scored[:5]]

    async def check(portal):
        try:
            data = await _get(
                f"{_base(portal['url'])}/package_search",
                {"q": query, "rows": 0})
            count = data["result"]["count"]
            return {
                "url": portal["url"],
                "country": portal["country"],
                "dataset_count": count,
                "relevant_datasets": count,
                "reachable": True}
        except Exception:
            return {"url": portal["url"], "country": portal["country"], "reachable": False}

    results = await asyncio.gather(*[check(p) for p in candidates])
    reachable = [r for r in results if r["reachable"]]
    reachable.sort(key=lambda x: -x["relevant_datasets"])

    return {
        "query": query,
        "portals_checked": len(candidates),
        "portals_found": len(reachable),
        "portals": reachable,
        "suggested": reachable[0]["url"] if reachable else None,
    }


if __name__ == "__main__":
    mcp.run()
