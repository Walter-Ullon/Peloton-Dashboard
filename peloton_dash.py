import pandas as pd
import streamlit as st
import plotly.express as px
from feature_engineering_functions import *
from EDA_functions import *
from os import listdir
from os.path import isfile, join
from api_functions import *
from humanfriendly import format_timespan
from datetime import datetime, timedelta


# set global page layout:
st.set_page_config(page_title='Peloton Workouts Dashboard', page_icon="./images/pelo_black2.png", layout="wide")

########################################################################################################################
# About section:
########################################################################################################################
with st.expander(" About this app and how to use it."):
    st1, st2, st3 = st.columns([0.75, 1, 0.5])
    with st1:
        st.markdown('#### Note: ')
        st.markdown('This app loads sample data unless you own workouts file is uploaded.')
        st.markdown('#### To download your peloton workout data: ')
        st.markdown('1. Sign in to your Peloton account.')
        st.markdown('2. Click on your picture/username on the top right.')
        st.markdown('3. Select **Workouts** from the menu.')
        st.markdown('4. Click **DOWNLOAD WORKOUTS**.')

    with st2:
        st.image('./images/instructions.png', width=700)
    st.markdown('---')

    with st3:
        st.markdown('#### About your data: ')
        st.markdown('I created this app primarily for the purpose of tracking my progress at a high level, and '
                    'additionally as a learning experience using new tech tools. I hope you find it as fun to use as I do.')
        st.markdown('The data in the uploaded files is NEVER saved, snooped on, nor shared with anyone. '
                    'At any rate, please inspect the file and ensure it contains no "personally identifiable information".')
        st.markdown('Thanks for using my dashboard, and if you have any questions or comments, please click on my LinkedIn '
                    'and drop me a message!')

