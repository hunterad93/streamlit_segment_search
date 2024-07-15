import streamlit as st

class State:
    def __init__(self):
        self.stage = 0
        self.company_name = ""
        self.extracted_audience_json = None
        self.old_audience_json = None
        self.conversation_history = []
        self.user_comment = ""
        self.summary_results = None
        self.audience_report = None
        self.final_report = None

    def reset(self):
        self.__init__()

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
    if 'state' not in st.session_state:
        st.session_state.state = State()
    return st.session_state.state

# Global state instance
state = get_state()