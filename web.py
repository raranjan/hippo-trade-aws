from flask import Flask, render_template, abort
import pandas as pd
from datetime import datetime

app = Flask(__name__)
now = datetime.now()
today_date = now.strftime("%d-%m-%Y")
INSTRUMENT = 'nifty'
LOT_SIZE = 50
FILE_PATH = f'data/positions/{INSTRUMENT}_smart_straddle_{today_date}.feather'

@app.route('/')
def index():
    position_data = read_position_file()
    total_pnl = position_data["PNL"].sum() * LOT_SIZE
    return render_template('index.html', data=position_data.values, total_pnl=total_pnl)

def read_position_file():
    try:
        data = pd.read_feather(FILE_PATH)
        print(data)
        columns = ['Premium', 'Trigger Price', 'Stop Loss', 'Target', 'Lots', 'Position', 'Entry Price', 'Exit Price', 'Current Price', 'PNL']
        return data
    except:
        abort(400)

@app.errorhandler(400)
def file_not_found(error):
    return "Sorry, Position File is not availaible yet", 400

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)