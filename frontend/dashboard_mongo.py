import math
import streamlit as st
import pandas as pd
import time
import asyncio
from datetime import datetime
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pytz


#from sql_table import collection_start_status, read_messages_from_db_enriched, read_messages_from_db
from mongo_connect import ChatMessagesHandler
from streamlit_extras.metric_cards import style_metric_cards 

handler = ChatMessagesHandler()
# Get list of active collection URLs
urls = handler.collection_start_status()

ss = st.session_state

def create_stance_line_charts(enriched_msgs_df):
    # Convert start_time and end_time to datetime objects if they're not already
    start_time = enriched_msgs_df['Create DateTime'].min()
    end_time = enriched_msgs_df['Create DateTime'].max()
    
    # Calculate time difference in minutes
    time_diff = (end_time - start_time).total_seconds() / 60
    
    # Determine frequency based on time difference
    if time_diff <= 15:
        freq = '1min'
    elif time_diff <= 60:
        freq = '5min'
    elif time_diff <= 120:
        freq = '10min'
    else:
        freq = '15min'
    
    # List of stance variables
    stance_variables = ['RnR', 'Military', 'SG', 'Societal Impact']
    
    # Color mapping for categories
    color_map = {'Favor': '#008000', 'Against': '#FF0000'}
    
    figures = {}
    
    for stance in stance_variables:
        if stance not in enriched_msgs_df.columns:
            print(f"Warning: {stance} column not found in the dataframe")
            continue
        
        # Group by time and stance, then count messages
        df_grouped = enriched_msgs_df.groupby([pd.Grouper(key='Create DateTime', freq=freq), stance]).size().unstack(fill_value=0)

        fig = go.Figure()
        
        max_value = 0  # Initialize max_value to track the highest point in the data
        
        for category in ['Favor', 'Against']:
            if category in df_grouped.columns:
                y_values = df_grouped[category]
                max_value = max(max_value, y_values.max())  # Update max_value
                
                fig.add_trace(go.Scatter(
                    x=df_grouped.index,
                    y=y_values,
                    mode='lines+markers',
                    name=category,
                    line=dict(color=color_map[category]),
                    marker=dict(color=color_map[category])
                ))
            else:
                print(f"Warning: {category} not found in grouped data for {stance}")
        
        # Calculate appropriate y-axis range
        y_max = math.ceil(max_value * 1.1) # Add 10% padding above the maximum value
        y_min = 0
        
        # Calculate an appropriate integer interval
        if y_max <= 5:
            interval = 1
        elif y_max <= 20:
            interval = 2
        elif y_max <= 50:
            interval = 5
        else:
            interval = 10
        
        # Adjust y_max to be a multiple of the interval
        y_max = math.ceil(y_max / interval) * interval
        
        fig.update_layout(
            title_text=f"{stance} Stance (Freq: {freq})",
            xaxis_title='Time',
            yaxis_title='Count of Messages',
            legend_title='Category',
            height=400,
            margin=dict(l=50, r=50, t=50, b=0)
        )
        
        fig.update_xaxes(range=[start_time, end_time])
        fig.update_yaxes(range=[y_min, y_max])  # Set dynamic y-axis range
        
        # Add more tick marks on y-axis for better readability
        fig.update_yaxes(dtick=(y_max - y_min) / 5)  # Add approximately 5 tick marks
        
        figures[stance] = fig
    
    return figures


# Display the active collection URLs
with st.sidebar:
    st.markdown("## Active Collection URLs:")
    # print list of urls
    if urls is None:
        st.write("No URLs started")
    else:
        for url in urls:
            st.write(url)


enriched_msgs = handler.read_messages_from_db_enriched()
enriched_msgs = [{k: v for k, v in d.items() if k != '_id'} for d in enriched_msgs]

enriched_msgs_df = pd.DataFrame(enriched_msgs)
# Rename columns for consistency
enriched_msgs_df.rename(columns={'id': 'ID',
                                 'msg_id': 'Msg Id',
                                    'vid_id': 'Video Id',
                                    'author_id': 'Author Id',
                                    'author': 'Author',
                                    'dt_stamp': 'Create DateTime',
                                    'message': 'Message',
                                    'enriched': 'Enriched',
                                    'mishap': 'Mishap',
                                    'sg': 'SG',
                                    'mil': 'Military',
                                    'rnr': 'RnR',
                                    'lang': 'Language',
                                    'troll': 'Troll',
                                    'toxic': 'Toxic',
                                    'societal_impact': 'Societal Impact',
                                    'senti': 'Sentiment'}, inplace=True)
# enriched_msgs_df = pd.DataFrame(enriched_msgs, columns=['id', 'Video Id', 'Author', 'author_id', 'Create DateTime',
#                                 'msg_id', 'Message', 'Enriched', 'Mishap', 'SG', 'Military', 'RnR', 'Language', 'Troll', 'Toxic', 'Sentiment'])

