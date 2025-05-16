import streamlit as st
import os
import base64
from pathlib import Path

# Import utilities
from utils.lilypond_finder import find_lilypond
from utils.file_converter import convert_lilypond_to_pdf_midi
from utils.midi_player import add_midi_player

# Import components
from components.templates import show_templates_ui
from components.chord_helper import create_chord_helper
from components.instrument_ref import create_instrument_reference
from components.version_history import setup_version_history, show_version_history

# Import styles
from assets.styles import apply_custom_styles

# App configuration
st.set_page_config(
    page_title="LilyPond to PDF Converter",
    page_icon="🎵",
    layout="wide"
)

# Apply custom styles
apply_custom_styles()

# Initialize session state
if 'pdf_generated' not in st.session_state:
    st.session_state.pdf_generated = False
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = None
if 'midi_data' not in st.session_state:
    st.session_state.midi_data = None
if 'midi_filename' not in st.session_state:
    st.session_state.midi_filename = None
if 'ly_text' not in st.session_state:
    st.session_state.ly_text = ""

# Title and description
st.title("LilyPond to PDF Converter")
st.markdown("""
This app converts LilyPond notation to PDF sheet music and MIDI files.
""")

# Check if LilyPond is installed
lilypond_path = find_lilypond()

# Display LilyPond status
if lilypond_path:
    st.success(f"✅ LilyPond found at: {lilypond_path}")
else:
    st.error("❌ LilyPond not found. You need to install LilyPond on the server running this app.")
    st.info("Download LilyPond from [lilypond.org](https://lilypond.org/download.html)")

# Setup sidebar
with st.sidebar:
    st.image("https://lilypond.org/pictures/double-lily-modified3.png", width=100)
    st.header("LilyPond Converter")
    
    # Add helpful resources
    st.markdown("### LilyPond Resources")
    st.markdown("""
    - [LilyPond Documentation](https://lilypond.org/doc/v2.20/Documentation/notation/index.html)
    - [LilyPond Cheat Sheet](https://lilypond.org/doc/v2.20/Documentation/notation/cheat-sheet)
    - [LilyPond Snippet Repository](https://lsr.di.unimi.it/)
    """)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Input Text",
    "📂 Upload File",
    "🎹 Chord Helper",
    "🎻 Instrument Reference",
    "📚 Version History"
])

# Tab 1: Input Text
with tab1:
    # Template selector
    template = show_templates_ui()
    if template:
        st.session_state.ly_text = template
    
    # Text input area
    st.subheader("Enter LilyPond Notation")
    
    # Button to load sample (using your existing piano_sheet)
    piano_sheet = r"""[your piano sample]"""
    if st.button("Load Sample"):
        ly_text = piano_sheet
        # Clear previous generated files when loading new content
        st.session_state.pdf_generated = False
    else:
        ly_text = st.session_state.get('ly_text', '')
    
    # Setup version history in tab 1
    setup_version_history()
    
    text_area = st.text_area("LilyPond Code", value=ly_text, height=400)
    
    # Clear previous generated files if text changes
    if 'ly_text' in st.session_state and st.session_state.ly_text != text_area:
        st.session_state.pdf_generated = False
    
    st.session_state['ly_text'] = text_area
    
    # Output options
    output_filename = st.text_input("Output Filename", value="my_sheet_music")
    
    # Convert button
    convert_text = st.button("Convert to PDF", key="convert_text", disabled=not lilypond_path)

# Tab 2: File Upload
with tab2:
    # File upload
    st.subheader("Upload LilyPond File")
    uploaded_file = st.file_uploader("Choose a LilyPond file", type=['ly'])
    
    # Clear previous generated files if a new file is uploaded
    if uploaded_file is not None and 'last_uploaded_file' in st.session_state:
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.pdf_generated = False
            st.session_state.last_uploaded_file = uploaded_file.name
    elif uploaded_file is not None:
        st.session_state.last_uploaded_file = uploaded_file.name
    
    # Output options for file upload
    if uploaded_file is not None:
        # Default filename from uploaded file
        default_name = os.path.splitext(uploaded_file.name)[0]
    else:
        default_name = "output"
        
    output_filename_file = st.text_input("Output Filename", value=default_name, key="file_output")
    
    # Convert button
    convert_file = st.button("Convert to PDF", key="convert_file", disabled=not lilypond_path or uploaded_file is None)

# Tab 3: Chord Helper
with tab3:
    create_chord_helper()

# Tab 4: Instrument Reference
with tab4:
    create_instrument_reference()

# Tab 5: Version History
with tab5:
    show_version_history()

# Display download buttons if files have been generated
if st.session_state.pdf_generated:
    st.success("Files generated successfully!")
    
    # Create download buttons for both PDF and MIDI
    if st.session_state.pdf_data is not None:
        st.download_button(
            label="Download PDF",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_filename,
            mime="application/octet-stream",
            key="pdf_download"
        )
    
    if st.session_state.midi_data is not None:
        st.download_button(
            label="Download MIDI",
            data=st.session_state.midi_data,
            file_name=st.session_state.midi_filename,
            mime="audio/midi",
            key="midi_download"
        )
        
        # Add MIDI player
        add_midi_player(st.session_state.midi_data)
    
    st.info("PDF preview not available in browser. Please download the PDF to view it.")

# Processing logic
if convert_text and lilypond_path:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    # Get LilyPond content
    ly_content = text_area
    output_name = output_filename
    
    # Convert to PDF/MIDI
    pdf_data, pdf_filename, midi_data, midi_filename, error = convert_lilypond_to_pdf_midi(
        ly_content, output_name, lilypond_path
    )
    
    if error:
        status_container.error(error)
    else:
        # Store in session state
        st.session_state.pdf_data = pdf_data
        st.session_state.pdf_filename = pdf_filename
        st.session_state.midi_data = midi_data
        st.session_state.midi_filename = midi_filename
        st.session_state.pdf_generated = True
        
        # Remove status message as we'll show success in the permanent UI
        status_container.empty()
        
        # Force a rerun to show the download buttons
        st.rerun()

elif convert_file and lilypond_path:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    # Read uploaded file
    ly_content = uploaded_file.getvalue().decode("utf-8")
    output_name = output_filename_file
    
    # Convert to PDF/MIDI
    pdf_data, pdf_filename, midi_data, midi_filename, error = convert_lilypond_to_pdf_midi(
        ly_content, output_name, lilypond_path
    )
    
    if error:
        status_container.error(error)
    else:
        # Store in session state
        st.session_state.pdf_data = pdf_data
        st.session_state.pdf_filename = pdf_filename
        st.session_state.midi_data = midi_data
        st.session_state.midi_filename = midi_filename
        st.session_state.pdf_generated = True
        
        # Remove status message as we'll show success in the permanent UI
        status_container.empty()
        
        # Force a rerun to show the download buttons
        st.rerun()

# Footer with instructions
st.markdown("---")
st.markdown("""
### How to Use This App
1. Enter LilyPond notation or upload a .ly file
2. Set your desired output filename
3. Click "Convert to PDF"
4. Download the generated PDF and MIDI files

### About LilyPond
[LilyPond](https://lilypond.org/) is an open-source music engraving program that produces beautiful sheet music.
This app requires LilyPond to be installed on the server where Streamlit is running.
""")