from streamlit import *
from streamlit_extras import *
from streamlit_lottie import *
from streamlit_option_menu import *
import pandas as pd 
from streamlit_extras.colored_header import colored_header
from streamlit_extras.metric_cards import style_metric_cards
import plotly.express as px
from streamlit_extras.keyboard_url import keyboard_to_url
from streamlit_lottie import st_lottie
import json as js
import pymongo as py
import requests
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine

pd.set_option('display.max_columns', None)

st.set_page_config(page_title='Airbnb Project By vinoth', layout="wide")

selected = option_menu(
    menu_title="airbnb",
    options=['Home', 'Insights', 'More', 'Thank You'],
    icons=['mic-fill', 'cash-stack', 'phone-flip', "handshake"],
    menu_icon='alexa',
    default_index=0,
)

def lottie(filepath):
    with open(filepath, 'r') as file:
        return js.load(file)
    
class data_collection:
    client = py.MongoClient("mongodb+srv://vinoth:Guvi8799@cluster0.mzh4mys.mongodb.net/?retryWrites=true&w=majority")
    db = client['sample_airbnb']
    col = db['listingsAndReviews']


class data_preprocessing:

    def primary():
        # direct feature columns
        data = []
        for i in data_collection.col.find({}, {'_id': 1, 'listing_url': 1, 'name': 1, 'property_type': 1, 'room_type': 1, 'bed_type': 1,
                                               'minimum_nights': 1, 'maximum_nights': 1, 'cancellation_policy': 1, 'accommodates': 1,
                                               'bedrooms': 1, 'beds': 1, 'number_of_reviews': 1, 'bathrooms': 1, 'price': 1,
                                               'cleaning_fee': 1, 'extra_people': 1, 'guests_included': 1, 'images.picture_url': 1,
                                               'review_scores.review_scores_rating': 1}):
            data.append(i)

        df_1 = pd.DataFrame(data)
        df_1['images'] = df_1['images'].apply(lambda x: x['picture_url'])
        df_1['review_scores'] = df_1['review_scores'].apply(
            lambda x: x.get('review_scores_rating', 0))

        # null value handling
        df_1['bedrooms'].fillna(0, inplace=True)
        df_1['beds'].fillna(0, inplace=True)
        df_1['bathrooms'].fillna(0, inplace=True)
        df_1['cleaning_fee'].fillna('Not Specified', inplace=True)

        # data types conversion
        df_1['minimum_nights'] = df_1['minimum_nights'].astype(int)
        df_1['maximum_nights'] = df_1['maximum_nights'].astype(int)
        df_1['bedrooms'] = df_1['bedrooms'].astype(int)
        df_1['beds'] = df_1['beds'].astype(int)
        df_1['bathrooms'] = df_1['bathrooms'].astype(str).astype(float)
        df_1['price'] = df_1['price'].astype(str).astype(float).astype(int)
        df_1['cleaning_fee'] = df_1['cleaning_fee'].apply(lambda x: int(
            float(str(x))) if x != 'Not Specified' else 'Not Specified')
        df_1['extra_people'] = df_1['extra_people'].astype(
            str).astype(float).astype(int)
        df_1['guests_included'] = df_1['guests_included'].astype(
            str).astype(int)

        return df_1

    def host():
        host = []
        for i in data_collection.col.find({}, {'_id': 1, 'host': 1}):
            host.append(i)

        df_host = pd.DataFrame(host)
        host_keys = list(df_host.iloc[0, 1].keys())
        host_keys.remove('host_about')

        # make nested dictionary to separate columns
        for i in host_keys:
            if i == 'host_response_time':
                df_host['host_response_time'] = df_host['host'].apply(
                    lambda x: x['host_response_time'] if 'host_response_time' in x else 'Not Specified')
            else:
                df_host[i] = df_host['host'].apply(
                    lambda x: x[i] if i in x and x[i] != '' else 'Not Specified')

        df_host.drop(columns=['host'], inplace=True)

        # data type conversion
        df_host['host_is_superhost'] = df_host['host_is_superhost'].map(
            {False: 'No', True: 'Yes'})
        df_host['host_has_profile_pic'] = df_host['host_has_profile_pic'].map(
            {False: 'No', True: 'Yes'})
        df_host['host_identity_verified'] = df_host['host_identity_verified'].map(
            {False: 'No', True: 'Yes'})

        return df_host

    def address():
        address = []
        for i in data_collection.col.find({}, {'_id': 1, 'address': 1}):
            address.append(i)

        df_address = pd.DataFrame(address)
        address_keys = list(df_address.iloc[0, 1].keys())

        # nested dicionary to separate columns
        for i in address_keys:
            if i == 'location':
                df_address['location_type'] = df_address['address'].apply(
                    lambda x: x['location']['type'])
                df_address['longitude'] = df_address['address'].apply(
                    lambda x: x['location']['coordinates'][0])
                df_address['latitude'] = df_address['address'].apply(
                    lambda x: x['location']['coordinates'][1])
                df_address['is_location_exact'] = df_address['address'].apply(
                    lambda x: x['location']['is_location_exact'])
            else:
                df_address[i] = df_address['address'].apply(
                    lambda x: x[i] if x[i] != '' else 'Not Specified')

        df_address.drop(columns=['address'], inplace=True)

        # bool data conversion to string
        df_address['is_location_exact'] = df_address['is_location_exact'].map(
            {False: 'No', True: 'Yes'})
        return df_address

    def availability():
        availability = []
        for i in data_collection.col.find({}, {'_id': 1, 'availability': 1}):
            availability.append(i)

        df_availability = pd.DataFrame(availability)
        availability_keys = list(df_availability.iloc[0, 1].keys())

        # nested dicionary to separate columns
        for i in availability_keys:
            df_availability['availability_30'] = df_availability['availability'].apply(
                lambda x: x['availability_30'])
            df_availability['availability_60'] = df_availability['availability'].apply(
                lambda x: x['availability_60'])
            df_availability['availability_90'] = df_availability['availability'].apply(
                lambda x: x['availability_90'])
            df_availability['availability_365'] = df_availability['availability'].apply(
                lambda x: x['availability_365'])

        df_availability.drop(columns=['availability'], inplace=True)
        return df_availability

    def amenities_sort(x):
        a = x
        a.sort(reverse=False)
        return a

    def amenities():
        amenities = []
        for i in data_collection.col.find({}, {'_id': 1, 'amenities': 1}):
            amenities.append(i)

        df_amenities = pd.DataFrame(amenities)

        # sort the list of amenities
        df_amenities['amenities'] = df_amenities['amenities'].apply(
            lambda x: data_preprocessing.amenities_sort(x))
        return df_amenities

    def merge_dataframe():
        df_1 = data_preprocessing.primary()
        df_host = data_preprocessing.host()
        df_address = data_preprocessing.address()
        df_availability = data_preprocessing.availability()
        df_amenities = data_preprocessing.amenities()

        df = pd.merge(df_1, df_host, on='_id')
        df = pd.merge(df, df_address, on='_id')
        df = pd.merge(df, df_availability, on='_id')
        df = pd.merge(df, df_amenities, on='_id')

        return df

