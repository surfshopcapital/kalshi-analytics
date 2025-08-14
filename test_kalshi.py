import sys, os

# Add the folder you’re in right now to sys.path:
sys.path.insert(0, os.getcwd())

from utils import get_client

client = get_client()

markets_page = client.get_markets(limit=5)
print("Sample markets page:", markets_page.get("markets", [])[:2])

all_markets = client.list_all_markets(status="open")
print(f"Total open markets fetched: {len(all_markets)}")

if all_markets:
    first = all_markets[0]["ticker"]
    print("Fetching orderbook and details for:", first)
    print(client.get_market(first))
    print(client.get_orderbook(first))

# If you enabled authentication and have actual account data:
# print(client.get_my_trades())
# print(client.get_positions())
