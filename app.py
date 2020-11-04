# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#     "Amount": [4, 1, 2, 2, 4, 5],
#     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })

gauge_info = pd.read_csv("data/elev.txt", sep = '\t')
latlon = ['mw_name','lat', 'lng']
gauge_info = gauge_info[latlon]
gauge_info = gauge_info.append({'mw_name': 'Cosumnes River Flow at Michigan Bar', 'lat': 38.500012,'lng': -121.045610}, ignore_index=True)


# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

### map
map_fig = px.scatter_mapbox(gauge_info, lat="lat", lon="lng", hover_name="mw_name", 
                        # hover_data=["State", "Population"],
                        color_discrete_sequence=["fuchsia"], zoom=8.5, height=300, width=500)
map_fig.update_layout(
    mapbox_style="white-bg",
    mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "sourceattribution": "United States Geological Survey",
            "source": [
                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
            ]
        }
      ])
map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
map_fig.show()

## import data
groundwater_df = pd.read_csv("data/UC_Water_gw_observatory.csv")
flow_df = pd.read_csv("data/cosumnesatmichiganbar.txt", sep="\t", skiprows=2, header=None)

## Select Date and CFS from USGS data
features = [2,3]
flow_df = flow_df[features]
flow_df = flow_df.rename(columns={2: "Date", 3: "CFS"})
flow_df = flow_df[flow_df['Date'] >= '2012-12-14']
flow_df

## Merge USGS data with groundwater data
groundwater_df = groundwater_df.merge(flow_df, how='outer', on='Date')


## Data is named differently in the csv of readings vs. the location data.
## I manually renamed some of the wells to make the two datasets match
groundwater_df = groundwater_df.rename(columns={
    "X283687": "MW_5", 
    "X284197": "UCD_26",
    "X284214": "MW_19",
    "X284215": "Rooney_1",
    "X284216": "MW_11",
    "X284217": "MW_22",
    "X284220":"MW_9",
    "X284221": "MW_405",
    "X284222": "MW_218",
    "X284227": "MW_DR1"
    })


## log transform
## must skew the column by 1 to remove NaN issues
groundwater_df['CFS (log)'] = np.log(groundwater_df['CFS']+1)

## Create a list of wells
wells = groundwater_df.copy()
wells = wells.drop('Date', axis=1)
wells_list = wells.columns.tolist()
wells_list





## levels over time
for well in wells_list:
  # groundwater_df[well] = np.log(groundwater_df[well]+1)
  ## minmax scaler
  # groundwater_df[well] = (groundwater_df[well] - groundwater_df[well].min())/(groundwater_df[well].max()-groundwater_df[well].min())
  ## standard scaler
  groundwater_df[well]=(groundwater_df[well]-groundwater_df[well].mean())/groundwater_df[well].std()


## Don't drop CFS if I want to look at it later
wells = wells.drop(['CFS (log)','CFS'], axis=1)

groundwater_df
import plotly.graph_objects as go
# Create traces
fig = go.Figure()

for well in wells:
  fig.add_trace(go.Scatter(x=groundwater_df['Date'], y=groundwater_df[well],
                      mode='lines',
                      line=dict(
                          color='darkblue',
                          width=2),
                      opacity=0.2,
                      name=well))
fig.add_trace(go.Scatter(x=groundwater_df['Date'], y=groundwater_df['CFS (log)'],
                      mode='lines',
                      line=dict(
                          color='blue',
                          width=2),
                      opacity=.8,
                      # color='LightSkyBlue',
                      name='Cosumnes River CFS (log)'))
# fig.show()



app.layout = html.Div(children=[
    html.H1(children='Groundwater Visualization'),

    html.Div(children='''
        See how different wells respond to changes in the Cosumnes River flow.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=map_fig
    ),
    dcc.Graph(
        id='example-graph2',
        figure=fig,
    ),
    dcc.Markdown('''

It's important to note that this graph is displaying the **relative** change in groundwater levels, not the actual levels. This is to make it easier to compare the trends in each well with the trends in streamflow. 

**Data transformations:**

The wells and stream discharge have all been normalized with a **standard scaler**, which means that the y-axis values are standard deviations from the average level.

Also note that the streamflow has been log transformed to make it easier to see these relationships.

**Coming Soon**

-Ability to hover over a location and see only that well's time series data

-Drought severity index data over time displayed against the well data

-Aesthetic improvements


This visualization was created with data from **UC Water** with input from **The Freshwater Trust.**
''') 
    
])

if __name__ == '__main__':
    app.run_server(debug=True)