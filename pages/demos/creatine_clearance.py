import streamlit as st
from datetime import datetime
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

        patient = st.selectbox(
            label="Patient",
            placeholder="Select Patient",
            index=None if len(patients_result['entry']) > 1 else 0,
            options=map(
                lambda entry: entry['resource'],
                patients_result['entry']
            ),
            format_func=lambda patient: f"{str.join(' ', patient['name'][0]['given'])} {patient['name'][0]['family']}"
        )

        if patient:
            weight_observations = self.fhir.search_resource(
                'Observation',
                {
                    'category': 'vital-signs',
                    'patient': f'{patient["resourceType"]}/{patient["id"]}',
                    'code': 'http://loinc.org|29463-7',
                    '_count': 1
                }
            )

            if weight_observations['total'] == 0:
                st.text('no weight observations found.')
                return

            age = datetime.now().year - int(patient["birthDate"][0:4])
            gender = patient["gender"]
            weight_entry = weight_observations['entry'][0]
            weight_resource = weight_entry['resource']
            weight = weight_resource['valueQuantity']['value']

            st.write(f"Age: {age}")
            st.write(f"Gender: {gender}")
            st.write(f"Weight: {weight}")

            serum_creatinine = st.number_input("Serum Creatinine (umol/L)", min_value=0.1, max_value=1500.0, value=60.0, step=0.1)

            creatinine_clearance = App.cockcroft_gault(weight, serum_creatinine, age, gender)
            st.write(f"Creatinine Clearance: {creatinine_clearance:.2f} ml/min")

    @staticmethod
    def cockcroft_gault(weight, serum_creatinine, age, gender):
        if gender == "male":
            constant = 1
        else:
            constant = 0.85

        # Cockcroft-Gault CrCl, mL/min = (140 – age) × (weight, kg) × (0.85 if female) / (72 × Cr, mg/dL)
        return ((140 - age) * weight * constant) / (72 * serum_creatinine)


if 'token' not in st.session_state:
    st.switch_page('main.py')
else:
    App().render_page()
