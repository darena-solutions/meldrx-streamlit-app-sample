import streamlit as st
from st_pages import add_page_title
from meldrx_fhir_client import FHIRClient


class App:

    def __init__(self):
        access_token = st.session_state['token']['access_token']
        workspace_id = st.session_state['workspace_id']
        fhir_endpoint = f'https://app.meldrx.com/api/fhir/{workspace_id}'
        self.fhir = FHIRClient(
            base_url=fhir_endpoint,
            access_token=access_token,
            access_token_type='Bearer'
        )

    def render_page(self):
        add_page_title()

        search_requirements = st.session_state['search_requirements']

        if 'patients_result' not in st.session_state:
            st.session_state['patients_result'] = {'entry': []}

        patients_result = st.session_state['patients_result']
        if search_requirements is None:
            patients_result = self.fhir.search_resource('Patient', '')
        else:
            inputs = {}
            for r in search_requirements:
                inputs[r] = st.text_input(r)

            search = st.button('find observations')
            if search:
                patients_result = self.fhir.search_resource('Patient', inputs)
                if 'entry' not in patients_result or len(patients_result['entry']) == 0 or patients_result['entry'][0]['resource']['resourceType'] != 'Patient':
                    st.text('failed to find patient')
                    st.json(patients_result)
                    return
                st.session_state['patients_result'] = patients_result

        if len(patients_result['entry']) == 0:
            return

        i = 0
        for patient in map(lambda entry: entry['resource'], patients_result['entry']):
            container = st.container()
            col1, col2 = container.columns(2, gap='small')
            patient_name = f"{str.join(' ', patient['name'][0]['given'])} {patient['name'][0]['family']}"
            if col1.button(patient_name):
                self.open_patient(patient)
            if col2.button('Observations', key=i):
                self.open_observations(patient['id'])
            i = i + 1

    @st.experimental_dialog("Patient Information")
    def open_patient(self, patient):
        st.markdown(f"""
        - **document id**: `{patient['id']}`
        - **identifiers**: {str.join('; ', map(lambda i: f"{i['system']}: {i['value']}", patient['identifier']))}
        - **name**: {str.join(' ', patient['name'][0]['given'])} {patient['name'][0]['family']}
        - **gender**: {patient['gender']}
        - **birth date**: {patient['birthDate']}
        """)

    @st.experimental_dialog("Patient Observations")
    def open_observations(self, patient_ref):
        observations_result = self.fhir.search_resource('Observation', {'category': 'social-history', 'patient': patient_ref})
        if 'entry' not in observations_result or len(observations_result['entry']) == 0:
            st.text('no observations found')
            st.json(observations_result)
            return

        for resource in map(lambda entry: entry['resource'], observations_result['entry']):
            container = st.container()

            col1, col2 = container.columns(2, gap='small')
            col1.write(resource['code']['text'])
            if 'valueString' in resource:
                col2.write(resource['valueString'])
            elif 'valueQuantity' in resource:
                col2.write(resource['valueQuantity']['value'])
            elif 'valueCodeableConcept' in resource:
                col2.write(resource['valueCodeableConcept']['text'])


if 'token' not in st.session_state:
    st.switch_page('main.py')
else:
    App().render_page()
