import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

st.set_page_config(layout="wide")
model1 = joblib.load('models/CoxPH.pkl')
model2 = joblib.load('models/EST.pkl')
model3 = joblib.load('models/GBS.pkl')
model4 = joblib.load('models/RSF.pkl')


@st.cache(show_spinner=False)
def load_setting():
    settings = {
        'Age': {'values': ["<79", ">=79"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Sex': {'values': ["Male", "Female"], 'type': 'radio', 'init_value': 0, 'add_after': ''},
        'Race': {'values': ["Black", "Other", "White"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Laterality': {'values': ["Left", "Right"], 'type': 'radio', 'init_value': 0, 'add_after': ''},
        'T_stage': {'values': ["T1", "T2", "T3", "T4"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'N_stage': {'values': ["N0", "N1", "N2", "N3"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'M_stage': {'values': ["M0", "M1"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Marital': {'values': ["Married", "Other"], 'type': 'radio', 'init_value': 0, 'add_after': ''},
        'Grade': {'values': ["I-II", "III-IV", "Unknown"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Tumor_size': {'values': ["28-52", "<28", ">52", "Unknown"], 'type': 'selectbox', 'init_value': 0,
                       'add_after': ', mm'},
        'Primary_site': {'values': ["L_NOS", "Lower", "Middle", "Other", "Upper"], 'type': 'selectbox',
                         'init_value': 0, 'add_after': ''},
        'Chemotherapy': {'values': ["No/Unknown", "Yes"], 'type': 'radio', 'init_value': 0, 'add_after': ''},
        'Surgery_group': {'values': ["Lobectomy", "No_Surgery", "Other_Surgery"], 'type': 'selectbox',
                          'init_value': 0,
                          'add_after': ''},
        'Radiation': {'values': ["No/Unknown", "Yes"], 'type': 'radio', 'init_value': 0, 'add_after': ''},
        'Model': {'values': ["CoxPH", "GBS", "EST", "RSF"], 'type': 'selectbox',
                  'init_value': 0, 'add_after': ''},
    }
    input_keys = ['Age', 'Sex', 'Race', 'Laterality', 'T_stage', 'N_stage',
                  'M_stage', 'Marital', 'Grade', 'Tumor_size', 'Primary_site',
                  'Chemotherapy', 'Surgery_group', 'Radiation', 'Model']
    return settings, input_keys


settings, input_keys = load_setting()


def load_model(val):
    model = ''
    if val == 'CoxPH':
        model = model1
    elif val == 'EST':
        model = model2
    elif val == 'GBS':
        model = model3
    elif val == 'RSF':
        model = model4
    return model


def get_code():
    sidebar_code = []
    for key in settings:
        if settings[key]['type'] == 'slider':
            sidebar_code.append(
                "{} = st.slider('{}',{},{},key='{}')".format(
                    key.replace(' ', '____'),
                    key + settings[key]['add_after'],
                    # settings[key]['values'][0],
                    ','.join(['{}'.format(value) for value in settings[key]['values']]),
                    settings[key]['init_value'],
                    key
                )
            )
        if settings[key]['type'] == 'selectbox':
            sidebar_code.append('{} = st.selectbox("{}",({}),{},key="{}")'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
                key
            )
            )
        if settings[key]['type'] == 'radio':
            sidebar_code.append('{} = st.radio("{}",({}),{},key="{}")'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
                key
            )
            )
    return sidebar_code


sidebar_code = get_code()

if 'patients' not in st.session_state:
    st.session_state['patients'] = []
if 'display' not in st.session_state:
    st.session_state['display'] = 1


def plot_survival():
    pd_data = pd.concat(
        [
            pd.DataFrame(
                {
                    'Survival': item['survival'],
                    'Time': item['times'],
                    'Patients': [item['No'] for i in item['times']]
                }
            ) for item in st.session_state['patients']
        ]
    )
    if st.session_state['display']:
        fig = px.line(pd_data, x="Time", y="Survival", color='Patients', range_y=[0, 1])
    else:
        fig = px.line(pd_data.loc[pd_data['Patients'] == pd_data['Patients'].to_list()[-1], :], x="Time", y="Survival",
                      range_y=[0, 1])
    fig.update_layout(title={
                          'text': 'Estimated Survival Probability',
                          'y': 0.9,
                          'x': 0.5,
                          'xanchor': 'center',
                          'yanchor': 'top',
                          'font': dict(
                              size=25
                          )
                      },
                      plot_bgcolor="LightGrey",
                      xaxis_title="Time, month",
                      yaxis_title="Survival probability",
                      )
    st.plotly_chart(fig, use_container_width=True)


def plot_patients():
    patients = pd.concat(
        [
            pd.DataFrame(
                dict(
                    {
                        'Patients': [item['No']],
                        '3-Year': ["{:.2f}%".format(item['3-year'] * 100)],
                        '5-Year': ["{:.2f}%".format(item['5-year'] * 100)],
                        '10-Year': ["{:.2f}%".format(item['10-year'] * 100)]
                    },
                    **item['arg']
                )
            ) for item in st.session_state['patients']
        ]
    ).reset_index(drop=True)
    st.dataframe(patients)


# @st.cache(show_spinner=True)
def predict():
    print('update patients . ##########')
    # print(st.session_state)
    model = load_model(st.session_state["Model"])
    inp = []
    for key in input_keys[:-1]:
        l = []
        value = st.session_state[key]
        l = [0 for i in range(len(settings[key]['values']))]
        l[settings[key]['values'].index(value)] = 1
        inp += l[1:]
    test_df = pd.DataFrame(inp,
                           index=['Age_>=79', 'Sex_Male', 'Race_Other', 'Race_White', 'Laterality_Right',
                                  'T_stage_T2', 'T_stage_T3', 'T_stage_T4', 'N_stage_N1', 'N_stage_N2',
                                  'N_stage_N3', 'M_stage_M1', 'Marital_Other', 'Grade_III-IV',
                                  'Grade_Unknown', 'Tumor_size_<28', 'Tumor_size_>52',
                                  'Tumor_size_Unknown', 'Primary_site_Lower', 'Primary_site_Middle',
                                  'Primary_site_Other', 'Primary_site_Upper', 'Chemotherapy_Yes',
                                  'Surgery_group_No_Surgery', 'Surgery_group_Other_Surgery',
                                  'Radiation_Yes']).T
    survival = model.predict_survival_function(test_df)
    data = {
        'survival': survival[0].y,
        'times': [i for i in range(0, len(survival[0].y))],
        'No': len(st.session_state['patients']) + 1,
        'arg': {key: st.session_state[key] for key in input_keys},
        '3-year': survival[0].y[35],
        '5-year': survival[0].y[59],
        '10-year': survival[0].y[118],
    }
    st.session_state['patients'].append(
        data
    )
    print('update patients ... ##########')


def plot_below_header():
    col1, col2 = st.columns([1, 9])
    col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2])
    with col1:
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        # st.session_state['display'] = ['Single', 'Multiple'].index(
        #     st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        st.session_state['display'] = ['Single', 'Multiple'].index(
            st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        # st.radio("Model", ('DeepSurv', 'NMTLR','RSF','CoxPH'), 0,key='model',on_change=predict())
    with col2:
        plot_survival()
    with col4:
        st.metric(
            label='3-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['3-year'] * 100)
        )
    with col5:
        st.metric(
            label='5-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['5-year'] * 100)
        )
    with col6:
        st.metric(
            label='10-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['10-year'] * 100)
        )
    st.write('')
    st.write('')
    st.write('')
    plot_patients()
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')


st.header('Models for predicting survival of lung papillary adenocarcinoma', anchor='Cancer-specific survival of lung papillary adenocarcinoma')
if st.session_state['patients']:
    plot_below_header()

with st.sidebar:
    with st.form("my_form", clear_on_submit=False):
        for code in sidebar_code:
            exec(code)
        col8, col9, col10 = st.columns([3, 4, 3])
        with col9:
            prediction = st.form_submit_button(
                'Predict',
                on_click=predict,
                # args=[{key: eval(key.replace(' ', '____')) for key in input_keys}]
            )
