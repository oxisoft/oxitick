#!/bin/sh
# Working examples against the personal API.
#
# Create a token in the app: Settings → Security → App tokens → New token.
set -eu

SERVER="${OXITICK_SERVER_URL:?set OXITICK_SERVER_URL, e.g. https://oxitick.example.com}"
TOKEN="${OXITICK_TOKEN:?set OXITICK_TOKEN, the oxt_... value shown when you created it}"

auth="Authorization: Bearer ${TOKEN}"
json="Content-Type: application/json"

echo "== Your lists =="
curl -sS -H "$auth" "$SERVER/api/v1/personal/lists"
echo

echo
echo "== Overdue, most urgent first =="
curl -sS -H "$auth" "$SERVER/api/v1/personal/items?overdue=true&limit=10"
echo

echo
echo "== Search =="
curl -sS -H "$auth" --get --data-urlencode "q=milk" \
  "$SERVER/api/v1/personal/items"
echo

echo
echo "== Add a task to the first list =="
LIST_ID=$(curl -sS -H "$auth" "$SERVER/api/v1/personal/lists" \
  | sed -n 's/.*"id":"\([^"]*\)".*/\1/p' | head -1)
[ -n "$LIST_ID" ] || { echo "no lists to add to" >&2; exit 1; }

ITEM=$(curl -sS -X POST -H "$auth" -H "$json" \
  -d '{"title":"Try the OxiTick API","importance":2}' \
  "$SERVER/api/v1/personal/lists/$LIST_ID/items")
echo "$ITEM"
ITEM_ID=$(echo "$ITEM" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p' | head -1)

echo
echo "== Complete it =="
curl -sS -X POST -H "$auth" -H "$json" -d '{"completed":true}' \
  "$SERVER/api/v1/personal/items/$ITEM_ID/completion"
echo

# Deliberately not shown, because they do not exist:
#
#   creating, renaming, archiving or deleting a list
#   deleting more than one task in a call
#   completing "everything matching" a filter
#
# The batch endpoint takes explicit ids and caps them at 25:
#
#   curl -X POST -H "$auth" -H "$json" \
#     -d '{"ids":["...","..."],"completed":true}' \
#     "$SERVER/api/v1/personal/items/completion"
