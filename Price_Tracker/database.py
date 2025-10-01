import sqlite3
import time
import os
import requests

# Create the database in same folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(SCRIPT_DIR, "market.db")
# Prices URLs
ALL_PRICES_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"
MAPPING_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"
# Need a header to make identified clals
HEADERS = {'User-Agent': 'Price Monitor'}


# Functions for our db
def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS exchange (
        id INTEGER PRIMARY KEY,
        fetch_timestamp INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        item_id INTEGER UNIQUE,
        high_price INTEGER,
        low_price INTEGER
    );
    '''
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()

def add_item_prices_bulk(price_data_list):
    """Adds a list of item price records to the database in one transaction."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # We need to replace if it exists 
    insert_sql = "REPLACE INTO exchange (fetch_timestamp, item_name, item_id, high_price, low_price) VALUES (?, ?, ?, ?, ?)"
    
    cursor.executemany(insert_sql, price_data_list)
    
    conn.commit()
    conn.close()
    print(f"Successfully added/updated {len(price_data_list)} item records.")

# API Functions
def get_item_mapping():
    try:
        response = requests.get(MAPPING_URL, timeout=20, headers=HEADERS)
        response.raise_for_status()
        items = response.json()
        # Create a dictionary for easy scraping
        return {str(item['id']): item['name'] for item in items if 'id' in item and 'name' in item}
    except Exception as e:
        print(f"UH oh, could not fetch item mapping: {e}")
        return None

def fetch_and_store_all_prices(item_mapping):
    print(f"\nFetching all prices at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        response = requests.get(ALL_PRICES_URL, timeout=60, headers=HEADERS) # If the payload is large, we may need a longer timeout
        response.raise_for_status()
        all_prices_json = response.json()
        
        price_data_to_insert = []
        current_timestamp = int(time.time())

        # The 'data' key contains a dictionary of {item_id: {high: price, low: price}}
        for item_id, price_info in all_prices_json['data'].items():
            # Look up the item name from our mapping
            item_name = item_mapping.get(item_id)
            
            if item_name and price_info['high'] is not None and price_info['low'] is not None:
                price_data_to_insert.append((
                    current_timestamp,
                    item_name,
                    int(item_id),
                    price_info['high'],
                    price_info['low']
                ))
        
        if price_data_to_insert:
            add_item_prices_bulk(price_data_to_insert)
            
    except Exception as e:
        print(f"Error during price update: {e}")

# Actual script execution
if __name__ == "__main__":
    print("Database will be created at:", DATABASE_FILE)
    initialize_database()

    print("Fetching item name mapping...")
    item_id_to_name = get_item_mapping()

    if not item_id_to_name:
        print("Could not start price tracker without item mapping. Exiting.")
    else:
        print(f"Successfully mapped {len(item_id_to_name)} items.")
        try:
            while True:
                fetch_and_store_all_prices(item_id_to_name)
                print("Wait")
                time.sleep(300)
        except KeyboardInterrupt:
            print("\nStopped price updater.")