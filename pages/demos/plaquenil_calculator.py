import dateutil.parser
import streamlit as st
import pandas as pd
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

            search = st.button('find patients')
            if search:
                patients_result = self.fhir.search_resource('Patient', inputs)
                if 'entry' not in patients_result or len(patients_result['entry']) == 0 or patients_result['entry'][0]['resource']['resourceType'] != 'Patient':
                    st.text('failed to find patient')
                    st.json(patients_result)
                    return
                st.session_state['patients_result'] = patients_result

        if len(patients_result['entry']) == 0:
            return

        select = st.selectbox(
            label="Patient",
            placeholder="Select Patient",
            index=None if len(patients_result['entry']) > 1 else 0,
            options=map(
                lambda entry: entry['resource'],
                patients_result['entry']
            ),
            format_func=lambda patient: f"{str.join(' ', patient['name'][0]['given'])} {patient['name'][0]['family']}"
        )

        condition = st.selectbox("Condition Being Treated", ["Malaria", "Rheumatoid Arthritis", "Lupus"])

        if select and condition:
            weight_observations = self.fhir.search_resource(
                'Observation',
                {
                    'category': 'vital-signs',
                    'patient': f'{select["resourceType"]}/{select["id"]}',
                    'code': 'http://loinc.org|29463-7'
                }
            )

            if weight_observations['total'] == 0:
                st.text('no weight observations found.')
                return

            calculations = []
            for weight_entry in weight_observations['entry']:
                weight_resource = weight_entry['resource']
                weight = weight_resource['valueQuantity']['value']

                dosing, schedule = App.calculate_dosing(weight, condition)
                calculations.append([
                    dateutil.parser.parse(weight_resource['effectiveDateTime']),
                    weight,
                    dosing,
                    schedule,
                ])

            df = pd.DataFrame(calculations, columns=['Time', 'Weight (kg)', 'Dosing (mg)', 'Schedule'])
            st.table(df)

    @staticmethod
    def calculate_dosing(weight_kg, condition):
        if condition == "Malaria":
            dose_mg = weight_kg * 13  # Example calculation for malaria prophylaxis
            dosing_schedule = "Single dose, repeated in 6-8 hours if needed."
        elif condition == "Rheumatoid Arthritis":
            dose_mg = weight_kg * 6.5  # Example calculation for rheumatoid arthritis
            if dose_mg > 400:
                dose_mg = 400  # Maximum daily dose
            dosing_schedule = "Once daily."
        elif condition == "Lupus":
            dose_mg = weight_kg * 6.5  # Example calculation for lupus
            if dose_mg > 400:
                dose_mg = 400  # Maximum daily dose
            dosing_schedule = "Once daily."
        else:
            dose_mg = 0
            dosing_schedule = "No dosing information available."

        return dose_mg, dosing_schedule


if 'token' not in st.session_state:
    st.switch_page('main.py')
else:
    App().render_page()
