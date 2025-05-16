# Instrument template definitions
instrument_templates = {
    "Piano Solo": r"""[your piano template]""",
    "String Quartet": r"""[your string quartet template]""",
    # Add the rest of your templates
}

def show_templates_ui():
    """
    Display the templates UI.
    Returns the selected template if the button is pressed, None otherwise.
    """
    import streamlit as st
    
    st.subheader("Choose Template")
    template_choice = st.selectbox(
        "Select an instrument ensemble template",
        options=list(instrument_templates.keys()),
        index=0
    )
    
    # Button to load selected template
    if st.button("Load Template"):
        return instrument_templates[template_choice]
    
    return None