########################################################################################################################
# Header
########################################################################################################################
# hide footer:
hide_menu_style = """
        <style>
        # MainMenu {visibility: hidden; }
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# set divider for peloton logo:
h1, h2, h3 = st.columns([6,1,6])
with h2:
    st.image("./images/Clap_V02.gif")

# set divider for title:
t1, t2, t3, t4 = st.columns([2.4, 3.5, 0.12, 0.5])
with t2:
    # set dashboard title:
    st.title('Peloton Workouts Dashboard')
with t3:
    st.image('./images/LI-In-Bug.png', width=30)
with t4:
    st.markdown("###### By [Walter Ullon](https://www.linkedin.com/in/walter-ullon-459220133/)")

st.markdown('---')

########################################################################################################################
# File Upload:
########################################################################################################################
# file upload:
# loads sample data upon booting the app.
uploaded_file = st.file_uploader("Upload .csv")


# cache files to decrease latency:
@st.experimental_memo()
def load_workout_file(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("./data/my_workouts.csv")
    return df


# load:
df = load_workout_file(uploaded_file)

########################################################################################################################
# KPIs:
########################################################################################################################
# basic feature engineering:
df['workout: datetime'] = date_cleaner(df, 'Workout Timestamp', 10)
df['workout: day of week'] = day_of_week(df, 'Workout Timestamp')
df['workout: time of day'] = time_of_day(df, 'Workout Timestamp')
df['workout: month and year'] = month_of_year(df, 'Workout Timestamp')
df['workout: title'] = df['Title']

# get list of instructors:
img_path = "./images/"
instructor_lst = [f.split('.png')[0] for f in listdir(img_path) if isfile(join(img_path, f))]


st.markdown('---')


# set the KPI columns:
# trick: use kpi0 to pad columns and align center...
# kpi0, kpi1, kpi2, kpi3 = st.columns([0.5, 1.5, 1.7, 1])
kpi0, kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns([0.2, 1, 1, 1, 1, 1, 1])

# get KPI data and write to KPIs:
with kpi1:
    total_workouts = int(df["Workout Timestamp"].count().sum())
    kpi1.metric(label='Total Workouts:', value=total_workouts)

with kpi2:
    total_cals = "{:,}".format(int(df['Calories Burned'].sum()))
    kpi2.metric(label='Total Calories Burned:', value=total_cals)

with kpi3:
    # get favorite instructor name:
    favorite_instructor = str(df.groupby(["Instructor Name"])["Instructor Name"].count().sort_values(
        ascending=False).index.tolist()[0])
    # get number of workouts:
    num_workouts = str(df.groupby(["Instructor Name"])["Instructor Name"].count().sort_values(
        ascending=False)[0])

    # get top instructor image:
    hero_img = "./images/" + favorite_instructor + ".png"
    kpi3.metric(label='Favorite Instructor:', value=favorite_instructor)
    st.image(hero_img, width=140)
    kpi3.metric(label='Number of workouts:', value=num_workouts)

with kpi4:
    # create a copy for 'hardest workout' calculations:
    hwo_df = df.copy()
    hwo_df = hwo_df.drop(df[df['Length (minutes)'] == 'None'].index)
    hwo_df['average output/minute'] = pd.to_numeric(hwo_df['Total Output'], errors='coerce').fillna(0.0001) / \
                                      pd.to_numeric(hwo_df['Length (minutes)'], errors='coerce').fillna(0.0001)
    hwo_df['calories per minute'] = pd.to_numeric(hwo_df['Calories Burned'], errors='coerce').fillna(0.0001) / \
                                    pd.to_numeric(hwo_df['Length (minutes)'], errors='coerce').fillna(0.0001)

    workout_title = hardest_workout_metrics(hwo_df, 'Calories Burned', 'Length (minutes)', 'Title')
    instructor = hardest_workout_metrics(hwo_df, 'Calories Burned', 'Length (minutes)', 'Instructor Name')
    output_metric = hardest_workout_metrics(hwo_df, 'Calories Burned', 'Length (minutes)', 'calories per minute')

    if instructor not in instructor_lst:
        kpi4.metric(label='Hardest Workout: ' + workout_title, value=instructor)
        hardest_instructor = "./images/multi-ride.png"
        st.image(hardest_instructor, width=132)
    else:
        kpi4.metric(label='Hardest Workout: ' + workout_title, value=instructor)
        hardest_instructor = './images/' + instructor + '.png'
        st.image(hardest_instructor, width=140)

    kpi4.metric(label='Avg. calories/minute:', value=str("{:.1f}".format(output_metric)))

with kpi5:
    total_time = get_total_workout_time(df, 'Length (minutes)')
    kpi5.metric(label='Total Workout Time:', value=str("{:,}".format(total_time)) + ' hours')

with kpi6:
    df.columns = df.columns.map(str)
    streak = longest_streak2(df, 'workout: datetime')
    kpi6.metric(label='Longest Consecutive Streak:', value=str(streak) + ' days')

st.markdown('---')


########################################################################################################################
# Charts (middle):
########################################################################################################################
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    hue1 = st.radio(
        "break down 'Time of Day' by: ",
        ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
    array_tod = ['early morning', 'morning', 'early afternoon', 'evening', 'late night']
    figc1 = count_histogram(df, x='workout: time of day', color=hue1, w=700, h=600, array_l=array_tod)
    st.plotly_chart(figc1)

with c2:
    hue2 = st.radio(
        "break down 'Day of Week' by: ",
        ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
    array_dow = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    figc2 = count_histogram(df, x='workout: day of week', color=hue2, w=700, h=600, array_l=array_dow)
    st.plotly_chart(figc2)

with c3:
    hue3 = st.radio(
        "break down 'Month and Year' by: ",
        ('Type', 'Fitness Discipline', 'Live/On-Demand'), index=0)
    dates = month_of_year(df, 'Workout Timestamp')
    array_dates = []
    array_dates = [array_dates.append(x) for x in dates if x not in array_dates]
    figc3 = count_histogram(df, x='workout: month and year', color=hue3, w=700, h=600, array_l=array_dates)
    st.plotly_chart(figc3)

st.markdown('---')

########################################################################################################################
# Charts (bottom):
########################################################################################################################
# set initial charts columns:
column_left, column_middle, column_right = st.columns([1, 1, 1])

# write to columns:
with column_left:
    option = st.selectbox("Calories Burned vs. Instructor: ", ['avg', 'sum', 'count'], index=1)
    fig = histogram(df, x="Instructor Name", y="Calories Burned", func=option, w=700, h=600)
    fig.update_xaxes(tickangle=45)
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
    fig2 = histogram(df, x='workout: title', y="Calories Burned", func=option, w=700, h=600)
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2)

########################################################################################################################
# Instructor section:
########################################################################################################################
st.markdown("""<hr style="height:4px;border:none;color:#d8d4dc;background-color:#d8d4dc;" /> """, unsafe_allow_html=True)
st.markdown('### Peloton Heroes and their Class Stats:')

@st.experimental_singleton()
def load_class_data(file):
    if file is not None:
        classes_df = pd.read_csv(file, low_memory=False)
        classes_df = classes_df.rename(columns={'difficulty_rating_avg': 'average difficulty rating',
                                                'fitness_discipline_display_name': 'fitness discipline',
                                                'difficulty_rating_count': 'difficulty rating count',
                                                'original_air_time': 'premiere',
                                                'overall_rating_avg': 'overall rating average',
                                                'overall_rating_count': 'overall rating count',
                                                'total_workouts': 'total user workouts'})
        classes_df['duration secs'] = classes_df['duration']
        classes_df['duration'] = [format_timespan(x) for x in sorted(classes_df['duration'])]
        classes_df['premiere'] = [x.split(' ')[0] for x in classes_df['premiere']]
        classes_df['average difficulty rating'] = classes_df['average difficulty rating'].apply(lambda x: round(x, 2))
        classes_df['overall rating average'] = (classes_df['overall rating average'] * 100).apply(lambda x: round(x, 2))

    return classes_df


# load and preprocess class data:
classes_df = load_class_data('./data/class_data/master_classes.csv')

ins1, ins2, ins3, ins4 = st.columns([0.5, 1, 1, 1])

# pull instructor data:
instructors_df = get_instructors_data()

# plot data:
with ins1:
    instructor = st.selectbox('Please Select your Peloton Hero: ', instructors_df['name'], index=17)
    image_url = instructors_df.loc[instructors_df['name'] == instructor, 'about_image_url'].values[0]
    instructor_quote = instructors_df.loc[instructors_df['name'] == instructor, 'quote'].values[0].replace('“', '').replace('”', '')
    st.image(image_url, width=300)
    st.markdown('"' + instructor_quote + '"')
    
with ins2:
    # TODO: need a way to update metrics so we can avoid zeros in the rating counts
    hero_df = classes_df[(classes_df['instructor_name'] == instructor) & (classes_df['overall rating count'] != 0)]
    diff_array = sorted(list(hero_df['duration']), reverse=True)
    difficultyfig = count_histogram(hero_df, 'fitness discipline', 'duration', 650, 600, diff_array)
    difficultyfig.update_layout(title_text='Count of Classes Instructed by Discipline')
    st.plotly_chart(difficultyfig)

with ins3:
    scatterfig2 = px.scatter(hero_df,
                            x='overall rating average',
                            y='overall rating count',
                            size='total user workouts',
                            marginal_x='box',
                            marginal_y='box',
                            color='fitness discipline',
                            hover_data=['title', 'premiere', 'average difficulty rating', 'difficulty rating count',
                                        'overall rating average', 'overall rating count', 'total user workouts'])
    scatterfig2.update_layout(
        title_text='Average User Rating of Classes Instructed',
        autosize=False,
        width=650,
        height=600)
    scatterfig2.update_xaxes(
        tickvals=np.arange(0, 101))
    scatterfig2.update_traces(notched=False, selector=dict(type='box'))
    st.plotly_chart(scatterfig2)

with ins4:
    scatterfig = px.scatter(hero_df,
                            x='average difficulty rating',
                            y='difficulty rating count',
                            size='total user workouts',
                            marginal_x='box',
                            marginal_y='box',
                            color='fitness discipline',
                            hover_data=['title', 'premiere', 'average difficulty rating', 'difficulty rating count',
                                        'overall rating average', 'overall rating count', 'total user workouts'])
    scatterfig.update_layout(
        title_text='Average Difficulty Rating of Classes Instructed',
        autosize=False,
        width=650,
        height=600)
    scatterfig.update_xaxes(
        tickvals=np.arange(0, 11))
    scatterfig.update_traces(notched=False, selector=dict(type='box'))
    st.plotly_chart(scatterfig)

st.markdown('---')

########################################################################################################################
# Instructor KPIs:
########################################################################################################################
# instructor KPIs:
inskpi0, inskpi1, inskpi2, inskpi3, inskpi4, inskpi5, inskpi6 = st.columns([0.2, 1, 1, 1, 1, 1, 1])

with inskpi1:
    total_instructed = '{:,}'.format(len(hero_df['instructor_id']))
    inskpi1.metric(label='Total Classes Instructed:', value=total_instructed)

with inskpi2:
    total_user_workouts = '{:,}'.format(hero_df['total user workouts'].sum()) + '+'
    inskpi2.metric(label='Total User Workouts:', value=total_user_workouts)

with inskpi3:
    median_quality_rating = '{:.2f}'.format(hero_df['overall rating average'].median())
    inskpi3.metric(label='Median Rating Across All Classes:', value=median_quality_rating)

with inskpi4:
    avg_rating_per_class = '{:,.0f}'.format(hero_df['overall rating count'].sum() / len(hero_df['instructor_id']))
    inskpi4.metric(label='Average Number of Rating per Class:', value=avg_rating_per_class)

with inskpi5:
    median_difficulty_rating = '{:.2f}'.format(hero_df['average difficulty rating'].median())
    inskpi5.metric(label='Median Difficulty Rating:', value=median_difficulty_rating)

with inskpi6:
    total_hours_instructed = '{:,.1f}'.format(hero_df['duration secs'].sum() / 3600) + ' hours'
    inskpi6.metric(label='Total Hours of Instruction:', value=total_hours_instructed)

st.markdown('---')

########################################################################################################################
# Instructor Best and Worst classes:
########################################################################################################################
# ride images:
insimages0, insimages1, insimages2, insimages3, insimages4 = st.columns([0.2, 1, 1, 1, 1])

# lag ratings dataframe by one month to give classes a chance to rack up ratings:
ratings_df = hero_df[pd.to_datetime(hero_df['premiere']) < pd.to_datetime(datetime.today() - timedelta(days=15))]

with insimages1:
    most_rated_ride_img = ratings_df.loc[ratings_df['overall rating count'] == ratings_df['overall rating count'].max(),
                                         'image_url'].values[0]
    most_rated_ride_title = ratings_df.loc[ratings_df['overall rating count'] == ratings_df['overall rating count'].max(),
                                           'title'].values[0]
    st.markdown('Most Rated Class: ' + most_rated_ride_title)
    most_rated_ride_premiere = ratings_df.loc[ratings_df['overall rating count'] == ratings_df['overall rating count'].max(),
                                           'premiere'].values[0]
    most_rated_ride_count = '{:,}'.format(ratings_df['overall rating count'].max()) + ' ratings'
    st.image(most_rated_ride_img, width=400)
    st.markdown('premiered on ' + most_rated_ride_premiere + " (" + most_rated_ride_count + ")")

with insimages2:
    highest_rated_ride_img = ratings_df.loc[ratings_df['overall rating average'] ==
                                            ratings_df['overall rating average'].max(), 'image_url'].values[0]
    highest_rated_ride_title = ratings_df.loc[ratings_df['overall rating average'] ==
                                              ratings_df['overall rating average'].max(), 'title'].values[0]
    st.markdown('Highest Rated Class: ' + highest_rated_ride_title)
    highest_rated_ride_premiere = ratings_df.loc[ratings_df['overall rating average'] ==
                                                 ratings_df['overall rating average'].max(), 'premiere'].values[0]
    highest_rated_ride_count = '{:,}'.format(ratings_df['overall rating average'].max()) + ' average rating'
    st.image(highest_rated_ride_img, width=400)
    st.markdown('premiered on ' + highest_rated_ride_premiere + " (" + highest_rated_ride_count + ")")

with insimages3:
    most_difficult_ride_img = ratings_df.loc[ratings_df['average difficulty rating'] ==
                                             ratings_df['average difficulty rating'].max(), 'image_url'].values[0]
    most_difficult_ride_title = ratings_df.loc[ratings_df['average difficulty rating'] ==
                                               ratings_df['average difficulty rating'].max(), 'title'].values[0]
    st.markdown('Most Difficult Class: ' + most_difficult_ride_title)
    most_difficult_ride_premiere = ratings_df.loc[ratings_df['average difficulty rating'] ==
                                                  ratings_df['average difficulty rating'].max(), 'premiere'].values[0]
    most_difficult_ride_count = '{:,}'.format(ratings_df['average difficulty rating'].max()) + \
                                ' average difficulty rating'
    st.image(most_difficult_ride_img, width=400)
    st.markdown('premiered on ' + most_difficult_ride_premiere + " (" + most_difficult_ride_count + ")")

with insimages4:
    lowest_rated_ride_img = ratings_df.loc[ratings_df['overall rating average'] ==
                                            ratings_df['overall rating average'].min(), 'image_url'].values[0]
    lowest_rated_ride_title = ratings_df.loc[ratings_df['overall rating average'] ==
                                              ratings_df['overall rating average'].min(), 'title'].values[0]
    st.markdown('Lowest Rated Class: ' + lowest_rated_ride_title)
    lowest_rated_ride_premiere = ratings_df.loc[ratings_df['overall rating average'] ==
                                                 ratings_df['overall rating average'].min(), 'premiere'].values[0]
    lowest_rated_ride_count = '{:,}'.format(ratings_df['overall rating average'].min()) + ' average rating'
    st.image(lowest_rated_ride_img, width=400)
    st.markdown('premiered on ' + lowest_rated_ride_premiere + " (" + lowest_rated_ride_count + ")")

# with st.expander("Note:"):
#     st.markdown('The data for this subsection has been "lagged" by 30 days to allow classes to rack up ratings and '
#                 'give a more accurate representation of the true user ratings. Thus, only classes that have premiered '
#                 'up to one month (from today) are used to find the highest and lowest rated classes. This avoids '
#                 'having classes with few but inflated ratings, and other with few but heavily penalized scores.')
st.markdown('---')
with st.expander("COMING SOON:"):
    st.markdown("I'm looking to add two more sections to this project: one on publicly available instructor workouts"
                " (classes they've taken as opposed to instructed) so that users can see how they stack up against "
                "their peloton faves. And one on the overall stats for the peloton ecosystem, "
                "(highest rated classes overall, total number of user workouts, etc. With all the talk about a "
                "possible acquisition by bigger brands, it'd be interesting to see what the available data says "
                "they'd be getting in terms of impressions, etc...")
