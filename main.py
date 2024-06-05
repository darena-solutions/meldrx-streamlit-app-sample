import streamlit as st
import os
from st_pages import add_page_title, show_pages, Page, Section
from streamlit_oauth import OAuth2Component

add_page_title()

show_pages(
    [
        Page(path="main.py", name="Connect", icon="🤝"),
        Section(name="FHIR Features", icon="🔥️"),
        Page(path="pages/features/search.py", name="Search", icon="🔍"),
        Page(path="pages/features/observations.py", name="Observations", icon="👀"),
        Section(name="Demo Apps", icon="🚨️"),
        Page(path="pages/demos/plaquenil_calculator.py", name="Plaquenil Calculator", icon="🧮"),
        Page(path="pages/demos/creatine_clearance.py", name="Creatine Clearance", icon="📏"),
    ]
)

sign_in_options = [
    {'workspace_id': os.environ.get('MELDRX_WORKSPACE_ID'), 'name': 'MeldRx', 'search_requirements': None},
    {'workspace_id': os.environ.get('SMART_WORKSPACE_ID'), 'name': 'SmartHealth IT', 'search_requirements': None},
    {'workspace_id': os.environ.get('EPIC_WORKSPACE_ID'), 'name': 'Epic', 'search_requirements': ['given', 'family', 'birthDate']},
]

AUTHORIZE_URL = 'https://app.meldrx.com/connect/authorize'
TOKEN_URL = 'https://app.meldrx.com/connect/token'
REFRESH_TOKEN_URL = 'https://app.meldrx.com/connect/token'
REVOKE_TOKEN_URL = 'https://app.meldrx.com/connect/revocation'
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
SCOPE = 'openid profile patient/*.read'


oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)
for option in sign_in_options:
    workspace_id = option['workspace_id']
    result = oauth2.authorize_button(
        name=option['name'],
        redirect_uri=f'{os.environ.get("APP_URL")}/component/streamlit_oauth.authorize_button',
        scope=SCOPE,
        extras_params={'aud': f'https://app.meldrx.com/api/fhir/{workspace_id}'},
        pkce='S256'
    )

    if result and 'token' in result:
        # If authorization successful, save token in session state
        st.session_state.token = result.get('token')
        st.session_state.workspace_id = workspace_id
        st.session_state.search_requirements = option['search_requirements']

if 'token' in st.session_state:
    token = st.session_state['token']
    st.text('token_response')
    st.json(token)
