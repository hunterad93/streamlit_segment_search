import streamlit as st
import uuid

class State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.stage = 0
        self.company_name = ""
        self.extracted_audience_json = None
        self.old_audience_json = None
        self.conversation_history = []
        self.user_comment = ""
        self.summary_results = None
        self.audience_report = None
        self.final_report = None
        self.session_id = str(uuid.uuid4())

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"State has no attribute '{key}'")

    def get(self, attr):
        return getattr(self, attr)

    def increment_stage(self):
        self.stage += 1

    def add_to_conversation(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def clear_audience_data(self):
        self.extracted_audience_json = None
        self.conversation_history = []
        self.summary_results = None
        self.audience_report = None

def get_state():
    if 'app_state' not in st.session_state:
        st.session_state.app_state = State()
    return st.session_state.app_state

# Use this to access state in your app
state = get_state()