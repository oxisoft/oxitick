#!/usr/bin/env python3
"""Minimal OxiTick API client.

Create a token in the app first: Settings -> Security -> App tokens.

    OXITICK_SERVER_URL=https://oxitick.example.com \
    OXITICK_TOKEN=oxt_... \
    python3 python_example.py

For an AI assistant, use the MCP server instead of writing this yourself:
https://github.com/oxisoft/oxitick-mcp
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SERVER = os.environ.get("OXITICK_SERVER_URL", "").rstrip("/")
TOKEN = os.environ.get("OXITICK_TOKEN", "")

if not SERVER or not TOKEN:
    sys.exit("Set OXITICK_SERVER_URL and OXITICK_TOKEN.")


def call(method, path, params=None, body=None):
    url = f"{SERVER}/api/v1/personal{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    # The header, and only the header. A token in a query string is written to
    # the server's access log and to every proxy in front of it.
    request.add_header("Authorization", f"Bearer {TOKEN}")
    if data:
        request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        # The codes worth branching on. See docs/authentication.md.
        if error.code == 401:
            sys.exit("Token invalid or revoked. Create a new one in the app.")
        if error.code == 403:
            sys.exit(f"This token lacks the scope for that: {detail}")
        if error.code == 429:
            wait = error.headers.get("Retry-After", "a few")
            sys.exit(f"Rate limited. Wait {wait} seconds.")
        if error.code == 503:
            sys.exit("App tokens are switched off on this server by its administrator.")
        if error.code == 404:
            # Deliberately ambiguous: does not exist, is not yours, was deleted,
            # or sits in a list hidden from the API. Do not try to tell them apart.
            sys.exit("Not found.")
        raise


lists = call("GET", "/lists")["lists"]
print(f"{len(lists)} list(s):")
for todo_list in lists:
    print(f"  {todo_list['title']:30} {todo_list['open_tasks']} open")

overdue = call("GET", "/items", {"overdue": "true", "limit": 10})
print(f"\n{overdue['total']} overdue, showing {len(overdue['items'])}:")
for task in overdue["items"]:
    print(f"  {task['due_at'][:10]}  {task['title']}")

if not lists:
    sys.exit(0)

created = call(
    "POST",
    f"/lists/{lists[0]['id']}/items",
    body={"title": "Try the OxiTick API", "importance": 2},
)
print(f"\nCreated: {created['title']} ({created['id']})")

call("POST", f"/items/{created['id']}/completion", body={"completed": True})
print("Completed it.")

# Content is truncated in list and search responses. Fetch by id for the whole
# body -- and check content_truncated rather than guessing.
whole = call("GET", f"/items/{created['id']}")
print(f"Full record has {len(whole.get('subitems', []))} subtask(s).")
