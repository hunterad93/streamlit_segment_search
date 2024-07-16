import streamlit as st
import uuid

class StateManager:
    @staticmethod
    def reset():
        st.session_state.stage = 0
        st.session_state.company_name = ""
        st.session_state.extracted_audience_json = None
        st.session_state.old_audience_json = None
        st.session_state.conversation_history = []
        st.session_state.user_comment = ""
        st.session_state.summary_results = None
        st.session_state.audience_report = None
        st.session_state.final_report = None
        st.session_state.session_id = str(uuid.uuid4())

    @staticmethod
    def update(**kwargs):
        for key, value in kwargs.items():
            if key in st.session_state:
                st.session_state[key] = value
            else:
                raise AttributeError(f"State has no attribute '{key}'")

    @staticmethod
    def get(attr):
        return st.session_state.get(attr)

    @staticmethod
    def increment_stage():
        st.session_state.stage += 1

    @staticmethod
    def add_to_conversation(role, content):
        st.session_state.conversation_history.append({"role": role, "content": content})

    @staticmethod
    def clear_audience_data():
        st.session_state.extracted_audience_json = None
        st.session_state.conversation_history = []
        st.session_state.summary_results = None
        st.session_state.audience_report = None

# No need for get_state() function or global state variable