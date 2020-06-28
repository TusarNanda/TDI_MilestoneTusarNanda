from flask import Flask, render_template, request, abort, redirect, url_for
import calendar
import datetime
from datetime import date, timedelta
import requests, os
import pandas as pd
from urllib.request import Request, urlopen
import json
import pandas as pd
from pandas.io.json import json_normalize
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
#key = "FT6OW31F32GSR9AZ"

# getYear function returns the year based on the month input by the user.
# if the month input is less than equal to 5, the year is 2020 else the year is 2019
def getYear(mon):
    if mon < 6 and mon > 0:
        year = int(2020)
    elif mon <= 12:
        year = int(2019)
    return int(year)

def getDataPlot(month, stock, p_type):
    #####month = int(input("Enter a month: "))
    yr = getYear(int(month))
    #print(yr)
    start_date = datetime.date(int(yr), int(month), int(1))
    #print('here', start_date, type( start_date))
    num_days = (calendar.monthrange(int(yr), int(month))[-1])
    #####print(num_days)
    end_date=start_date + timedelta(days=num_days-1)
    #print('end', end_date)
    ######key = os.environ.get('API_KEY')
    key = 'FT6OW31F32GSR9AZ'
    ######stock = ((input("Enter a ticker: ")).upper())
    ######print(stock)
    # get data from Alpha Vantage and store in a pandas dataframe
    base_url = 'https://www.alphavantage.co/query?'
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": stock,
        "outputsize": "full",
        "apikey": key
        }
    response = requests.get(base_url, params=params)
    response_dict = response.json()
    try:
        meta, header = response.json()
    except:
        print("An exception occurred")
        abort(500)
    df = pd.DataFrame.from_dict(response_dict[header], orient='index')

    ######Clean up column names
    df_cols = [i.split(' ')[1] for i in df.columns]
    df.columns = df_cols
    # print(df.dtypes)
    # print(df.head())
    df = df.drop(['high', 'low', 'volume', 'dividend', 'split' ], axis=1)
    #print('after_drop', df.head())
    df['Date'] = pd.to_datetime(df.index)
    df.reset_index(drop=True, inplace=True)
    # print(df.dtypes)
    ## filter data based on user input, calculate the new column and arrange the data
    start_date = str(start_date)
    end_date = str(end_date)
    mask = (df['Date'] > pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
    df = df.loc[mask]
    # print("after filter")
    # print(df.head())
    df.columns = ['open', 'close', 'adjusted_close', 'Date']
    df = df.sort_values(by=['Date'])
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['adjusted_close'] = df['adjusted_close'].astype(float)
    df['adjusted_open'] = (df.adjusted_close / df.close) * df.open
    df = df[['Date', 'open', 'adjusted_open', 'close', 'adjusted_close']]

    # print("final columns")
    # print(df.head(25))

    df = df.sort_values(by=['Date'])
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['adjusted_close'] = df['adjusted_close'].astype(float)
    df["adjusted_open"] = (df["adjusted_close"]/ df["close"])*df["open"]

    # print('before bokeh')
    # print(df.head())
    ## plot the data in bokeh bases on the plot chosen by the user
    p = figure(
        width=1725,
        height=500,
        x_axis_type="datetime")


    if p_type == 'Opening Price':
        #p.yaxis.axis_label = 'Opening Price'
        #p.legend.title = p_type + 'Stock prices of ' + stock
        p.line(df["Date"], df["open"], line_width=3, color="red", alpha=0.5, legend_label="Opening Price")
    elif p_type == 'Adjusted Opening Price':
        # p.yaxis.axis_label = 'Adjusted Opening Price'
        # p.legend.title = p_type + 'Stock prices of ' + stock
        p.line(df["Date"], df["adjusted_open"], line_width=3, color="orange", alpha=0.5, legend_label="Adjusted Opening Price")
    elif p_type == 'Closing Price':
        # p.yaxis.axis_label = 'Closing Price'
        # p.legend.title = p_type + 'Stock prices of ' + stock
        p.line(df["Date"], df["close"], line_width=3, color="blue", alpha=0.5, legend_label="Closing Price")

    elif p_type == 'Adjusted Closing Price':
        # p.yaxis.axis_label = 'Adjusted Closing Price'
        # p.legend.title = p_type + 'Stock prices of ' + stock
        p.line(df["Date"], df["adjusted_close"], line_width=3, color="green", alpha=0.5, legend_label="Adjusted_Closing Price")
    elif p_type == 'All':
        #p.legend.title = p_type + 'Stock prices of ' + stock
        p.line(df["Date"], df["open"], line_width=3, color="red", alpha=0.5, legend_label="Opening Price")
        p.line(df["Date"], df["close"], line_width=3, color="blue", alpha=0.5, legend_label="Closing Price")
        p.line(df["Date"], df["adjusted_open"], line_width=3, color="orange", alpha=0.5, legend_label="Adjusted Opening price")
        p.line(df["Date"], df["adjusted_close"], line_width=3, color="green", alpha=0.5, legend_label="Adjusted_Closing Price")
    p.xaxis.axis_label = 'Date'
    p.legend.location = 'top_left'
    p.legend.title = 'Legend'
    p.legend.title_text_font = 'Arial'
    p.legend.title_text_font_size = '15pt'
    p.title.text = "One-Month stock Price of " +stock.upper()
    p.title.align = "center"
    p.title.text_color = "red"
    p.title.text_font_size = "25px"
    p.title.background_fill_color = "yellow"
    script, div = components(p)
    #print(script)
    # output_file("plot.html")
    # show(p)
    # return
    return script, div






app = Flask(__name__)
# for handling errors caused by user inputs where data does not exist
@app.errorhandler(500)
def server_error(e):
    print('Please do not enter a valid ticker')
    return render_template("error.html")
# render error.html if non existant data error occurs.
@app.route('/error', methods=['GET', 'POST'])
def back():
    if request.method== 'POST':
        return render_template("index.html")
# render contact.html when the relevant link is clicked on the web App
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return render_template("contact.html")
    return render_template("contact.html")

# Main function for the index or home page
@app.route('/', methods=['GET', 'POST'])
def index():
    #abort(404)
    if request.method== 'POST':
        stock1 = request.form['stock']
        print(stock1)
        user_month = request.form['month']
        print(user_month)
        graph1 = request.form['plot_type']
        print (graph1)
        script, div = getDataPlot(user_month, stock1, graph1)
        return render_template("index.html", div=div, script=script)
    return render_template("index.html")

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(port=32103)
