import pandas as pd
import numpy as np
import networkx as nx
import plotly.express as px
import plotly.figure_factory as ff
from pandas.api.types import CategoricalDtype
from PIL import Image


# plots histogram of x and y. Aggregates based on func (sum, avg, etc.):
def histogram(df, x, y, func, w, h):
    fig = px.histogram(df, x=x, y=y, histfunc=func, hover_data=df.columns)
    fig.update_layout(
        autosize=False,
        width=w,
        height=h,)
    return fig


# plots histogram of x and count(x). Aggregates based on func (sum, avg, etc.):
def count_histogram(df, x, color, w, h):
    fig = px.histogram(df, x=x, color=color, hover_data=df.columns)
    fig.update_layout(
        autosize=False,
        width=w,
        height=h)
    return fig


# plots scatter matrix:
def scatter_matrix(df, category, dims, w, h):
    fig = px.scatter_matrix(df, dimensions=dims, color=category)
    fig.update_layout(
        autosize=False,
        width=w,
        height=h,)
    return fig


# plots scatter strip with hue:
def strip_plot(df, x, y, hue, w, h):
    fig = px.strip(df, x=x, y=y, color=hue)
    fig.update_layout(
        autosize=False,
        width=w,
        height=h)
    return fig


# plots day of the week heatmap (only work of datetimes have been converted to day of week):
def day_of_week_heatmap(df, y, w, h):
    cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    cat_type = CategoricalDtype(categories=cats, ordered=True)
    df['workout: day of week'] = df['workout: day of week'].astype(cat_type)
    df.sort_values(by='workout: day of week',axis=0, ascending=True,inplace = True)
    fig = px.density_heatmap(df, x="workout: day of week", y=y, marginal_x="histogram", marginal_y="histogram")
    fig.update_layout(
        autosize=False,
        width=w,
        height=h)
    return fig


def heatmap(df, x, y, w, h):
    fig = px.density_heatmap(df, x=x, y=y, marginal_x="histogram", marginal_y="histogram")
    fig.update_layout(
        autosize=False,
        width=w,
        height=h)
    return fig





    