# Convert Troll, Toxic and Enriched to boolean
enriched_msgs_df['Troll'] = enriched_msgs_df['Troll'].astype(bool)
enriched_msgs_df['Toxic'] = enriched_msgs_df['Toxic'].astype(bool)
enriched_msgs_df['Enriched'] = enriched_msgs_df['Enriched'].astype(bool)
enriched_msgs_df['Create DateTime'] = pd.to_datetime(enriched_msgs_df['Create DateTime'], errors='coerce')

# Set the timezone to GMT+8
timezone = pytz.timezone('Asia/Singapore')  # Singapore is in GMT+8

st.markdown(f"## Dashboard (Last updated - {datetime.now(timezone).strftime('%H:%M:%S')})")
# Group sentiments by sentiment type
sentiments = enriched_msgs_df['Sentiment'].value_counts().to_dict()
sentiments = {k.capitalize(): v for k, v in sentiments.items()}
# Drop Na
sentiments.pop('Na', None)


# Create DataFrame
sentiments_df = pd.DataFrame(list(sentiments.items()), columns=['Sentiment', 'Count'])

# Define color mapping
sentiment_map = {'Pos': 'Positive', 'Neut': 'Neutral', 'Neg': 'Negative'}
sentiments_df['Sentiment'] = sentiments_df['Sentiment'].map(sentiment_map)
color_map = {'Positive': '#008000', 'Negative': '#FF0000', 'Neutral': '#808080'}  # Green, Red, Grey

# Create Plotly figure (horizontal bar chart)
senti_fig = go.Figure(data=[go.Bar(
    y=sentiments_df['Sentiment'],
    x=sentiments_df['Count'],
    marker_color=[color_map[s] for s in sentiments_df['Sentiment']],
    orientation='h'  # This makes the bar chart horizontal
)])

# Update layout
senti_fig.update_layout(
    title_text='Sentiment Distribution😃😡',
    yaxis_title='Sentiment',
    xaxis_title='Count',
    showlegend=False,
    height=200,  # Adjust the height as needed
    margin=dict(l=0, r=0, t=30, b=0)  # Adjust margins as needed
)

troll = enriched_msgs_df['Troll'].value_counts().to_dict()
# Capitalize the keys
troll = {str(k).capitalize(): v for k, v in troll.items()}

toxic = enriched_msgs_df['Toxic'].value_counts().to_dict()
# Capitalize the keys
toxic = {str(k).capitalize(): v for k, v in toxic.items()}



# Display the DataFrame in bar form
col1, col2, col3= st.columns([2, 1, 1])
with col1:
    st.plotly_chart(senti_fig, use_container_width=True)
with col2:
    st.write("")
    troll_true = troll.get('True', 0)
    if troll_true == 0:
        st.metric(label="**Troll**🧌", value="Not Applicable")
    else:
        st.metric(label="**Troll**🧌", value=f"{troll_true} of {len(enriched_msgs_df['Troll'])} ({round(troll_true / len(enriched_msgs_df['Troll']) * 100, 1)}%)")
with col3:
    st.write("")
    toxic_true = toxic.get('True', 0)
    if toxic_true == 0:
        st.metric(label="**Toxic**💀", value="Not Applicable")
    else:
        st.metric(label="**Toxic**💀", 
                  value=f"{toxic_true} of {len(enriched_msgs_df['Toxic'])} ({round(toxic_true / len(enriched_msgs_df['Toxic']) * 100, 1)}%)",
                  help="Indicates if the comment contains harmful or inappropriate content.")
style_metric_cards(box_shadow=False)



stances_figs = create_stance_line_charts(enriched_msgs_df)
col5, col6, col7, col8 = st.columns(4)
stance_columns = [col5, col6, col7, col8]
stance_map = {'RnR': 'Race and Religion', 'Military': 'Military', 'SG': 'Singapore', 'Societal Impact': 'Societal Impact'}
for i, (stance, fig) in enumerate(stances_figs.items()):
    with stance_columns[i]:
        stance_norm = stance_map[stance]
        stance_dict = enriched_msgs_df[stance].value_counts().to_dict()
        favor = stance_dict.get('Favor', 0)
        against = stance_dict.get('Against', 0)
        neutral = stance_dict.get('Neutral', 0)
        st.metric(label=f"**{stance_norm}**", value=f"{favor}👍, {neutral} 😑, {against} 👎")
        st.plotly_chart(fig, use_container_width=True)

# Calculate language distribution
language_distribution = enriched_msgs_df['Language'].value_counts()
total_messages = language_distribution.sum()

# Calculate percentages
percentages = (language_distribution / total_messages * 100).round(1)

# Create labels
labels = [f"{count} ({pct}%)" for count, pct in zip(language_distribution, percentages)]

# Define colors for each language
colors = {'EN': '#1f77b4', 'MS': '#ff7f0e', 'ZH': '#2ca02c', 'TA': '#d62728', 'Other': '#9467bd'}

# Create a stacked bar chart
lang_fig = go.Figure(data=[
    go.Bar(
        name='Count',
        x=language_distribution.index,
        y=language_distribution.values,
        text=labels,
        textposition='auto',
        marker_color=[colors.get(lang, '#8c564b') for lang in language_distribution.index]
    )
])

