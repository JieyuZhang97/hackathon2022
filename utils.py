#%%
import plotly.graph_objects as go


import json
import requests
import pandas as pd 
from pyproj import Proj
from scipy.spatial import cKDTree
import numpy as np
from scipy.interpolate import griddata

def get_well_data(uwis_list,url):

    headers = {'Content-Type': 'application/json', 'x-api-key': 'Z6omObqgyUa1N7ApvBHfZ88qHnPNi4Df2X0V3OKp'}

    myobj ={
	"uwis": uwis_list}

    x = requests.post(url, data = json.dumps(myobj), headers=headers)
    df_well_tops = pd.DataFrame.from_records(x.json())
    return df_well_tops

def create_well_header_qc_map(df_well_headers, filter_columns_dict, longitude_col = 'surface_longitude',latitude_col = 'surface_latitude',hover_text_col = 'well_name'):
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon = df_well_headers[longitude_col],
        lat = df_well_headers[latitude_col],
        text = df_well_headers[hover_text_col],
        mode = 'markers',
        showlegend=False
        ))


    for filter_column,filter_legend in filter_columns_dict.items():
        fig.add_trace(go.Scattergeo(
            lon = df_well_headers.loc[~df_well_headers[filter_column],longitude_col],
            lat = df_well_headers.loc[~df_well_headers[filter_column],latitude_col],
            text = df_well_headers.loc[~df_well_headers[filter_column],hover_text_col],
            mode = 'markers',
            name = filter_legend
            ))

    fig.update_layout(
    mapbox_style="white-bg",
    mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "sourceattribution": "Government of Canada",
            "source": ["https://geo.weather.gc.ca/geomet/?"
                       "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={bbox-epsg-3857}&CRS=EPSG:3857"
                       "&WIDTH=1000&HEIGHT=1000&LAYERS=RADAR_1KM_RDBR&TILED=true&FORMAT=image/png"],
        }
      ])
    fig.update_geos(fitbounds="locations")
    fig.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(legend=dict(
            yanchor="top",
            y=1.01,
            xanchor="left",
            x=-0.05
        ))
    return fig

def create_histogram(df,col):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df[col],nbinsx=50))
    fig.update_traces(opacity=0.75)
    fig.update_layout(title=col)
    return fig 

def create_well_header_boxplots(df_well_headers, cols_boxplot):
    fig = go.Figure()

    for col in cols_boxplot:
        fig.add_trace(go.Box(x=df_well_headers[col],name=col))
    return fig

def create_well_top_interpo_plot(df_well_tops_detail_vertical, show_well_location, formation_col= 'formation_complete', formation_bottom_depth_col= 'bottom_depth', formation_top_depth_col='depth', well_loc_y='surface_northing', well_loc_x='surface_easting', well_uwi_col='wellbore_uwi'):
    formation_list = df_well_tops_detail_vertical['formation_complete'].unique()
    invalid_formation_list = list()
    invalid_formation_depth_list = list()

    fig = go.Figure()
    
    for formation in formation_list:
        formation_mask = df_well_tops_detail_vertical[formation_col]==formation
        formation_bottom_depth = df_well_tops_detail_vertical.loc[formation_mask,formation_bottom_depth_col]
        formation_northing = df_well_tops_detail_vertical.loc[formation_mask,well_loc_y]
        formation_easting = df_well_tops_detail_vertical.loc[formation_mask,well_loc_x]
    
        points = np.array([formation_easting,formation_northing]).T
        grid_x, grid_y = np.meshgrid(np.linspace(formation_easting.min(),formation_easting.max(),100), np.linspace(formation_northing.min(),formation_northing.max(),100))
        try:
            grid_z0 = griddata(points, formation_bottom_depth, (grid_x, grid_y), method='linear')
            fig.add_trace(go.Surface(z=grid_z0, x=grid_x, y=grid_y,name=formation, showscale=False))
        except:
            invalid_formation_list.append(formation)
            invalid_formation_depth_list.append(np.nanmean([df_well_tops_detail_vertical.loc[formation_mask,formation_top_depth_col].mean(),df_well_tops_detail_vertical.loc[formation_mask,formation_bottom_depth_col].mean()]))

    if show_well_location:
        for uwi in df_well_tops_detail_vertical[well_uwi_col].unique():
            df_well_location = df_well_tops_detail_vertical.loc[df_well_tops_detail_vertical[well_uwi_col]==uwi,[well_loc_x,well_loc_y,formation_top_depth_col]]
            fig.add_trace(go.Scatter3d(x=df_well_location[well_loc_x],y=df_well_location[well_loc_y],z=df_well_location[formation_top_depth_col],mode='lines',line=dict(
            color='red'
        ),name=uwi,showlegend=False))
    fig.update_layout(scene = dict(
                    xaxis_title='Easting',
                    yaxis_title='Northing',
                    zaxis_title='Depth'),
                    
                    margin=dict(r=1, b=1, l=1, t=1))
    df_invalid_formation = pd.DataFrame(columns=['formation','formation_avg_depth'])
    df_invalid_formation['formation'] = invalid_formation_list
    df_invalid_formation['formation_avg_depth'] = invalid_formation_depth_list
    df_invalid_formation
    return fig,df_invalid_formation


def get_well_formation_estimation(df_well_tops_org):
    df_well_tops = df_well_tops_org.copy()
    # wells with no formation picks
    # they have depth and bottom depth, just the formation information is lost
    formation_null_mask = df_well_tops['formation'].isna() 
    
    # use nearest neighbor to fill the formation 
    df_well_tops['formation_estimate'] = None


    data = np.array([df_well_tops.dropna(subset=['bottom_depth']).loc[~formation_null_mask,'surface_latitude'],df_well_tops.dropna(subset=['bottom_depth']).loc[~formation_null_mask,'surface_longitude'],df_well_tops.dropna(subset=['bottom_depth']).loc[~formation_null_mask,'depth'],df_well_tops.dropna(subset=['bottom_depth']).loc[~formation_null_mask,'bottom_depth']]).T
    sample = np.array([df_well_tops.loc[formation_null_mask,'surface_latitude'],df_well_tops.loc[formation_null_mask,'surface_longitude'],df_well_tops.loc[formation_null_mask,'depth'],df_well_tops.loc[formation_null_mask,'bottom_depth']]).T

    kdtree=cKDTree(data)
    dist,points=kdtree.query(sample,1)

    df_well_tops.loc[formation_null_mask,'formation_estimate'] = df_well_tops.loc[~formation_null_mask,'formation'].iloc[points].values
    df_well_tops['formation_complete'] = df_well_tops['formation'].fillna(df_well_tops['formation_estimate'])
    return df_well_tops

def get_utm(lat,long):
    projection = Proj(proj='utm',zone=10,ellps='WGS84', preserve_units=False)

    easting, northing = projection(long,lat)
    return easting, northing