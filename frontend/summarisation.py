from typing import Literal, Optional
from openai import OpenAI, APIConnectionError, RateLimitError
from pydantic import BaseModel, Field
import datetime
from typing import List, Literal
# Import necessary modules
import backoff

import json
from datetime import datetime
import numpy as np
import pandas as pd
import os
from configparser import ConfigParser
import streamlit as st
import copy
from mongo_connect import ChatMessagesHandler
import pytz


# Set the timezone to GMT+8
timezone = pytz.timezone('Asia/Singapore')  # Singapore is in GMT+8


try:
    config = ConfigParser()
    config.read('config.ini')
    api_key = config['OPENAI']['api_key']
    os.environ["OPENAI_API_KEY"] = api_key
except:
    api_key = st.secrets['OPENAI']['api_key']

client = OpenAI(api_key=api_key, max_retries=5)

default_system_messages = f"""You are a helpful assistant in summarising comments and extract the key essence of the narrative, keep it short and concise. 

Provide your summary in a short paragraphs and bold on the key themes."""

# Define a 'chat' function that uses the OpenAI API to generate a response


@backoff.on_exception(backoff.expo, APIConnectionError, max_time=1000)
@backoff.on_exception(backoff.expo, RateLimitError, max_time=6000)
def chat(prompt: str, openai_client=client, system_message=default_system_messages, model="gpt-4o", temperature=0, max_tokens=500):
    """
    Function that uses the OpenAI API to generate a response.

    Args:
    - history (list[dict[str, str]]): List of previous messages in the conversation.
    - new_input (dict): Dictionary containing the new message to be added to the conversation.
    - temperature (float): Controls the "creativity" of the response generated by the model.
    - max_tokens (int): Maximum number of tokens (words) in the response generated by the model.
    - exclude_functions (list[str]): List of function names to exclude from the response.

    Returns:
    - response.choices[0] (dict): Dictionary containing the response generated by the model.
    """
    # Generate a response using the OpenAI API
    response = openai_client.chat.completions.create(
        model=model, temperature=temperature, max_tokens=max_tokens,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": """Summarising the messages and extract the key essence of the narrative, keep it short and concise. 

Provide your summary in a short paragraphs and bold on the key themes.\n\nMessages:\n""" + prompt
            }
        ]
    )

    # openai v1.0.0 > return the response in a pydantic model
    # will need to dump the model into json str then load into json
    response = json.loads(response.model_dump_json())

    # Return the response generated by the model
    return response["choices"][0]['message']['content']

handler = ChatMessagesHandler()
recent_msgs = handler.get_recent_message_breakdowns()
recent_msgs_updated = copy.deepcopy(recent_msgs)
ss = st.session_state
# Custom CSS
st.markdown("""
<style>
    .positive-container {
        background-color: #e6ffe6;
        padding: 10px;
        border-radius: 10px;
    }
    .negative-container {
        background-color: #ffe6e6;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

input_1, input_2 = st.columns(2, vertical_alignment='center')
with input_1:
    msg_threshold = st.slider("Select the number of messages to analyze", min_value=30, max_value=100, value=30, step=10, key="num_messages")
with input_2:
    generate_summary = st.button("Generate Summary", use_container_width=True, type="primary", key="generate_summary")


mapped_section = {"sg": "Singapore", 
                    "sentiment": "Sentiment Analysis", 
                    "religion_race": "Race and Religion", 
                    "societal_impact": "Societal Impact Assessment",
                    "military": "Military"}
label_map = {"Favor": "Favor", "Against": "Against", "Pos": "Positive", "Neg": "Negative"}
if generate_summary:
    for section, value in recent_msgs.items():
        with st.container(border=True):
            st.markdown(f"## {mapped_section[section]}")
            col_1, col_2 = st.columns(2, vertical_alignment='center')
            for label, messages in value.items():
                messages = [msg['message'] for msg in messages]                 
                if label in ['Favor', 'Pos'] and len(messages) >= msg_threshold:
                    chat_summary = chat(str(messages))
                    recent_msgs_updated[section][f'summary_{label}'] = chat_summary
                    with col_1:
                        st.markdown(f"""<div class="positive-container">

##### {label_map[label]} Summary
{chat_summary}
</div>""", unsafe_allow_html=True)
                elif label in ['Favor', 'Pos'] and len(messages) < msg_threshold:
                    with col_1:
                        st.write(f"Insufficient messages for {label_map[label]}, only {len(messages)} messages found.")
                        
                if label in ['Against', 'Neg'] and len(messages) >= msg_threshold:
                    chat_summary = chat(str(messages))
                    recent_msgs_updated[section][f'summary_{label}'] = chat_summary
                    with col_2:
                        st.markdown(f"""<div class="negative-container">

##### {label_map[label]} Summary
{chat_summary}
</div>""", unsafe_allow_html=True)
                elif label in ['Against', 'Neg'] and len(messages) < msg_threshold:
                    with col_2:
                        st.write(f"Insufficient messages for {label_map[label]}, only {len(messages)} messages found.")

    recent_msgs_updated['generate_dt'] = datetime.now(timezone)
    handler.insert_summaries(recent_msgs_updated)
# with st.container(border=True):
#     st.markdown("### Sentiment Analysis Summary")





#     # Your Streamlit app
#     senti_col1, senti_col2 = st.columns(2)

#     with senti_col1:
#         with st.container():
#             pos_senti_summary = """
# Dummy text for positive summary:
# - Summaries are generated based on the sentiment analysis of comments."""
            

#     with senti_col2:
#         with st.container():
#             neg_senti_summary = """
# Dummy text for negative summary: 
# - This container should have a light red background."""
#             st.markdown(f"""<div class="negative-container">

# ##### Negative Summary
#     {neg_senti_summary}""", unsafe_allow_html=True)
#             st.markdown('</div>', unsafe_allow_html=True)
