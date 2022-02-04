import pandas as pd
import requests
import streamlit as st
import os
from datetime import datetime

# initiate session:
s = requests.Session()
payload = {'username_or_email':'RuntimeT3rror', 'password':'Brielle2021'}
s.post('https://api.onepeloton.com/auth/login', json=payload)


# convert unix dates to readable date format i.e. "2021-03-14 08:33":
def unix_date_converter(date_series):
    for i, unix_ts in enumerate(date_series):
        date_series[i] = datetime.utcfromtimestamp(date_series[i]).strftime('%Y-%m-%d %H:%M')
    return date_series


# get a dataframe of all instructors plus their quotes, hero pictures, etc:
@st.experimental_memo()
def get_instructors_data():
    instructors = s.get('https://api.onepeloton.com/api/instructor?limit=100').json()
    instructors_df = pd.DataFrame.from_dict(instructors['data'])

    return instructors_df


# return a csv for every workout category and all of its classes:
def get_class_data(dir_path):
    # get a list of all workout categories:
    wo_categories = s.get('https://api.onepeloton.com/api/v2/ride/archived?browse_category=cycling&page=0').json()
    categories_df = pd.DataFrame.from_dict(wo_categories['browse_categories'])

    # for each class category (saved as a 'slug' in peloton's lingo), get the total number of pages worth of classes:
    for slug in categories_df['slug']:
        wo_url = 'https://api.onepeloton.com/api/v2/ride/archived?browse_category=' + str(slug)
        page_count = s.get(wo_url).json()['page_count']

        # for each page, get all the classes and append the results to the previous page:
        slug_df = pd.DataFrame()
        for page_num in range(page_count + 1):
            page_url = wo_url + '&page=' + str(page_num)
            page_classes = s.get(page_url).json()
            slug_df = pd.concat([slug_df, pd.DataFrame.from_dict(page_classes['data'])])

        # after all pages have been iterated through, save final df to csv and free it from memory:
        # TODO: ensure dir_path contains '/'
        slug_df.to_csv(dir_path + slug + ".csv", index=None)
        del slug_df


# takes a df of instructor taken workouts and looks for the name of the instructors who conducted for said workouts:
def get_class_instructor_name(workouts_df):
    instructor_names = []
    try:
        for workout_id in workouts_df['id']:
            workout_data = s.get('https://api.onepeloton.com/api/workout/' + str(workout_id)).json()
            try:
                instructor_id = workout_data['ride']['instructor_id']
                if instructor_id is not None:
                    instructor_name = s.get('https://api.onepeloton.com/api/instructor/' + instructor_id).json()['name']
                    instructor_names.append(instructor_name)
                else:
                    instructor_name = workout_data['name']
                    instructor_names.append(instructor_name)
            except KeyError as e:
                instructor_name = workout_data['workout_type']
                instructor_names.append(instructor_name)
    except KeyError as e:
        pass

    workouts_df['instructor_name'] = instructor_names
    return workouts_df


# return all publicly available workouts for an instructor:
def get_instructor_workouts(user_id):
    # TODO: add ability to perform diff and always get latest workouts:
    wo_url = 'https://api.onepeloton.com/api/user/' + str(user_id) + '/workouts?limit=100'
    wo_df = pd.DataFrame()
    try:
        page_count = s.get(wo_url).json()['page_count']

        for page_num in range(page_count + 1):
            page_url = wo_url + '&page=' + str(page_num)
            page_classes = s.get(page_url).json()
            wo_df = pd.concat([wo_df, pd.DataFrame.from_dict(page_classes['data'])])
    except KeyError as e:
        print('Workout data for this instructor is not publicly available.')
    wo_df = get_class_instructor_name(wo_df)

    return wo_df


# pull workout data for all available peloton instructors and save them as individual files for each instructor:
def get_all_instructors_workouts(path_to_dir):
    # TODO: change API call to file read (./data/complete_instructors.csv)
    instructors_df = get_instructors_data()

    for user_id in instructors_df['user_id']:
        wo_df = get_instructor_workouts(user_id)
        instructor_name = (instructors_df.loc[instructors_df['user_id'] == user_id, 'name'].values[0]).replace(' ', '_')
        file_name = path_to_dir + '/' + instructor_name + '.csv'
        wo_df.to_csv(file_name)


# get device type mappings:
@st.experimental_memo()
def get_device_type_mappings():
    device_types = s.get('https://api.onepeloton.com/api/ride/metadata_mappings').json()['device_type_display_names']
    device_types_df = pd.DataFrame.from_dict(device_types)

    return device_types_df


# concatenate all class dataframes into a single file and convert dates, get instructor names, etc...
def preprocess_classes_data(dir_path):
    # create master file to hold all data:
    master_class_df = pd.DataFrame()

    # get list of instructors and their profile data:
    instructors = pd.read_csv('./data/complete_instructors.csv')

    # scan directory and start appending files:
    for filename in os.scandir(dir_path):
        try:
            # check for to see if file is .csv:
            if filename.is_file() and '.csv' in str(filename):
                temp_df = pd.read_csv(filename, low_memory=False)

                # convert unix time to datetime:
                temp_df['original_airtime'] = unix_date_converter(temp_df['original_air_time'])
                temp_df['instructor_name'] = pd.Series()

                # get instructor name from ID:
                try:
                    for i, instructor_id in enumerate(temp_df['instructor_id']):
                        try:
                            instructor_name = instructors.loc[instructors['id'] == instructor_id, 'name'].values[0]
                            temp_df['instructor_name'][i] = instructor_name
                        except (IndexError, KeyError) as e:
                            # if ID not found in instructors file, call the API, append the new record to the instructors
                            # file and save:
                            instructor_dict = s.get(
                                'https://api.onepeloton.com/api/instructor/' + str(instructor_id)).json()
                            new_instructor_df = pd.DataFrame([instructor_dict])
                            instructor_name = instructor_dict['name']
                            instructors = pd.concat([instructors, new_instructor_df])
                            temp_df['instructor_name'][i] = instructor_name
                except (IndexError, KeyError) as e:
                    pass
        except (IndexError, KeyError) as e:
            pass

        # collect all of the class dataframes:
        master_class_df = pd.concat([master_class_df, temp_df])
        # save any new records to the main instructors file:
        instructors.to_csv('./data/complete_instructors.csv')
    return master_class_df