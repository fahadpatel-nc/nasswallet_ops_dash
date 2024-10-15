import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

service_account_info = st.secrets["gcp_service_account"]
# service_account_info = cn.service_account_info
credentials = service_account.Credentials.from_service_account_info(service_account_info)
service = build('drive', 'v3', credentials=credentials)

def read_data(name, id):
    file_id = id
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    globals()[name] = pd.read_csv(fh)  

## reading data from local
# df = pd.read_csv('/Users/fahadpatel/Downloads/Nym_ops_data/cardholder.csv')

## reading data from google drive
read_data('df', '1o_XnsuIqZtqZ5rZf0UFkHBSwPWnH1cL9')

status_counts_dict = df['status'].value_counts().to_dict()

df['created'] = pd.to_datetime(df['created'])
current_year = datetime.now().year
current_month = datetime.now().month

df_current_month = df[(df['created'].dt.year == current_year) & (df['created'].dt.month == current_month)]

if df_current_month.empty:
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1
    df_current_month = df[(df['created'].dt.year == previous_year) & (df['created'].dt.month == previous_month)]
    df_current_month['month'] = df_current_month['created'].dt.strftime('%B')
    current_month_val = df_current_month['month'].dropna().unique()[0] + " (Previous Month)"
else:
    df_current_month['month'] = df_current_month['created'].dt.strftime('%B')
    current_month_val = df_current_month['month'].dropna().unique()[0]

# Group by day and status, and count occurrences of each status
df_current_month['day_of_created_date'] = df_current_month['created'].dt.day
status_counts = df_current_month.groupby(['day_of_created_date', 'status']).size().reset_index(name='count')

#######################################################################################################################################################
color_map = {
    'PENDINGIDVERIFICATION': '#e3cb14',  # Yellow for pending verification
    'ACTIVE': '#33bd33',                 # Green for verified
    'SUSPENDED': '#fc8b8b',              # Red for rejected/suspended
    'TERMINATED': '#000000',             # Black for terminated
    'PENDINGKYC': '#ff8800'              # Orange for pending KYC
}


fig_line_status = px.line(
    status_counts,
    x='day_of_created_date',
    y='count',
    color='status',
    title= f'User Onboarding Status Each Day for the month of {current_month_val}',
    labels={'day_of_created_date': 'Day', 'count': 'Status Count'},
    markers=True,
    text='count',
    line_shape='spline',
    color_discrete_map=color_map
)

fig_line_status.update_layout(
    font=dict(size=14),
    title={
        'font': {
            'color': 'gray',
            'family': 'Arial',
            'size': 18
        }
    },
    height=500,
    xaxis=dict(tickmode='linear')
)

fig_line_status.update_traces(
    textposition="top right",
    texttemplate='%{text:.0f}'
)

#######################################################################################################################################################


st. set_page_config(layout="wide")

metrics_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .summary-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .summary-box {{
            background: #f4f4f4;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            width: calc(25% - 20px); /* Adjust width to fit 4 boxes per line */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            box-sizing: border-box;
        }}
        .summary-box h3 {{
            margin: 10px 0;
            font-size: 1.5em;
            color: #333;
        }}
        .heading {{
            margin-top: 0px;
            font-size: 18px;
            color: gray;
            font-family: Arial, sans-serif;
            margin-bottom: 15px;
        }}
        .summary-box {{
            font-family: Arial, sans-serif;
            font-size: 15px;
        }}
    </style>
</head>
<body>
    <h1 class="heading">User Onboarding Summary</h1>
    <div class="summary-container">
        <div class="summary-box">
            <p>Active </p>
            <h3>{status_counts_dict.get('ACTIVE')}</h3>
        </div>
        <div class="summary-box">
            <p>Suspended </p>
            <h3>{status_counts_dict.get('SUSPENDED')}</h3>
        </div>
        <div class="summary-box">
            <p>Pending Verification </p>
            <h3>{status_counts_dict.get('PENDINGIDVERIFICATION')}</h3>
        </div>
        <div class="summary-box">
            <p>Terminated </p>
            <h3>{status_counts_dict.get('TERMINATED')}</h3>
        </div>
        <div class="summary-box">
            <p> Pending KYC</p>
            <h3>{status_counts_dict.get('PENDINGKYC')}</h3>
        </div>
    </div>
    
</body>
</html>
"""

components.html(metrics_html, height=330, scrolling=True)
st.plotly_chart(fig_line_status, use_container_width=True)