class sql:
    def create_table_and_data_migration():

    
    
        # Connect to the MySQL server
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        
        # Create a new database and use
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS airbnb")

        # Close the cursor and database connection
        mycursor.close()
        mydb.close()

        engine = create_engine('mysql+mysqlconnector://root:vino8799@localhost/airbnb', echo=False)
        df = data_preprocessing.merge_dataframe()
        columns_to_drop = ['host_verifications', 'amenities']
        df.drop(columns=columns_to_drop, inplace=True)   

        df.to_sql('airbnb', engine, if_exists='replace', index=False, dtype={
            '_id': sqlalchemy.types.VARCHAR(length=255),
            'listing_url': sqlalchemy.types.VARCHAR(length=255),
            'name': sqlalchemy.types.VARCHAR(length=255),
            'property_type': sqlalchemy.types.VARCHAR(length=255),
            'room_type': sqlalchemy.types.VARCHAR(length=255),
            'bed_type': sqlalchemy.types.VARCHAR(length=255),
            'minimum_nights': sqlalchemy.types.INT,
            'maximum_nights': sqlalchemy.types.INT,
            'cancellation_policy': sqlalchemy.types.VARCHAR(length=255),
            'accommodates': sqlalchemy.types.INT,
            'bedrooms': sqlalchemy.types.INT,
            'beds': sqlalchemy.types.INT,
            'number_of_reviews': sqlalchemy.types.INT,
            'bathrooms': sqlalchemy.types.FLOAT,
            'price': sqlalchemy.types.INT,
            'cleaning_fee': sqlalchemy.types.VARCHAR(length=20),
            'extra_people': sqlalchemy.types.INT,
            'guests_included': sqlalchemy.types.INT,
            'images': sqlalchemy.types.TEXT,
            'review_scores': sqlalchemy.types.INT,
            'host_id': sqlalchemy.types.VARCHAR(length=255),
            'host_url': sqlalchemy.types.TEXT,
            'host_name': sqlalchemy.types.VARCHAR(length=255),
            'host_location': sqlalchemy.types.VARCHAR(length=255),
            'host_response_time': sqlalchemy.types.VARCHAR(length=255),
            'host_thumbnail_url': sqlalchemy.types.TEXT,
            'host_picture_url': sqlalchemy.types.TEXT,
            'host_neighbourhood': sqlalchemy.types.VARCHAR(length=255),
            'host_response_rate': sqlalchemy.types.VARCHAR(length=255),
            'host_is_superhost': sqlalchemy.types.VARCHAR(length=25),
            'host_has_profile_pic': sqlalchemy.types.VARCHAR(length=25),
            'host_identity_verified': sqlalchemy.types.VARCHAR(length=25),
            'host_listings_count': sqlalchemy.types.INT,
            'host_total_listings_count': sqlalchemy.types.INT,
            'street': sqlalchemy.types.VARCHAR(length=255),
            'suburb': sqlalchemy.types.VARCHAR(length=255),
            'government_area': sqlalchemy.types.VARCHAR(length=255),
            'market': sqlalchemy.types.VARCHAR(length=255),
            'country': sqlalchemy.types.VARCHAR(length=255),
            'country_code': sqlalchemy.types.VARCHAR(length=255),
            'location_type': sqlalchemy.types.VARCHAR(length=255),
            'longitude': sqlalchemy.types.FLOAT,
            'latitude': sqlalchemy.types.FLOAT,
            'is_location_exact': sqlalchemy.types.VARCHAR(length=25),
            'availability_30': sqlalchemy.types.INT,
            'availability_60': sqlalchemy.types.INT,
            'availability_90': sqlalchemy.types.INT,
            'availability_365': sqlalchemy.types.INT
            })
        

    def delete_table():
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""delete from airbnb;""")
        mydb.close()    


class plotly:
    def pie_chart(df, x, y, title, title_x=0.20):

        fig = px.pie(df, names=x, values=y, hole=0.5, title=title)

        fig.update_layout(title_x=title_x, title_font_size=22)

        fig.update_traces(text=df[y], textinfo='percent+value',
                          textposition='outside',
                          textfont=dict(color='white'))

        st.plotly_chart(fig, use_container_width=True)

    def horizontal_bar_chart(df, x, y, text, color, title, title_x=0.25):

        fig = px.bar(df, x=x, y=y, labels={x: '', y: ''}, title=title)

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        fig.update_layout(title_x=title_x, title_font_size=22)

        text_position = ['inside' if val >= max(
            df[x]) * 0.75 else 'outside' for val in df[x]]

        fig.update_traces(marker_color=color,
                          text=df[text],
                          textposition=text_position,
                          texttemplate='%{x}<br>%{text}',
                          textfont=dict(size=14),
                          insidetextfont=dict(color='white'),
                          textangle=0,
                          hovertemplate='%{x}<br>%{y}')

        st.plotly_chart(fig, use_container_width=True)

    def vertical_bar_chart(df, x, y, text, color, title, title_x=0.25):

        fig = px.bar(df, x=x, y=y, labels={x: '', y: ''}, title=title)

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        fig.update_layout(title_x=title_x, title_font_size=22)

        text_position = ['inside' if val >= max(
            df[y]) * 0.90 else 'outside' for val in df[y]]

        fig.update_traces(marker_color=color,
                          text=df[text],
                          textposition=text_position,
                          texttemplate='%{y}<br>%{text}',
                          textfont=dict(size=14),
                          insidetextfont=dict(color='white'),
                          textangle=0,
                          hovertemplate='%{x}<br>%{y}')

        st.plotly_chart(fig, use_container_width=True, height=100)

    def line_chart(df, x, y, text, textposition, color, title, title_x=0.25):

        fig = px.line(df, x=x, y=y, labels={
                      x: '', y: ''}, title=title, text=df[text])

        fig.update_layout(title_x=title_x, title_font_size=22)

        fig.update_traces(line=dict(color=color, width=3.5),
                          marker=dict(symbol='diamond', size=10),
                          texttemplate='%{x}<br>%{text}',
                          textfont=dict(size=13.5),
                          textposition=textposition,
                          hovertemplate='%{x}<br>%{y}')

        st.plotly_chart(fig, use_container_width=True, height=100)


class feature:
    def feature(column_name, order='count desc', limit=10):
        
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select distinct {column_name}, count({column_name}) as count
                       from airbnb
                       group by {column_name}
                       order by {order}
                       limit {limit};""")
        s = cursor.fetchall()
        i = [i for i in range(1, len(s)+1)]
        data = pd.DataFrame(s, columns=[column_name, 'count'], index=i)
        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
        data['percentage'] = data['count'].apply(
            lambda x: str('{:.2f}'.format(x/55.55)) + '%')
        data['y'] = data[column_name].apply(lambda x: str(x)+'`')
        return data

    def cleaning_fee():
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select distinct cleaning_fee, count(cleaning_fee) as count
                       from airbnb
                       where cleaning_fee != 'Not Specified'
                       group by cleaning_fee
                       order by count desc
                       limit 10;""")
        s = cursor.fetchall()
        i = [i for i in range(1, len(s)+1)]
        data = pd.DataFrame(s, columns=['cleaning_fee', 'count'], index=i)
        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
        data['percentage'] = data['count'].apply(
            lambda x: str('{:.2f}'.format(x/55.55)) + '%')
        data['y'] = data['cleaning_fee'].apply(lambda x: str(x)+'`')
        return data

    def location():
        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select host_id, country, longitude, latitude from airbnb group by host_id, country, longitude, latitude""")
        
        s = cursor.fetchall()
        i = [i for i in range(1, len(s)+1)]
        data = pd.DataFrame(
            s, columns=['Host ID', 'Country', 'Longitude', 'Latitude'], index=i)
        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
        return data

    def feature_analysis():

        # vertical_bar chart
        property_type = feature.feature('property_type')
        plotly.vertical_bar_chart(df=property_type, x='property_type', y='count',
                                  
                                  text='percentage', color='#00BFFF', title='Property Type', title_x=0.43)

        # line & pie chart
        col1, col2 ,col3 = st.columns(3)
        with col1:
            bed_type = feature.feature('bed_type')
            plotly.line_chart(df=bed_type, y='bed_type', x='count', text='percentage', color='#00BFFF',
                              textposition=[
                                  'top center', 'bottom center', 'middle right', 'middle right', 'middle right'],
                              title='Bed Type', title_x=0.50)
        with col3:
            room_type = feature.feature('room_type')
            plotly.pie_chart(df=room_type, x='room_type',
                             y='count', title='Room Type', title_x=0.30)

        # vertical_bar chart
        tab1, tab2 = st.tabs(['Minimum Nights', 'Maximum Nights'])
        with tab1:
            minimum_nights = feature.feature('minimum_nights')
            plotly.vertical_bar_chart(df=minimum_nights, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Nights', title_x=0.43)
        with tab2:
            maximum_nights = feature.feature('maximum_nights')
            plotly.vertical_bar_chart(df=maximum_nights, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Nights', title_x=0.43)

        # line chart
        cancellation_policy = feature.feature('cancellation_policy')
        plotly.line_chart(df=cancellation_policy, y='cancellation_policy', x='count', text='percentage', color='#00BFFF',
                          textposition=['top center', 'top right',
                                        'top center', 'bottom center', 'middle right'],
                          title='Cancellation Policy', title_x=0.43)

        # vertical_bar chart
        accommodates = feature.feature('accommodates')
        plotly.vertical_bar_chart(df=accommodates, x='y', y='count', text='percentage',
                                  color='#00BFFF', title='Accommodates', title_x=0.43)

        # vertical_bar chart
        tab1, tab2, tab3 = st.tabs(['Bedrooms', 'Beds', 'Bathrooms'])
        with tab1:
            bedrooms = feature.feature('bedrooms')
            plotly.vertical_bar_chart(df=bedrooms, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Bedrooms', title_x=0.43)
        with tab2:
            beds = feature.feature('beds')
            plotly.vertical_bar_chart(df=beds, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Beds', title_x=0.43)
        with tab3:
            bathrooms = feature.feature('bathrooms')
            plotly.vertical_bar_chart(df=bathrooms, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Bathrooms', title_x=0.43)

        # vertical_bar chart
        tab1, tab2, tab3, tab4 = st.tabs(
            ['Price', 'Cleaning Fee', 'Extra People', 'Guests Included'])
        with tab1:
            price = feature.feature('price')
            plotly.vertical_bar_chart(df=price, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Price', title_x=0.43)
        with tab2:
            cleaning_fee = feature.cleaning_fee()
            plotly.vertical_bar_chart(df=cleaning_fee, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Cleaning Fee', title_x=0.43)
        with tab3:
            extra_people = feature.feature('extra_people')
            plotly.vertical_bar_chart(df=extra_people, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Extra People', title_x=0.43)
        with tab4:
            guests_included = feature.feature('guests_included')
            plotly.vertical_bar_chart(df=guests_included, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Guests Included', title_x=0.43)

       
       
        # pie chart
        tab1, tab2, tab3 = st.tabs(
            ['Host is Superhost', 'Host has Profile Picture', 'Host Identity Verified'])
        with tab1:
            host_is_superhost = feature.feature('host_is_superhost')
            plotly.pie_chart(df=host_is_superhost, x='host_is_superhost',
                             y='count', title='Host is Superhost', title_x=0.39)
        with tab2:
            host_has_profile_pic = feature.feature('host_has_profile_pic')
            plotly.pie_chart(df=host_has_profile_pic, x='host_has_profile_pic',
                             y='count', title='Host has Profile Picture', title_x=0.37)
        with tab3:
            host_identity_verified = feature.feature('host_identity_verified')
            plotly.pie_chart(df=host_identity_verified, x='host_identity_verified',
                             y='count', title='Host Identity Verified', title_x=0.37)

        # vertical_bar,pie,map chart
        tab1, tab2, tab3 = st.tabs(['Market', 'Country', 'Location Exact'])
        with tab1:
            market = feature.feature('market', limit=12)
            plotly.vertical_bar_chart(df=market, x='market', y='count', text='percentage',
                                      color='#00BFFF', title='Market', title_x=0.43)
        with tab2:
            country = feature.feature('country')
            plotly.vertical_bar_chart(df=country, x='country', y='count', text='percentage',
                                      color='#00BFFF', title='Country', title_x=0.43)
        with tab3:
            is_location_exact = feature.feature('is_location_exact')
            plotly.pie_chart(df=is_location_exact, x='is_location_exact', y='count',
                             title='Location Exact', title_x=0.37)

        # vertical_bar,pie,map chart
        tab1, tab2, tab3, tab4 = st.tabs(['Availability 30', 'Availability 60',
                                          'Availability 90', 'Availability 365'])
        with tab1:
            availability_30 = feature.feature('availability_30')
            plotly.vertical_bar_chart(df=availability_30, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability 30', title_x=0.45)
        with tab2:
            availability_60 = feature.feature('availability_60')
            plotly.vertical_bar_chart(df=availability_60, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability 60', title_x=0.45)
        with tab3:
            availability_90 = feature.feature('availability_90')
            plotly.vertical_bar_chart(df=availability_90, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability 90', title_x=0.45)
        with tab4:
            availability_365 = feature.feature('availability_365')
            plotly.vertical_bar_chart(df=availability_365, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability 365', title_x=0.45)

        # vertical_bar,pie,map chart
        tab1, tab2, tab3 = st.tabs(
            ['Number of Reviews', 'Maximum Number of Reviews', 'Review Scores'])
        with tab1:
            number_of_reviews = feature.feature('number_of_reviews')
            plotly.vertical_bar_chart(df=number_of_reviews, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Number of Reviews', title_x=0.43)
        with tab2:
            max_number_of_reviews = feature.feature(
                'number_of_reviews', order='number_of_reviews desc')
            plotly.vertical_bar_chart(df=max_number_of_reviews, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Number of Reviews', title_x=0.35)
        with tab3:
            review_scores = feature.feature('review_scores')
            plotly.vertical_bar_chart(df=review_scores, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Review Scores', title_x=0.43) 
            
class host:
    def countries_list():

        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select distinct country
                       from airbnb
                       order by country asc;""")
        s = cursor.fetchall()
        i = [i for i in range(1, len(s)+1)]
        data = pd.DataFrame(s, columns=['Country'], index=i)
        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
        return data

    def column_value(country, column_name, limit=10):
        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select {column_name}, count({column_name}) as count
                       from airbnb
                       where country='{country}'
                       group by {column_name}
                       order by count desc
                       limit {limit};""")
       
        s = cursor.fetchall()
        data = pd.DataFrame(s, columns=[column_name, 'count'])
        return data[column_name].values.tolist()

    def column_value_names(country, column_name, order='desc', limit=10):
        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select {column_name}, count({column_name}) as count
                       from airbnb
                       where country='{country}'
                       group by {column_name}
                       order by {column_name} {order}
                       limit {limit};""")
        s = cursor.fetchall()
        data = pd.DataFrame(s, columns=[column_name, 'count'])
        return data[column_name].values.tolist()

    def column_value_count_not_specified(country, column_name, limit=10):
        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select {column_name}, count({column_name}) as count
                       from airbnb
                       where country='{country}' and {column_name}!='Not Specified'
                       group by {column_name}
                       order by count desc
                       limit {limit};""")
        s = cursor.fetchall()
        data = pd.DataFrame(s, columns=[column_name, 'count'])
        return data[column_name].values.tolist()

    def host(country, column_name, column_value, limit=10):
        mydb = mysql.connector.connect(

            host = "localhost",
            user = "root",
            password = "vino8799",
            database = "airbnb"
            )
        cursor = mydb.cursor()
        cursor.execute(f"""select distinct host_id, count(host_id) as count
                       from airbnb
                       where country='{country}' and {column_name}='{column_value}'
                       group by host_id
                       order by count desc
                       limit {limit};""")
        s = cursor.fetchall()
        i = [i for i in range(1, len(s)+1)]
        data = pd.DataFrame(s, columns=['host_id', 'count'], index=i)
        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
        data['percentage'] = data['count'].apply(
            lambda x: str('{:.2f}'.format(x/55.55)) + '%')
        data['y'] = data['host_id'].apply(lambda x: str(x)+'`')
        return data

    def main(values, label):
        col1, col2, col3 = st.columns(3)
        with col1:

            a = str(values) + '_column_value_list'
            b = str(values) + '_column_value'

            a = host.column_value(country=country, column_name=values)
            b = st.selectbox(label=label, options=a)

            values = host.host(country=country, column_name=values,
                               column_value=b)
            return values

    def main_min(values, label):
        col1, col2, col3 = st.columns(3)
        with col1:
            a = str(values) + '_column_value_list'
            b = str(values) + '_column_value'

            a = host.column_value_names(
                country=country, column_name=values, order='asc')
            b = st.selectbox(label=label, options=a)

            values = host.host(country=country, column_name=values,
                               column_value=b)
            return values

    def main_max(values, label):
        col1, col2, col3 = st.columns(3)
        with col1:
            a = str(values) + '_column_value_list'
            b = str(values) + '_column_value'

            a = host.column_value_names(
                country=country, column_name=values, order='desc')
            b = st.selectbox(label=label, options=a)

            values = host.host(country=country, column_name=values,
                               column_value=b)
            return values

    def not_specified(values, label):
        col1, col2, col3 = st.columns(3)
        with col1:
            a = str(values) + '_column_value_list'
            b = str(values) + '_column_value'

            a = host.column_value_count_not_specified(
                country=country, column_name=values)
            b = st.selectbox(label=label, options=a)

            values = host.host(country=country, column_name=values,
                               column_value=b)
            return values

    def host_analysis():

        # vertical_bar chart
        property_type = host.main(
            values='property_type', label='Property Type')
        plotly.vertical_bar_chart(df=property_type, x='y', y='count', text='percentage',
                                  color='#00BFFF', title='Property Type', title_x=0.45)

        # vertical_bar chart
        tab1, tab2 = st.tabs(['Room Type', 'Bed Type'])
        with tab1:
            room_type = host.main(values='room_type', label='')
            plotly.vertical_bar_chart(df=room_type, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Room Type', title_x=0.45)
        with tab2:
            bed_type = host.main(values='bed_type', label='')
            plotly.vertical_bar_chart(df=bed_type, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Bed Type', title_x=0.45)

        # vertical_bar chart
        tab1, tab2 = st.tabs(['Minimum Nights', 'Maximum Nights'])
        with tab1:
            minimum_nights = host.main(values='minimum_nights', label='')
            plotly.vertical_bar_chart(df=minimum_nights, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Nights', title_x=0.45)
        with tab2:
            maximum_nights = host.main(values='maximum_nights', label='')
            plotly.vertical_bar_chart(df=maximum_nights, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Nights', title_x=0.45)

        # vertical_bar chart
        cancellation_policy = host.main(
            values='cancellation_policy', label='Cancellation Policy')
        plotly.vertical_bar_chart(df=cancellation_policy, x='y', y='count', text='percentage',
                                  color='#00BFFF', title='Cancellation Policy', title_x=0.45)

        # vertical_bar chart
        tab1, tab2 = st.tabs(
            ['Minimum Accommodates', 'Maximum Accommodates'])
        with tab1:
            minimum_accommodates = host.main_min(
                values='accommodates', label='')
            plotly.vertical_bar_chart(df=minimum_accommodates, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Accommodates', title_x=0.45)
        with tab2:
            maximum_accommodates = host.main_max(
                values='accommodates', label='')
            plotly.vertical_bar_chart(df=maximum_accommodates, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Accommodates', title_x=0.45)

        # vertical_bar chart
        tab1, tab2, tab3, tab4 = st.tabs(
            ['Bedrooms', 'Minimum Beds', 'Maximum Beds', 'Bathrooms'])
        with tab1:
            bedrooms = host.main(values='bedrooms', label='')
            plotly.vertical_bar_chart(df=bedrooms, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Bedrooms', title_x=0.45)
        with tab2:
            
            minimum_beds = host.main_min(values='beds', label='')
            plotly.vertical_bar_chart(df=minimum_beds, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Beds', title_x=0.45)
        with tab3:
            maximum_beds = host.main_max(values='beds', label='')
            plotly.vertical_bar_chart(df=maximum_beds, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Beds', title_x=0.45)
        with tab4:
            bathrooms = host.main(values='bathrooms', label='')
            plotly.vertical_bar_chart(df=bathrooms, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Bathrooms', title_x=0.45)

        # vertical_bar chart
        tab1, tab2, tab3, tab4 = st.tabs(
            ['Price', 'Minimum Price', 'Maximum Price', 'Cleaning Fee'])
        with tab1:
            price = host.main(values='price', label='')
            plotly.vertical_bar_chart(df=price, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Price', title_x=0.45)
        with tab2:
            minimum_price = host.main_min(values='price', label='')
            plotly.vertical_bar_chart(df=minimum_price, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Price', title_x=0.45)
        with tab3:
            maximum_price = host.main_max(values='price', label='')
            plotly.vertical_bar_chart(df=maximum_price, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum price', title_x=0.45)
        with tab4:
            cleaning_fee = host.not_specified(
                values='cleaning_fee', label='')
            plotly.vertical_bar_chart(df=cleaning_fee, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Cleaning Fee', title_x=0.45)

        # vertical_bar chart
        tab1, tab2, tab3, tab4 = st.tabs(['Guests Included', 'Cost at Extra People',
                                          'Minimum Cost at Extra People', 'Maximum Cost at Extra People'])
        with tab1:
            guests_included = host.main(values='guests_included', label='')
            plotly.vertical_bar_chart(df=guests_included, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Guests Included', title_x=0.45)
        with tab2:
            extra_people = host.main(values='extra_people', label='')
            plotly.vertical_bar_chart(df=extra_people, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Cost at Extra People', title_x=0.45)
        with tab3:
            extra_people_min_cost = host.main_min(
                values='extra_people', label='')
            plotly.vertical_bar_chart(df=extra_people_min_cost, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Minimum Cost at Extra People', title_x=0.45)
        with tab4:
            extra_people_max_cost = host.main_max(
                values='extra_people', label='')
            plotly.vertical_bar_chart(df=extra_people_max_cost, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Maximum Cost at Extra People', title_x=0.45)


        # vertical_bar chart
        tab1, tab2, tab3, tab4 = st.tabs(
            ['Availability 30', 'Availability 60', 'Availability 90', 'Availability 365'])
        with tab1:
            availability_30 = host.main_max(
                values='availability_30', label='')
            plotly.vertical_bar_chart(df=availability_30, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability of Next 30 Days', title_x=0.45)
        with tab2:
            availability_60 = host.main_max(
                values='availability_60', label='')
            plotly.vertical_bar_chart(df=availability_60, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability of Next 60 Days', title_x=0.45)
        with tab3:
            availability_90 = host.main_max(
                values='availability_90', label='')
            plotly.vertical_bar_chart(df=availability_90, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability of Next 90 Days', title_x=0.45)
        with tab4:
            availability_365 = host.main_max(
                values='availability_365', label='')
            plotly.vertical_bar_chart(df=availability_365, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Availability of Next 365 Days', title_x=0.45)

        # vertical_bar chart
        tab1, tab2 = st.tabs(['Number of Reviews', 'Review Scores'])
        with tab1:
            number_of_reviews = host.main_max(
                values='number_of_reviews', label='')
            plotly.vertical_bar_chart(df=number_of_reviews, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Number of Reviews', title_x=0.45)
        with tab2:
            review_scores = host.main_max(values='review_scores', label='')
            plotly.vertical_bar_chart(df=review_scores, x='y', y='count', text='percentage',
                                      color='#00BFFF', title='Review Scores', title_x=0.45)


st.write('')     


if selected == "Insights":
    option = option_menu(menu_title='', options=['Migrating to SQL', 'Features Analysis'],
                         icons=['database-fill', 'list-task', 'person-circle', 'sign-turn-right-fill'],
                         default_index=0, orientation="horizontal")
    
    if button and option == 'Migrating to SQL':
        st.write('')
        col1, col2, col3 = st.columns([0.26, 0.48, 0.26])
        with col2:
            button = st.button(label='Submit')
        sql.create_table_and_data_migration()
        st.success('Successfully Data Migrated to SQL Database')

    elif option == 'Features Analysis':
        col1,col2,col3=st.columns(3)
        with col2:
            file = lottie(r"D:\vk_project\lottiite animation\zoom_search.json")
            st_lottie(file,height=300,key=None)
        st.write('')
        feature.feature_analysis()


if selected == "More":

    def load_lottieurl(url):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    
    with st.container():
        st.subheader('Host Analysis')
        col1,col2=st.columns(2)
        with col1:
            countries_list = host.countries_list()
            country = st.selectbox(label='Country', options=countries_list)
        with col2:
            file = lottie(r"D:\vk_project\lottiite animation\room booking.json")
            st_lottie(file,height=300,key=None) 
        if country:
            host.host_analysis()

if selected == "Thank You":
    with st.container():
        col1,col2,col3,col4,col5=st.columns(5)
        with col3:
            file = lottie(r"D:\vk_project\lottiite animation\thnak you.json")
            st_lottie(file,height=500,key=None)
        with col3:
            st.write("👉[explore website >](https://www.airbnb.co.in/)")        


                        
if selected == 'Home':

    def load_lottieurl(url):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    # Use local CSS
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    local_css(r"D:\vk_project\Air_bnb\style.css")

    lottie_coding = lottie(r"D:\vk_project\lottiite animation\intro vk.json")


    # ---- HEADER SECTION -----``
    with st.container():
        col1,col2=st.columns(2)
        with col1:
            st.markdown( f"<h1 style='font-size: 70px;'><span style='color: #00BFFF;'> Hi,  </span><span style='color: white;'> I am vinoth kumar </h1>",unsafe_allow_html=True)
            st.markdown(
                f"<h1 style='font-size: 40px;'><span style='color: white;'>A Data Scientist,</span><span style='color: #00BFFF;'> From India</span></h1>",
                unsafe_allow_html=True
                )
            st.write(f'<h1 style="color:#B0C4DE; font-size: 20px;">A data scientist skilled in extracting actionable insights from complex datasets, adept at employing advanced analytics and machine learning techniques to solve real-world problems. Proficient in Python, statistical modeling, and data visualization, with a strong commitment to driving data-driven decision-making.</h1>', unsafe_allow_html=True)    

            st.write("[view more projects >](https://github.com/vinothkumarpy?tab=repositories)")

        with col2:
            st_lottie(lottie_coding, height=400, key="coding")    

    # ---- WHAT I DO ----
    with st.container():
        st.write("---")
        col1,col2,col3=st.columns(3)

        with col1:
            file = lottie(r"D:\vk_project\lottiite animation\data science.json")
            st_lottie(file,height=500,key=None)

        with col2:
            st.markdown( f"<h1 style='font-size: 70px;'><span style='color: #00BFFF;'> WHAT  </span><span style='color: white;'> I DO </h1>",unsafe_allow_html=True)
        
        with col3:
            file = lottie(r"D:\vk_project\lottiite animation\working with data set.json")
            st_lottie(file,height=500,key=None)    

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'>Data  </span><span style='color: white;'>Collection</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Gathered Airbnb data from diverse sources, meticulously curating information</h1>', unsafe_allow_html=True)
    

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> Data  </span><span style='color: white;'>Preprocessing</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Conducted thorough cleaning and preparation to refine data for analysis.</h1>', unsafe_allow_html=True) 

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> ETL  </span><span style='color: white;'>(Extract, Transform, Load)</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Transformed raw data from MongoDB into structured and meaningful DataFrames.</h1>', unsafe_allow_html=True)

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> Exploratory  </span><span style='color: white;'>Preprocessing</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Delved deep into the Airbnb dataset, unraveling insights through detailed analysis and captivating visualizations.</h1>', unsafe_allow_html=True)

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> Interactive  </span><span style='color: white;'>Streamlit UI</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Crafted an engaging and user-friendly interface for seamless data exploration and presentation.</h1>', unsafe_allow_html=True)

        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> Data  </span><span style='color: white;'>Preprocessing</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">Conducted thorough cleaning and preparation to refine data for analysis.</h1>', unsafe_allow_html=True)   

        st.markdown("[🔗 GitHub Repo >](https://github.com/vinothkumarpy/AirBnb)")    



    with st.container():
        st.write("---")
        st.markdown( f"<h1 style='font-size: 40px;'><span style='color: #00BFFF;'> Used-Tech  </span><span style='color: white;'>& Skills</h1>",unsafe_allow_html=True)

        col1,col2,col3 =st.columns(3)
        with col1:
            file = lottie(r"D:\vk_project\lottiite animation\python.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>python</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)

            file = lottie(r"D:\vk_project\lottiite animation\Data cleaning.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Data Cleaning</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)


            file = lottie(r"D:\vk_project\lottiite animation\database.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>DataBase</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)

        with col2:
            file = lottie(r"D:\vk_project\lottiite animation\Mongo.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Mongo-DB</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)


            file = lottie(r"D:\vk_project\lottiite animation\analyis.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Data visualization</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)

            file = lottie(r"D:\vk_project\lottiite animation\frame work.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Web application development with Streamlit</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)

        with col3:    
            file = lottie(r"D:\vk_project\lottiite animation\data collection.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Data Collection</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)


            file = lottie(r"D:\vk_project\lottiite animation\data_exploaration.json")
            st.markdown("<h1 style='color: #00BFFF; text-align: center; font-size: 30px;'>Data Exploaration</h1>", unsafe_allow_html=True)
            st_lottie(file,height=200,key=None)
       

    # ---- PROJECTS ----
    with st.container():
        st.write("---")
        st.markdown( f"<h1 style='font-size: 70px;'><span style='color: #00BFFF;'> About  </span><span style='color: white;'> Projects </h1>",unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            file = lottie(r"D:\vk_project\lottiite animation\airbnb.json")
            st_lottie(file,height=300,key=None)
        with col2:
            st.write("##")
            st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">The Airbnb Data Analysis and Visualization project is a comprehensive data exploration and presentation effort. It involves data collection, preprocessing, ETL work, and the creation of an interactive Streamlit user interface. The project aims to provide insights and make Airbnb data more accessible and understandable.</h1>', unsafe_allow_html=True)
        st.markdown( f"<h1 style='font-size: 70px;'><span style='color: #00BFFF;'> Re</span><span style='color: white;'>sults</h1>",unsafe_allow_html=True)
        st.write(f'<h1 style="color:#B0C4DE; font-size: 30px;">The project provides a user-friendly interface for exploring Airbnb data.Insights and trends in the Airbnb market are presented through interactive charts and visualizations.Data is cleaned, organized, and ready for further analysis.</h1>', unsafe_allow_html=True)    
        

    # ---- CONTACT ----
    with st.container():
        st.write("---")
        st.markdown( f"<h1 style='font-size: 70px;'><span style='color: #00BFFF;'> Get In Touch  </span><span style='color: white;'> With Me </h1>",unsafe_allow_html=True)
        st.write("##")

        # Documention: https://formsubmit.co/ !!! CHANGE EMAIL ADDRESS !!!
        contact_form = """
        <form action="https://formsubmit.co/vinoharish8799@gmail.com" method="POST">
            <input type="hidden" name="_captcha" value="false">
            <input type="text" name="name" placeholder="Your name" required>
            <input type="email" name="email" placeholder="Your email" required>
            <textarea name="message" placeholder="Your message here" required></textarea>
            <button type="submit" style="background-color: #00BFFF; color: white;">Send</button>
        </form>
        """
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown(contact_form, unsafe_allow_html=True)
        with right_column:
            st.empty()