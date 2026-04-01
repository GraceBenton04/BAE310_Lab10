# ============================================================
# Import required libraries
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
    
# Define file paths
station_file = 'station.csv'
result_file = 'narrowresult.csv'

# Load both datasets
station_df = pd.read_csv(station_file)
results_df = pd.read_csv(result_file)

    # Convert the date column into datetime format
results_df['ActivityStartDate'] = pd.to_datetime(
        results_df['ActivityStartDate']
    )

    # Convert measurement values into numeric values
results_df['ResultMeasureValue'] = pd.to_numeric(
        results_df['ResultMeasureValue'], errors='coerce')

    # Remove rows that do not contain a valid value
results_df = results_df.dropna(subset=['ResultMeasureValue'])

    # --------------------------------------------------------
    # Create a dropdown list of available characteristics
    # --------------------------------------------------------
characteristic_list = sorted(
        results_df['CharacteristicName'].dropna().unique()
    )

selected_characteristic = st.selectbox(
        'Choose a water quality characteristic:',
        characteristic_list
    )

    # --------------------------------------------------------
    # Filter data to only the selected characteristic
    # --------------------------------------------------------
filtered_results = results_df[
        results_df['CharacteristicName'] == selected_characteristic
    ]

    # --------------------------------------------------------
    # Create sliders for the value range
    # --------------------------------------------------------
min_value = float(filtered_results['ResultMeasureValue'].min())
max_value = float(filtered_results['ResultMeasureValue'].max())

selected_range = st.slider(
        'Select measurement value range:',
        min_value=min_value,
        max_value=max_value,
        value=(min_value, max_value)
    )

    # --------------------------------------------------------
    # Create date inputs for the date range
    # --------------------------------------------------------
min_date = filtered_results['ActivityStartDate'].min().date()
max_date = filtered_results['ActivityStartDate'].max().date()

start_date = st.date_input('Start Date', min_date)
end_date = st.date_input('End Date', max_date)

    # --------------------------------------------------------
    # Apply all filters to the results
    # --------------------------------------------------------
final_results = filtered_results[
        (filtered_results['ResultMeasureValue'] >= selected_range[0]) &
        (filtered_results['ResultMeasureValue'] <= selected_range[1]) &
        (filtered_results['ActivityStartDate'] >= pd.Timestamp(start_date)) &
        (filtered_results['ActivityStartDate'] <= pd.Timestamp(end_date))
    ]

    # --------------------------------------------------------
    # Merge with station data to get locations
    # --------------------------------------------------------
merged_data = final_results.merge(station_df, on='MonitoringLocationIdentifier', how='left')

    # --------------------------------------------------------
    # Display map with stations
    # --------------------------------------------------------
if len(merged_data) > 0:
    # Create a map centered on the average location
    map_center = [merged_data['LatitudeMeasure'].mean(), merged_data['LongitudeMeasure'].mean()]
    m = folium.Map(location=map_center, zoom_start=10)
    
    # Add markers for each station
    for idx, row in merged_data.iterrows():
        folium.Marker(
            location=[row['LatitudeMeasure'], row['LongitudeMeasure']],
            popup=f"{row['MonitoringLocationName']}<br>Value: {row['ResultMeasureValue']}"
        ).add_to(m)
    
    # Display the map
    st_folium(m, width=700, height=500)
    
    # --------------------------------------------------------
    # Display trend plot over time
    # --------------------------------------------------------
    st.subheader(f'{selected_characteristic} vs Time')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each station's data
    for station_id in final_results['MonitoringLocationIdentifier'].unique():
        station_data = final_results[final_results['MonitoringLocationIdentifier'] == station_id].sort_values('ActivityStartDate')
        station_name = station_data['OrganizationFormalName'].iloc[0] if 'OrganizationFormalName' in station_data.columns else station_id
        ax.plot(station_data['ActivityStartDate'], station_data['ResultMeasureValue'], marker='o', label=station_name, alpha=0.7)
    
    ax.set_xlabel('Date')
    ax.set_ylabel(f'{selected_characteristic} (Value)')
    ax.set_title(f'{selected_characteristic} vs Time')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)
else:
    st.warning('No data found for the selected filters.')
