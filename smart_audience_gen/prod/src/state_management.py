import streamlit as st
import uuid
import copy

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
        st.session_state.use_presearch_filter = False
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.post_search_results = None
        st.session_state.last_feedback = ""
        st.session_state.state_backup = None
        st.session_state.user_feedback = ""


    @staticmethod
    def update(**kwargs):
        # Create a backup before updating
        StateManager.create_backup()
        
        for key, value in kwargs.items():
            if key in st.session_state:
                st.session_state[key] = value
            else:
                raise AttributeError(f"State has no attribute '{key}'")

    @staticmethod
    def get(attr):
        return st.session_state.get(attr)
    
    @staticmethod
    def create_backup():
        # Create a deep copy of the current state
        backup = {key: copy.deepcopy(value) for key, value in st.session_state.items() if key != 'state_backup' and key != 'last_feedback'}
        st.session_state.state_backup = backup

    @staticmethod
    def restore_backup():
        if st.session_state.state_backup:
            for key, value in st.session_state.state_backup.items():
                try:
                    st.session_state[key] = value
                except Exception as e:
                    print(f"Error restoring state for key {key}: {e}")
            st.session_state.state_backup = None
        else:
            st.warning("No backup available to restore.")

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

