import pandas as pd
import streamlit as st
import plotly.express as px
from feature_engineering_functions import *
from EDA_functions import *

########################################################################################################################
# Header
########################################################################################################################

# set global page layout:
st.set_page_config(layout="wide")

# set divider for peloton logo:
h1, h2, h3 = st.columns([6,1,6])
with h2:
    st.image("./images/Clap_V02.gif")

# set divider for title:
t1, t2, t3, t4 = st.columns([2, 3.5, 0.12, 0.5])
with t2:
    # set dashboard title:
    st.title('My Peloton Workouts Dashboard')
with t3:
    st.image('./images/LI-In-Bug.png', width=30)
with t4:
    st.markdown("###### By [Walter Ullon](https://www.linkedin.com/in/walter-ullon-459220133/)")

st.markdown('---')
st1, st2, st3 = st.columns([1, 2, 1])
with st1:
    st.markdown('#### To download your peloton workout data: ')
    st.markdown('1. Sing into your Peloton account.')
    st.markdown('2. Click on your picture/username on the top right.')
    st.markdown('3. Select **Workouts** from the menu.')
    st.markdown('4. Click **DOWNLOAD WORKOUTS**.')

with st2:
    st.image('./images/instructions.png', width=700)
st.markdown('---')
########################################################################################################################
# KPIs:
########################################################################################################################
# file upload:
uploaded_file = st.file_uploader("Upload .csv")
if uploaded_file is not None:
     # To read file as bytes:
    # bytes_data = uploaded_file.getvalue()
     # st.write(bytes_data)

     # # To convert to a string based IO:
     # stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
     # st.write(stringio)

     # # To read file as string:
     # string_data = stringio.read()
     # st.write(string_data)

     # Can be used wherever a "file-like" object is accepted:
    df = pd.read_csv(uploaded_file)

     # basic feature engineering:
    df['workout: datetime'] = date_cleaner(df, 'Workout Timestamp')
    df['workout: day of week'] = day_of_week(df, 'Workout Timestamp')
    df['workout: time of day'] = time_of_day(df, 'Workout Timestamp')
    df['workout: month and year'] = month_of_year(df, 'Workout Timestamp')
    df['workout: title'] = get_workout_type(df)

    # get KPI Data:
    total_cals = "{:,}".format(int(df['Calories Burned'].sum()))
    total_workouts = int(df["Workout Timestamp"].count().sum())
    favorite_instructor = str(df.groupby(["Instructor Name"])["Instructor Name"].count().sort_values(
        ascending=False).index.tolist()[0])

    # get top instructor image:
    hero_img = "./images/" + favorite_instructor + ".png"

    # set the KPI columns:
    # trick: use kpi0 to pad columns and align center...
    kpi0, kpi1, kpi2, kpi3 = st.columns([0.5, 1.5, 1.7, 1])

    # write info to KPIs:
    with kpi1:
         kpi1.metric(label='Total Calories Burned', value=total_cals)
    with kpi2:
        kpi2.metric(label='Favorite Instructor', value=favorite_instructor)
        st.image(hero_img, width=100)
    with kpi3:
        kpi3.metric(label='Total Workouts', value=total_workouts)

    st.markdown('---')


########################################################################################################################
# Charts (middle):
########################################################################################################################
    # set initial charts columns:
    column_left, column_middle, column_right = st.columns([1, 1, 1])

    # write to columns:
    with column_left:
        option = st.selectbox("Calories Burned vs. Instructor: ", ['avg', 'sum', 'count'], index=1)
        fig = histogram(df, x="Instructor Name", y="Calories Burned", func=option, w=700, h=600)
        st.plotly_chart(fig)

    with column_middle:
        option = st.selectbox("Avg. Heartrate by Key Metric: ", ["Calories Burned", "Avg. Watts", "Total Output",
                                                                  "Distance (mi)", "Avg. Speed (mph)",
                                                                  "Avg. Cadence (RPM)",
                                                                  "Avg. Resistance"], index=5)
        fig_heat = heatmap(df, x="Avg. Heartrate", y=option, w=700, h=600)
        st.plotly_chart(fig_heat)

    with column_right:
        option = st.selectbox("Calories Burned vs. Workout Title: ", ['avg', 'sum', 'count'], index=1)
        fig2 = histogram(df, x='workout: title', y="Calories Burned", func=option, w=800, h=600)
        st.plotly_chart(fig2)

    st.markdown('---')
########################################################################################################################
# Charts (bottom):
########################################################################################################################
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        hue1 = st.radio(
            "break down 'Time of Day' by: ",
            ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
        figc1 = count_histogram(df, x='workout: time of day', color=hue1, w=700, h=600)
        st.plotly_chart(figc1)

    with c2:
        hue2 = st.radio(
            "break down 'Day of Week' by: ",
            ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
        figc2 = count_histogram(df, x='workout: day of week', color=hue2, w=700, h=600)
        st.plotly_chart(figc2)

    with c3:
        hue3 = st.radio(
            "break down 'Month and Year' by: ",
            ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
        figc3 = count_histogram(df, x='workout: month and year', color=hue3, w=700, h=600)
        st.plotly_chart(figc3)

    st.markdown('---')