# Update the layout
lang_fig.update_layout(
    title_text='Language Distribution',
    xaxis_title='Language',
    yaxis_title='Count',
    height=400,
    margin=dict(l=50, r=50, t=50, b=50)
)


# Insert the language distribution chart before the Datasource section
st.plotly_chart(lang_fig, use_container_width=True)


not_enriched = handler.read_messages_from_db()
st.markdown(f"#### Datasource ({len(not_enriched)} not enriched, {len(enriched_msgs)} enriched)", help = "Messages less than 5 characters are not enriched or displayed.")

# Drop msg_id column
enriched_msgs_df.drop(columns=['Msg Id', 'Author Id'], inplace=True)

stances_options = ['Favor', 'Against', 'Neutral', 'NA']
column_config = {
        "Language": st.column_config.SelectboxColumn(
            "Language",
            help="Main Language of the Message (English (EN), Malay (MS), Chinese (ZH), Tamil (TA), Other)",
            width="small",
            options=[
                "EN",
                "MS",
                "ZH",
                "TA",
                "Other",
            ],
            required=True,
        ),
        "Sentiment": st.column_config.SelectboxColumn(
            "Sentiment",
            help="Sentiment of the Message (Positive, Neutral, Negative)",
            width="small",
            options=[
                "Pos",
                "Neut",
                "Neg",
            ],
            required=True,
        ),
        "Military": st.column_config.SelectboxColumn(
            "Military",
            help="Stance on Military (Favor, Against, Neutral, NA)",
            width="small",
            options=stances_options,
            required=True,
        ),
        "RnR": st.column_config.SelectboxColumn(
            "Race and Religion",
            help="Stance on Race and Religion (Favor, Against, Neutral, NA)",
            width="small",
            options=stances_options,
            required=True,
        ),
        "SG": st.column_config.SelectboxColumn(
            "Singapore",
            help="Stance on Singapore (Favor, Against, Neutral, NA)",
            width="small",
            options=stances_options,
            required=True,
        ),
        "Troll": st.column_config.CheckboxColumn(
            "Troll",
            help="Stance on Troll (True, False)",
        ),
        "Toxic": st.column_config.CheckboxColumn(
            "Toxic",
            help="Stance on Toxic (True, False)",
        ),
        "Societal Impact": st.column_config.SelectboxColumn(
            "Societal Impact",
            help="Stance on Societal Impact (Favor, Against, Neutral, NA)",
            width="small",
            options=stances_options,
            required=True,
        ),
    }
# Sort enriched_msgs_df by Create DateTime descending
if not bool(ss.get("changed_rows", False)):
    # enriched_msgs_df.sort_values(by='Create DateTime', ascending=False, inplace=True)
    # Initialize a list to keep track of changed rows
    ss["changed_rows"] = []



edited_df = st.data_editor(enriched_msgs_df,
                column_config=column_config,
                key = "edited_df",
                disabled=["ID", "Video Id", "Author", "Create DateTime", "Message", "Enriched"],
                hide_index=True, 
                use_container_width=True)



# Iterate through the rows and compare
for i in range(len(enriched_msgs_df)):
    if not enriched_msgs_df.iloc[i].equals(edited_df.iloc[i]):
        # Append the ID of the row to changed_rows
        ss["changed_rows"].append(edited_df.iloc[i]['ID'])

ds_col1, ds_blank, ds_col2 = st.columns([1, 1, 1])
with ds_col1:
    auto_refresh_toggle = st.toggle("Auto Refresh", not bool(ss.get("changed_rows")), help = "Automatically refresh the page every 30 seconds to fetch new data.")
with ds_col2:
    update_btn = st.button("Update", key="update_btn", use_container_width=True, type="primary")
    
if update_btn:
    st.write("Updating the database...")
    enriched_msgs_list = []
    ss["changed_rows"] = list(set(ss["changed_rows"]))
    # Update the database with the changed rows
    fe_be_mapper = {
        "ID": "id",
        "Language": "lang",
        "Sentiment": "senti",
        "Military": "mil",
        "RnR": "rnr",
        "SG": "sg",
        "Troll": "troll",
        "Toxic": "toxic",
        "Societal Impact": "societal_impact"
    }
    for idx in ss["changed_rows"]:
        edited_msg_dict = edited_df.loc[edited_df['ID'] == idx].to_dict('records')[0]
        # Map frontend column names to backend column names (Drop columns not in the mapper)
        edited_msg_dict = {k: v for k, v in edited_msg_dict.items() if k in fe_be_mapper.keys()}
        # Rename columns
        edited_msg_dict = {fe_be_mapper[k]: v for k, v in edited_msg_dict.items()}
        enriched_msgs_list.append(edited_msg_dict)
    
    handler.update_msg_enrichment_many(enriched_msgs_list)
    ss['changed_rows_success'] = True


if ss.get("changed_rows_success", False):
    st.write(f"Database updated successfully for {len(ss['changed_rows'])} rows.")
    ss['changed_rows'] = []
    ss['changed_rows_success'] = False
    st.balloons()
    time.sleep(3)
    st.rerun()
    

if auto_refresh_toggle:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
