from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import numpy as np
from multiprocessing import Pool
from functools import partial
import warnings
import yfinance as yf
from statsmodels.tsa.stattools import adfuller
import datetime
import threading


warnings.filterwarnings("ignore")

def get_historical_stock_data(symbol, start_date, end_date):
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    return data

def cald(data):
    adfuller()

def evaluate_arima_model(X, arima_order):
    model = ARIMA(X, order=arima_order)
    model_fit = model.fit()
    aic = model_fit.aic

    return aic

def evaluate_models(dataset, p_values, d_values, q_values):
    dataset=np.array(dataset).astype('float32')
    best_score, best_cfg = float("inf"), None
    
    pdq_values = [(p,d,q) for p in p_values for d in d_values for q in q_values]
    
    # define a partial function to pass the dataset as an argument to the evaluate_arima_model function
    partial_evaluate_arima_model = partial(evaluate_arima_model, dataset)
    
    # create a pool of worker processes
    pool = Pool()
    
    # evaluate all combinations of p, d and q values in parallel
    scores = pool.map(partial_evaluate_arima_model, pdq_values)
    # find the best performing model
    for pdq_value, score in zip(pdq_values, scores):
        print(pdq_value, score)
        if score < best_score:
            best_score, best_cfg = score, pdq_value
    
    print('Best ARIMA%s AIC=%.3f' % (best_cfg, best_score))
    model = ARIMA(dataset, order=best_cfg)
    model_fit = model.fit()
    yhat = model_fit.forecast()[0]
    print(yhat)
    result=[]
    for i in range(15):
        model = ARIMA(dataset, order=best_cfg)
        model_fit = model.fit()
        yhat = model_fit.forecast()[0]
        dataset=np.append(dataset,[yhat])
        result.append(yhat)
    print(result)
    return result

# load dataset
def main(data):
    # evaluate parameters
    p_values = range(0,5)
    q_values = range(0,5)
    data2=data.copy()
    d=0
    ad=adfuller(data2)
    print(ad)
    while ad[1]>0.05:
        d+=1
        data2=data2.diff()
        data2 = data2.replace([np.inf, -np.inf], np.nan).dropna()
        ad=adfuller(data2)
    d_values=range(d,d+1)
    return evaluate_models(data, p_values, d_values, q_values)

def getdata(symbol):
    current_date = datetime.date.today()
    prior_date = current_date - datetime.timedelta(days=500)
    start_date= prior_date.strftime("%Y-%m-%d")
    end_date = current_date - datetime.timedelta(days=1)
    end_date=end_date.strftime("%Y-%m-%d")
    historical_data = get_historical_stock_data(symbol, start_date, end_date)
    historical_data.reset_index(inplace=True)
    data=historical_data["Close"]
    return main(data)

if __name__=='__main__':
    start_date = "2022-01-01"
    end_date = "2023-01-30"

    historical_data = get_historical_stock_data("AAPL", start_date, end_date)
    data =historical_data['Open']
    main(data)