import streamlit as st

st.set_page_config(layout="wide")

codebook = st.Page(
    "frontend/codebook.py", title="Codebook", icon=":material/book:"
)

collection = st.Page(
    "frontend/collection.py", title="Collection Insertion/Status", icon=":material/info:", default=True
)
dashboard = st.Page(
    "frontend/dashboard_mongo.py", title="Dashboard", icon=":material/dashboard:"
)




pg = st.navigation([codebook, collection, dashboard])


pg.run()