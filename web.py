from flask import Flask, render_template, abort
import pandas as pd
from datetime import datetime
import os
import glob
import pandas as pd

app = Flask(__name__)
now = datetime.now()
today_date = now.strftime("%Y-%m-%d")
INSTRUMENT = 'nifty'
LOT_SIZE = 50
FILE_PATH = f'data/positions/{today_date}_positions.feather'

@app.route('/')
def index():
    position_data = read_position_file()
    print(position_data.columns)
    total_pnl = position_data["PNL"].sum() * LOT_SIZE
    return render_template('index.html', data=position_data.values, total_pnl=total_pnl)

@app.route('/summary')
def summary():
    data = create_summary_details()
    total_pnl = data["PNL"].sum() * LOT_SIZE
    return render_template('index.html', data=data.values, total_pnl=total_pnl)

@app.route('/login')
def login():
    return render_template('login.html')


def read_position_file():
    try:
        data = pd.read_feather(FILE_PATH)
        print(data)
        columns = ['Premium', 'Trigger Price', 'Stop Loss', 'Target', 'Lots', 'Position', 'Entry Price', 'Exit Price', 'Current Price', 'PNL']
        return data
    except:
        abort(400)

def create_summary_details():
    path = "data/positions/*.feather"
    files = glob.glob(path)
    data = None
    for file in files:
        if data is None:
            data = pd.read_feather(file)
        else:
            data = pd.concat(data, pd.read_feather(file))

    data = data[data["Entry Price"].notnull()]
    return data

@app.errorhandler(400)
def file_not_found(error):
    return "Sorry, Position File is not availaible yet", 400

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)