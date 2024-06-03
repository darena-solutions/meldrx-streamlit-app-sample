import streamlit as st
from st_pages import add_page_title
from requests import get


def render_page():
    access_token = st.session_state['token']['access_token']
    workspace_id = st.session_state['workspace_id']
    search_requirements = st.session_state['search_requirements']
    # fhir = FHIRClient(
    #     base_url='https://app.meldrx.com/api/fhir/6b11b99f-0aa3-4cc3-972f-158c70c88c4d',
    #     access_token=access_token,
    #     access_token_type='Bearer'
    # )
    add_page_title()

    fhir_endpoint = f'https://app.meldrx.com/api/fhir/{workspace_id}'
    with st.form('search'):
        st.text(fhir_endpoint)
        query_input = st.text_input(label='Query', value='Patient?gender=male' if search_requirements is None else 'Patient?family=Lin&given=Derrick&birthdate=1973-06-03')
        submit = st.form_submit_button('Search')

    if submit:
        response = get(
            url=f'{fhir_endpoint}/{query_input}',
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )
        if response.status_code == 200:
            st.text('Success')
            st.json(response.json())
        else:
            st.text('Error')
            st.json(response.json())


if 'token' not in st.session_state:
    st.switch_page('main.py')
else:
    render_page()
