import pandas as pd
import numpy as np
from datetime import datetime
from pandas.api.types import CategoricalDtype

# returns day of the week:
def day_of_week(df, col):
    # remove last 6 characters:
    df['day_of_week'] = [x[:-6] for x in df[col]]
    # convert to day of week:
    df['day_of_week'] = pd.to_datetime(df['day_of_week']).dt.day_name()
    day_of_week_lst = df['day_of_week'].tolist()
    df.drop(labels='day_of_week', axis=1, inplace=True)
    return day_of_week_lst


# returns date without trailing (-#):
def date_cleaner(df, date_col):
    # remove last 6 characters:
    df['new_datetime'] = [x[:-12] for x in df[date_col]]
    # convert to day of week:
    df['new_datetime'] = pd.to_datetime(df['new_datetime'])
    cleaned_date_lst = df['new_datetime'].tolist()
    df.drop(labels='new_datetime', axis=1, inplace=True)
    return cleaned_date_lst


# returns the discretized time of day:
def time_of_day(df, col):
    # get middle 5 chracters and strip colon, essentially turning it into military time.
    # converts to integer for comparison:
    df['time_of_day'] = [int(x[10:16].replace(':', '')) for x in df[col]]
    time_of_day_lst = []
    
    # discretize hours
    for tod in df['time_of_day']:
        if tod <= 600:
            time_of_day_lst.append('early morning')
        elif tod > 600 and tod <= 1200:
            time_of_day_lst.append('morning')
        elif tod > 1200 and tod <= 1700:
            time_of_day_lst.append('early afternoon')
        elif tod > 1700 and tod <= 2100:
            time_of_day_lst.append('evening')
        else:
            time_of_day_lst.append('late night')
            
    df.drop(labels='time_of_day', axis=1, inplace=True)
    return time_of_day_lst


# returns the month of the year i.e. October-21:
def month_of_year(df, col):
    df['month_of_year'] = [x[:-12] for x in df[col]]
    dates = pd.to_datetime(df['month_of_year'])
    df['month_of_year'] = dates.apply(lambda x: x.strftime('%B-%y'))
    month_of_year_lst = df['month_of_year'].tolist()
    
    df.drop(labels='month_of_year', axis=1, inplace=True)
    return month_of_year_lst


# get ride type:
def get_workout_type(df):
    workout_type_lst = [x.split(' ', 2)[2] for x in df['Title']]
    return workout_type_lst


# return instructor images matching top value given by y:
def get_hero(df, y):
    hero = df.loc[df[y].idxmax(), "Instructor Name"]