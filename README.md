# hackathon2022

A simple dashboard for visualizing well header and tops data for QC purposes.

## Well header
We looked at kb elevation and groud elevation. In theory, kb elevation should always be higher than ground elevation. Wells with invalid kb elevation and ground elevation are highlighted in different colors in the plot. 

## Well tops 
We focused on visualizing the picked tops from wells in area. There are well entries with `top_depth` and `depth` values but no formation. For those wells, a simple nearest neighbor algorithm is applied to estimate the most possible formation. The plot can either be using provided formation column from the API or the formation column integrated with estimated formations. 
