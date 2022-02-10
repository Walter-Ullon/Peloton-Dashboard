import pandas as pd
import requests
import streamlit as st
from datetime import datetime
from feature_engineering_functions import *

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
@st.experimental_singleton()
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
# TODO: add try except to replace the api call with file read for instructors
def get_class_instructor_name(workouts_df, instructors_df):
    instructor_names = []
    try:
        for workout_id in workouts_df['id']:
            workout_data = s.get('https://api.onepeloton.com/api/workout/' + str(workout_id)).json()
            try:
                instructor_id = workout_data['ride']['instructor_id']
                if instructor_id is not None:
                    try:
                        instructor_name = instructors_df.loc[instructors_df['id'] == instructor_id, 'name'].values[0]
                        instructor_names.append(instructor_name)
                    except (IndexError, KeyError) as e:    
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


# preprocess class data:
def preprocess_classes_data(diff_df):
    # get list of instructors and their profile data:
    instructors = pd.read_csv('./data/instructor_data/complete_instructors_list.csv')

    # convert unix time to datetime:
    diff_df['original_airtime'] = unix_date_converter(diff_df['original_air_time'])
    diff_df['instructor_name'] = pd.Series()
    
    # convert to day of week:
    diff_df['workout: day of week'] = pd.to_datetime(diff_df['original_airtime']).dt.day_name()
    # get time of day:
    diff_df['workout: time of day'] = time_of_day(diff_df, 'original_airtime')
    # get month and year i.e 'September 21'
    diff_df['workout: month and year'] = month_of_year(diff_df, 'original_airtime')
    # get workout title:
    diff_df['workout: title'] = diff_df['title']
    
    # get instructor name from ID:
    try:
        for i, instructor_id in enumerate(diff_df['instructor_id']):
            try:
                instructor_name = instructors.loc[instructors['id'] == instructor_id, 'name'].values[0]
                diff_df['instructor_name'][i] = instructor_name
            except (IndexError, KeyError) as e:
                # if ID not found in instructors file, call the API, append the new record to the instructors
                # file and save:
                instructor_dict = s.get('https://api.onepeloton.com/api/instructor/' + str(instructor_id)).json()
                new_instructor_df = pd.DataFrame([instructor_dict])
                instructor_name = instructor_dict['name']
                instructors = pd.concat([instructors, new_instructor_df])
                diff_df['instructor_name'][i] = instructor_name
    except (IndexError, KeyError) as e:
        pass

    # save any new records to the main instructors file:
    instructors.to_csv('./data/instructor_data/complete_instructors_list.csv', index=None)
    
    return diff_df


# find the latest classes and add them to the master file with all classes:
def get_class_diff():
    # get a list of all workout categories:
    wo_categories = s.get('https://api.onepeloton.com/api/v2/ride/archived?browse_category=cycling&page=0').json()
    categories_df = pd.DataFrame.from_dict(wo_categories['browse_categories'])
    
    # read master file with saved classes up to date:
    master_df = pd.read_csv('./data/class_data/master_classes.csv', low_memory=False)
    master_slug_ids_set = set(master_df['id'])
    
    # set empty df to contain the difference in records (new classes not in master file):
    diff_df = pd.DataFrame()
    
    # get the top url for all rides:
    rides_url = 'https://api.onepeloton.com/api/v2/ride/archived?browse_category&limit=100'

    # get the total number of class pages for the category:
    rides_dict = s.get(rides_url).json()
    page_count = rides_dict['page_count']

    # iterate through every page in until a class id in the master file is found:
    found = False
    try:
        for page_num in range(page_count + 1):
            # get url for category and specific page number:
            page_url = rides_url + '&page=' + str(page_num)

            #all classes in a given page:
            page_classes_df = pd.DataFrame.from_dict(s.get(page_url).json()['data'])
            for i, class_id in enumerate(page_classes_df['id']):
                if class_id not in master_slug_ids_set:
                    diff_df = pd.concat([diff_df, page_classes_df.iloc[[i]]])
                else:
                    print(f'class_id found in file: {class_id}')
                    found = True
                    break
            if found:
                break
    except KeyError as e:
        pass

    # check to see if there is any difference in the data:
    if len(diff_df) != 0:
        diff_df = diff_df.reset_index(drop=True)
        
        # preprocess diff_df before appending to master file:
        preprocessed_diff_df = preprocess_classes_data(diff_df)
        # return an updated master file:
        updated_master_df = pd.concat([master_df, preprocessed_diff_df])
        updated_master_df.drop_duplicates(subset=['id'], inplace=True)
        updated_master_df.sort_values(by='original_airtime', ascending=False, inplace=True)

        # check for number of records after:
        # total_records_master = len(updated_master_df)
        # total_rides_available = rides_dict['total']
        # print(f"total records in master file: {total_records_master}")
        # print(f"total rides available: {total_rides_available}")
    else:
        updated_master_df = master_df
        pass
    
    updated_master_df.to_csv('./data/class_data/master_classes.csv', index=None)


