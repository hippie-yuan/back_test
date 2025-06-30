import numpy as np
import yfinance as yf
from datetime import datetime,timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time
from functools import partial

from matplotlib import animation

import matplotlib.lines as line
nvda_hist=pd.read_csv('nvda_hist.csv')
nvda_hist.index=pd.to_datetime(nvda_hist.Date, utc=True).dt.tz_convert('Asia/Shanghai')
real_time_price=nvda_hist['Close']
# print(type(real_time_price))
# print(nvda_hist[['Date','Close']].iloc[1001])
real_time_price=pd.concat([real_time_price[:1000],nvda_hist[['Date','Close']].iloc[[1001]]])
print(real_time_price)
