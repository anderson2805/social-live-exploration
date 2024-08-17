import streamlit as st

st.set_page_config(layout="wide")

codebook = st.Page(
    "frontend/codebook.py", title="Codebook", icon=":material/book:"
)

collection = st.Page(
    "frontend/collection.py", title="Collection Center", icon=":material/youtube_activity:", default=True
)
dashboard = st.Page(
    "frontend/dashboard_mongo.py", title="Dashboard", icon=":material/dashboard:"
)
summary = st.Page(
    "frontend/summarisation.py", title="Summary", icon=":material/summarize:"
)



pg = st.navigation([codebook, collection, dashboard, summary])


pg.run()