# looks for differences between instructor taken classes available online, versus the ones on file:
def get_instructor_workouts_diff(user_id, instructors_df):
    # get instructors list from API:
    instructors = instructors_df
    
    # get instructor name and prepare for file read:
    instructor_name = str(instructors.loc[instructors['user_id'] == user_id, 'name'].values[0]).replace(' ', '_')
    print(f"instructor name: {instructor_name}")
    
    # get page of workouts for specific instructors:
    workout_url = 'https://api.onepeloton.com/api/user/' + str(user_id) + '/workouts?limit=100'
    
    try:
        # get file of already saved workouts for specific instructor:
        instructor_workouts = pd.read_csv('./data/instructor_data/instructor_workouts/' + instructor_name + '.csv')
        
        try:
            # class ids:
            class_ids_lst = set(instructor_workouts['id'])
            
            # get the total number of class pages for instructor workouts:
            workout_dict = s.get(workout_url).json()
            page_count = workout_dict['page_count']

            # set empty df to all updates:
            diff_df = pd.DataFrame()
            
            # check to see if class id exists in file, if found, break:
            found = False
            for page_num in range(page_count + 1):
                # get page URL:
                page_url = workout_url + '&page=' + str(page_num)
                page_classes_df = pd.DataFrame.from_dict(s.get(page_url).json()['data'])
                
                # check every ID in the class page, and see if it exists alredy in file
                for i, class_id in enumerate(page_classes_df['id']):
                    if class_id not in class_ids_lst:
                        diff_df = pd.concat([diff_df, page_classes_df.iloc[[i]]])
                    else:
                        found = True
                        # print(f'class_id found in file: {class_id}')
                        break
                if found:
                    break
            
            # get instructor names for each class taken in the diff dataframe:
            diff_df = get_class_instructor_name(diff_df, instructors)

            # convert to timestamp:
            diff_df['workout_timestamp'] = unix_date_converter(list(diff_df['created_at']))
            # convert to day of week:
            diff_df['workout: day of week'] = pd.to_datetime(diff_df['workout_timestamp']).dt.day_name()
            # get time of day:
            diff_df['workout: time of day'] = time_of_day(diff_df, 'workout_timestamp')
            # get month and year i.e 'September 21'
            diff_df['workout: month and year'] = month_of_year(diff_df, 'workout_timestamp')
            
            # append diff df to file already on record:
            updated_workouts_df = pd.concat([instructor_workouts, diff_df])
            updated_workouts_df.drop_duplicates(subset=['id'], inplace=True)
            
            # save the updated df to file:
            updated_workouts_df.to_csv('./data/instructor_data/instructor_workouts/' + instructor_name + '.csv', index=None)
            
            # return updated_workouts_df

        except KeyError as e:
            pass
        
    except FileNotFoundError as e:
        print("File not Found")
        # TODO: if file is not found, look for instructor classes (if publicly available)
        
        
# updates all instructor taken workouts:
def update_instructor_workouts():
    # get list of instructors from API
    instructors_df = get_instructors_data()
    
    # loop through every user_id and update the workout data:
    for user_id in instructors_df['user_id']:
        get_instructor_workouts_diff(user_id, instructors_df)
        
