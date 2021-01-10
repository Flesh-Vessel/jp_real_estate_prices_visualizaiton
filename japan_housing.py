import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from confirm_button_hack import cache_on_button_press

st.set_page_config(
    page_title='Japanese Real Estate Prices)',
    layout='centered',
    initial_sidebar_state='expanded',
)

pd.options.display.float_format = '{:.0f}'.format


@st.cache
def load_data():
    df = pd.DataFrame()
    for filename in ['data/data01.csv', 'data/data02.csv', 'data/data03.csv']:
        temp = pd.read_csv(filename, engine='c')
        df = pd.concat([df, temp])
    return df


@cache_on_button_press('Show price trends')
def get_assessment(df, your_price, muni_assess, type, area,
                   time_to_nearest_station, land_shape, age_of_building,
                   structure, direction):

    with st.spinner('Wait for a moment...'):
        df_assess = df.copy()
        #TODO delete debug message
        #st.write(df_assess.shape[0])

        if len(list(muni_assess)) != 0:
            mask = df_assess['Municipality'].isin(muni_assess)
            df_assess = df_assess[mask]

        if len(list(type)) != 0:
            mask = df_assess['Type'].isin(type)
            df_assess = df_assess[mask]

        if len(list(area)) != 0:
            df_assess = df_assess[df_assess['Area'] != 'unknown']
            df_assess = df_assess[(df_assess['Area'].astype(float) >= area[0])
                                  &
                                  (df_assess['Area'].astype(float) <= area[1])]

        if len(list(time_to_nearest_station)) != 0:
            df_assess = df_assess[
                df_assess['MinTimeToNearestStation'] != 'unknown']
            df_assess = df_assess[
                (df_assess['MinTimeToNearestStation'].astype(float) >=
                 time_to_nearest_station[0])
                & (df_assess['MinTimeToNearestStation'].astype(float) <=
                   time_to_nearest_station[1])]

        if len(list(land_shape)) != 0:
            mask = df_assess['LandShape'].isin(land_shape)
            df_assess = df_assess[mask]

        if len(list(age_of_building)) != 0:
            df_assess = df_assess[df_assess['AgeOfBuilding'] != 'unknown']
            df_assess = df_assess[(
                df_assess['AgeOfBuilding'].astype(float) >= age_of_building[0])
                                  & (df_assess['AgeOfBuilding'].astype(float)
                                     <= age_of_building[1])]

        if len(list(structure)) != 0:
            mask = df_assess['Structure'].isin(structure)
            df_assess = df_assess[mask]

        if len(list(direction)) != 0:
            mask = df_assess['Direction'].isin(direction)
            df_assess = df_assess[mask]
        st.write(df_assess.shape[0], 'samples match your conditions.')
        df_assess = df_assess[['Year', 'PricePerM2']].groupby(
            ['Year']).quantile(
                q=[0, 0.25, 0.5, 0.75, 1]).reset_index().sort_values(by='Year')

        maximum = df_assess.query('level_1==1')
        third_quartile = df_assess.query('level_1==0.75')
        median = df_assess.query('level_1==0.5')
        second_quartile = df_assess.query('level_1==0.25')
        minimum = df_assess.query('level_1==0')

        return {
            'your_price': your_price,
            'maximum': maximum,
            'third_quartile': third_quartile,
            'median': median,
            'second_quartile': second_quartile,
            'minimum': minimum,
        }


df = load_data()

st.title('Japanese Real Estate Prices')
st.write(
    'This dashboard aims to provide an intuitive view of real estate transaction prices in Japan from 2005 to 2019.\
    You can also see the price trends under some conditions to determine if a price of a particular house is reasonable or not. \
    Move to expanders below to explore data or see price trends.')

#data_load_state = st.text('データをロード中...')
#st.spinner()

with st.beta_expander("Explore data", expanded=True):
    pref = df['Prefecture'].unique()
    muni = df['Municipality'].unique()
    len_pref, len_muni = len(pref), len(muni)

    pref_selected = st.multiselect('Filter by Prefecture', pref)
    muni_selected = st.multiselect('Filter by Municipality', muni)

    def mask_logical_sum(mask1, mask2):
        temp = (mask1 == True) | (mask2 == True)
        return temp

    if len(pref_selected) != 0 or len(muni_selected) != 0:
        mask_pref = df['Prefecture'].isin(pref_selected)
        mask_muni = df['Municipality'].isin(muni_selected)
        mask = mask_logical_sum(mask_pref, mask_muni)

        df_for_graph = df[mask]
        df_for_graph = df_for_graph[[
            'Year', 'Prefecture', 'Municipality', 'PricePerM2'
        ]].groupby(['Year', 'Prefecture',
                    'Municipality']).median().reset_index()

        bar = px.bar(df_for_graph[df_for_graph['Year'] == 2019].sort_values(
            by='PricePerM2', ascending=False),
                     x='Municipality',
                     y='PricePerM2',
                     height=300,
                     title='Average Unit Price by Municipality in 2019')

        line = px.line(
            df_for_graph.sort_values(by='Year', ascending=True),
            x='Year',
            y='PricePerM2',
            color='Municipality',
            hover_data=["Prefecture", "Municipality"],
            height=500,
            title='Average Unit Price by Municipality from 2005 to 2019')

        st.write(bar)
        st.write(line)

    else:
        df_for_graph = df[['Year', 'Prefecture',
                           'PricePerM2']].groupby(['Year', 'Prefecture'
                                                   ]).median().reset_index()

        bar = px.bar(df_for_graph[df_for_graph['Year'] == 2019].sort_values(
            by='PricePerM2', ascending=False),
                     x='Prefecture',
                     y='PricePerM2',
                     height=300)

        line = px.line(df_for_graph.sort_values(by='Year', ascending=True),
                       x='Year',
                       y='PricePerM2',
                       color='Prefecture',
                       hover_data=["Prefecture"],
                       height=500)
        st.write(bar)
        st.write(line)

