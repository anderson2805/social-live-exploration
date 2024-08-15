# from sql_table import insert_collection, stop_collection, get_collection, delete_collection
import time
from mongo_connect import ChatMessagesHandler
import streamlit as st
import pandas as pd

handler = ChatMessagesHandler()

ss = st.session_state
ss['collection_list'] = handler.get_collection()
# Drop _id from dict in collection_list
ss['collection_list'] = [{k: v for k, v in d.items() if k != '_id'} for d in ss['collection_list']]

# Collection_list into a dataframe
df = pd.DataFrame(ss['collection_list'])
df = pd.DataFrame([item.values() for item in ss['collection_list']], columns=["URL", "Platform", "Status"])

event = st.dataframe(df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="multi-row",
                    )

col1, col2a, col2b, col3, col4 = st.columns([5, 1, 1, 1, 1])

with col1:
    url = st.text_input("URL", placeholder="Enter YouTube URL. E.g. https://www.youtube.com/watch?v=wsT2D03KTMM", label_visibility="collapsed")
with col2a:
    insert_btn = st.button("Insert", use_container_width=True)
with col2b:
    start_btn = st.button("Start", use_container_width=True)
with col3:
    stop_btn = st.button("Stop", use_container_width=True)
with col4:
    del_btn = st.button("Delete", type="primary", use_container_width=True)

if handler.get_service_status() == "stopped":
    st.write("Backend collection service is stopped. Please contact support to start the service. 🔴")
else:
    st.write("Backend collection service is running. ✅")


if event.selection.rows:
    ss['collection_select'] = df.iloc[event.selection.rows]['URL'].values.tolist()
else:
    ss['collection_select'] = None

if insert_btn:
    if handler.insert_collection(url):
        st.write(f"Collection for {url} inserted and started.")
    else:
        st.write(f"Collection for {url} already exists.")
    st.rerun()

if start_btn:
    handler.start_collection(ss['collection_select'])
    st.balloons()
    st.write(f"Collection for {ss['collection_select']} started.")
    time.sleep(3)
    st.rerun()

if stop_btn:
    handler.stop_collection(ss['collection_select'])
    st.balloons()
    st.write(f"Collection for {ss['collection_select']} stopped.")
    time.sleep(3)
    st.rerun()
    
if del_btn:
    handler.delete_collection(ss['collection_select'])
    st.balloons()
    st.write(f"Collection for {ss['collection_select']} deleted.")
    st.rerun()

