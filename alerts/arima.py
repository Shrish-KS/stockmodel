from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import numpy as np
from multiprocessing import Pool
from functools import partial
import warnings
import yfinance as yf
from statsmodels.tsa.stattools import adfuller


'''
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_email_password'

'''



warnings.filterwarnings("ignore")

def get_historical_stock_data(symbol, start_date, end_date):
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    return data

def cald(data):
    adfuller()

def evaluate_arima_model(X, arima_order):
    train_size = int(len(X) * 0.66)
    train, test = X[0:train_size], X[train_size:]
    history = [x for x in train]
    
    predictions = list()
    for t in range(len(test)):
        model = ARIMA(history, order=arima_order)
        model_fit = model.fit()
        yhat = model_fit.forecast()[0]
        predictions.append(yhat)
        history.append(test[t])
    
    error = mean_squared_error(test, predictions)
    return error

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
    
    print('Best ARIMA%s MSE=%.3f' % (best_cfg, best_score))
    model = ARIMA(dataset, order=best_cfg)
    model_fit = model.fit()
    yhat = model_fit.forecast()[0]
    print(yhat)
    result=[]
    for i in range(10):
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
    p_values = range(2,3)
    q_values = range(20,21)
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

if __name__=='__main__':
    start_date = "2022-01-31"
    end_date = "2023-01-30"

    historical_data = get_historical_stock_data("AAPL", start_date, end_date)
    data =historical_data['Open']
    main(data)