with st.beta_expander("Show price trends", expanded=True):
    st.write('Set conditions and click "Show price trends" button below.')
    col1, col2 = st.beta_columns(2)
    your_price = col1.number_input('Enter Your Unit Price (JPY/M2)', 500000)
    muni_assess = col1.multiselect('Municipality',
                                   list(df['Municipality'].unique()))
    type = col1.multiselect('Type', list(df['Type'].unique()))
    area = col1.select_slider('Area', range(0, 301, 10), (0, 250))

    time_to_nearest_station = col2.select_slider(
        'Time to nearest station.(minutes)', range(0, 160, 5), (0, 10))

    land_shape = col2.multiselect('Land shape', list(df['LandShape'].unique()))
    age_of_building = col2.select_slider('Age of buiding', range(0, 51),
                                         (0, 20))
    structure = col2.multiselect('Structure', list(df['Structure'].unique()))
    direction = col2.multiselect('Direction', list(df['Direction'].unique()))

    val = get_assessment(df, your_price, muni_assess, type, area,
                         time_to_nearest_station, land_shape, age_of_building,
                         structure, direction)

    fig = go.Figure([
        go.Scatter(name='Median',
                   x=val['median']['Year'],
                   y=val['median']['PricePerM2'],
                   mode='lines',
                   marker=dict(color="#444"),
                   line=dict(color='rgb(31, 119, 180)'),
                   showlegend=False),
        go.Scatter(name='Maximum',
                   x=val['maximum']['Year'],
                   y=val['maximum']['PricePerM2'],
                   mode='lines',
                   marker=dict(color="#444"),
                   line=dict(width=0),
                   showlegend=False),
        go.Scatter(name='Minimum',
                   x=val['minimum']['Year'],
                   y=val['minimum']['PricePerM2'],
                   marker=dict(color="#444"),
                   line=dict(width=0),
                   mode='lines',
                   fillcolor='rgba(68, 68, 68, 0.3)',
                   fill='tonexty',
                   showlegend=False),
        go.Scatter(name='Third Quartile',
                   x=val['third_quartile']['Year'],
                   y=val['third_quartile']['PricePerM2'],
                   mode='lines',
                   marker=dict(color="#444"),
                   line=dict(width=0),
                   showlegend=False),
        go.Scatter(name='Second Quartile',
                   x=val['second_quartile']['Year'],
                   y=val['second_quartile']['PricePerM2'],
                   mode='lines',
                   marker=dict(color="#444"),
                   fillcolor='rgba(232, 213, 215, 0.3)',
                   fill='tonexty',
                   line=dict(width=0),
                   showlegend=False),
        go.Scatter(name='Your Price',
                   x=val['minimum']['Year'],
                   y=pd.Series([your_price] * len(val['minimum']['Year'])),
                   marker=dict(color="red"),
                   line=dict(width=1),
                   mode='lines',
                   showlegend=False),
    ],
                    layout=go.Layout(height=600, width=800))
    fig.update_layout(yaxis_title='Unit Price (JPY/M2)',
                      title='Unit Price Quartiles of selected conditions',
                      hovermode="x")
    st.write(fig)

    c1, c2, c3 = st.beta_columns(3)
    c1.write('Maximum Values')
    c1.table(val['maximum'][['Year', 'PricePerM2'
                             ]].style.format({'PricePerM2': "{:,.0f}"}))

    c2.write('Median Values')
    c2.table(val['median'][['Year', 'PricePerM2'
                            ]].style.format({'PricePerM2': "{:,.0f}"}))

    c3.write('Minimum Values')
    c3.table(val['minimum'][['Year', 'PricePerM2'
                             ]].style.format({'PricePerM2': "{:,.0f}"}))

#Credit
components.html(
    '<font size="2" color="#828282">The data used are <a href="https://www.kaggle.com/nishiodens/japan-real-estate-transaction-prices">Japan Real Estate Prices (Kaggle)</a> which is cleaned dataset originally published by Bureau Ministry of Land, Infrastructure, Transport and Tourism in Japan.<br>©2020 Fan Jiang</font>'
)