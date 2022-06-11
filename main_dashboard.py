#%%

import pandas as pd
from utils import *
# %%
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


#%%

df_well_headers = pd.read_csv("example_172_well_headers.csv")
df_well_tops_detail_vertical = pd.read_csv('df_well_tops_detail_vertical.csv')

filter_columns_dict = {'kb_gt_gl':'KB < Ground Level','kb_gt_zero':'KB < 0','gl_gt_zero':'Ground Level < 0'}
fig_well_header_scatter = create_well_header_qc_map(df_well_headers, filter_columns_dict)
cols_boxplot = ['kb_elevation', 'ground_elevation']
fig_well_header_boxplot = create_well_header_boxplots(df_well_headers, cols_boxplot)
df_invalid_formation = pd.DataFrame(columns=['formation','formation_avg_depth'])
formation_list = df_well_tops_detail_vertical['formation_complete'].unique()
#%%
## create the dashboard 
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
    
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1(
                                    "Well Data Audit",
                                    style={"margin-bottom": "0px"},
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5(
                                    "2022 SeisWare Hackathon", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-third column",
                    id="version",
                )
                
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "0px"},
        ),
        html.P('Well Headers'),
        html.Div(
            [
                
                html.Div(
                    [

                        
                        html.Div(
                            [
                                html.Div(
                                [
                                    dcc.Graph(id="well_header_qc_map",
                                    figure=fig_well_header_scatter),
                                ],
                            
                            )
                            ]
                        )
                    ],
                    className="pretty_container six columns",
                   
                ),
                html.Div(
                    [
                        html.Div(
                            dcc.Graph(id="well_header_qc_boxplot",
                                    figure=fig_well_header_boxplot)
                        )
                    ],
                    className="pretty_container six columns"
                    )
                
            ],
            className="pretty_container row flex-display"
        ),
        html.P("Well Tops"),
        html.Div(
            [
                
                html.Div(
                    [

                        
                        html.Div(
                            [
                                html.Div(
                                [
                                    dcc.Checklist(options=['Show Well Locations','Include Estimated Formations'],value=['Show Well Locations'],inline=True,
                                    id='well_top_plot_checkbox'),
                                   
                                    dcc.Graph(id="well_tops_interpo_map"),
                                ],
                            
                            )
                            ]
                        )
                    ],
                    className="pretty_container twelve columns",
                   
                ),
                
                
            ],
            className="pretty_container row flex-display"
        ),
        
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)



@app.callback(Output('well_tops_interpo_map', 'figure'),
              [Input('well_top_plot_checkbox', 'value')])
def get_well_tops_interpo_plot(well_top_plot_options):
    if 'Include Estimated Formations' in well_top_plot_options:
        formation_col = 'formation_complete'
    else:
        formation_col = 'formation'
    if 'Show Well Locations' in well_top_plot_options:
        show_well_location = True
    else:
        show_well_location = False
    
    fig, _ = create_well_top_interpo_plot(df_well_tops_detail_vertical,show_well_location,formation_col=formation_col)
    return fig

if __name__ == "__main__":
    PORT = 8020
    app.run_server(debug=False,port=PORT)

# %%