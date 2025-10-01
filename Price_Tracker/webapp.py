import sqlite3
from flask import Flask, jsonify, render_template
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(SCRIPT_DIR, "market.db")

app =  Flask(__name__)

def get_db_conn():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_conn()
    db_items = conn.execute('SELECT * FROM exchange ORDER BY item_name').fetchall()
    conn.close()

    processed_items = []
    for item in db_items:
        processed_items.append({
            'item_name': item['item_name'],
            'high_price': item['high_price'],
            'low_price': item['low_price'],
            'formatted_time': datetime.fromtimestamp(item['fetch_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('index.html', items=processed_items, current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == '__main__':
    app.run(debug=True)