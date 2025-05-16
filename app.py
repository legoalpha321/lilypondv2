import streamlit as st
import os
import subprocess
import tempfile
import base64
from pathlib import Path
import platform
import re

st.set_page_config(
    page_title="LilyPond to PDF Converter",
    page_icon="🎵",
    layout="wide"
)

# Title and description
st.title("LilyPond to PDF Converter")
st.markdown("""
This app converts LilyPond notation to PDF sheet music and MIDI files.
""")

# Function to extract title from LilyPond code
def extract_title_from_lilypond(ly_content):
    """Extract the title from LilyPond header."""
    # Look for the header block
    header_match = re.search(r'\\header\s*{([^}]*)}', ly_content, re.DOTALL)
    if not header_match:
        return None
        
    header_content = header_match.group(1)
    
    # Look for the title within the header
    title_match = re.search(r'title\s*=\s*"([^"]*)"', header_content)
    if title_match:
        title = title_match.group(1)
        # Convert title to a valid filename by replacing problematic characters
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        return safe_title
    
    return None

# Check if LilyPond is installed on the server
@st.cache_resource
def find_lilypond():
    """Attempt to find the LilyPond executable on the system."""
    try:
        # Try to get LilyPond version which will fail if not installed
        result = subprocess.run(['lilypond', '--version'], 
                                capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return 'lilypond'  # It's in the PATH
    except FileNotFoundError:
        pass
        
    # Common installation paths to check
    common_paths = []
    
    # Windows common paths
    if os.name == 'nt':
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        for base_dir in [program_files, program_files_x86]:
            common_paths.extend([
                os.path.join(base_dir, 'LilyPond', 'usr', 'bin', 'lilypond.exe'),
                os.path.join(base_dir, 'LilyPond', 'bin', 'lilypond.exe')
            ])
    
    # macOS common paths
    elif platform.system() == 'darwin':
        common_paths.extend([
            '/Applications/LilyPond.app/Contents/Resources/bin/lilypond',
            os.path.expanduser('~/Applications/LilyPond.app/Contents/Resources/bin/lilypond')
        ])
    
    # Linux common paths
    else:
        common_paths.extend([
            '/usr/bin/lilypond',
            '/usr/local/bin/lilypond'
        ])
    
    # Check each path
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
            
    return None

lilypond_path = find_lilypond()

# Display LilyPond status
if lilypond_path:
    st.success(f"✅ LilyPond found at: {lilypond_path}")
else:
    st.error("❌ LilyPond not found. You need to install LilyPond on the server running this app.")
    st.info("Download LilyPond from [lilypond.org](https://lilypond.org/download.html)")

# Piano sheet sample
piano_sheet = r"""\version "2.20.0"

\header {
  title = "Ascension"
  subtitle = "An Epic Piano Journey"
  composer = "Composed for You"
}

\paper {
  #(set-paper-size "letter")
}

global = {
  \key d \major
  \time 4/4
  \tempo "With passion" 4 = 72
}

upper = \relative c'' {
  \global
  \clef treble
  
  % Introduction - Majestic and contemplative
  \partial 4 a4\mp |
  <d fis a>2. <cis e a>4 |
  <b d g>2. <a d fis>4 |
  <g b e>2 <fis a d>2 |
  <e a cis>2. a,4\< |
  
  <d fis a>2.\mf <e g b>4 |
  <fis a d>2. <g b e>4 |
  <a cis e>2 <b d fis>2 |
  <a cis e>2. r4\! |
  
  % Main theme - Hopeful and building
  d,4\mp\< fis a d |
  cis4. b8 a4 fis |
  b4. a8 g4 d |
  e4. fis8 g4\mf a\> |
  
  d,4\mp fis a d |
  e4. d8 cis4 a |
  b4. a8 g4 e |
  fis2\> d2\mp\! |
  
  % First few measures of the piece for brevity
  \bar "|."
}

lower = \relative c {
  \global
  \clef bass
  
  % Introduction
  \partial 4 r4 |
  d4 a' d, a' |
  g,4 d' g, d' |
  e,4 b' e, b' |
  a,4 e' a, e' |
  
  d4 a' d, a' |
  d,4 a' d, a' |
  a,4 e' a, e' |
  a,4 e' a, e' |
  
  % Main theme
  d4 a' fis a |
  a,4 e' a, e' |
  g,4 d' g, d' |
  a4 e' a, e' |
  
  d4 a' fis a |
  a,4 e' a, e' |
  g,4 d' g, d' |
  a4 d fis a |
  
  \bar "|."
}

\score {
  \new PianoStaff <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout { }
  \midi { }
}"""

# Create tabs
tab1, tab2 = st.tabs(["Input Text", "Upload File"])

# Initialize session state for storing generated files
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

with tab1:
    # Text input area
    st.subheader("Enter LilyPond Notation")
    
    # Button to load sample
    if st.button("Load Sample"):
        ly_text = piano_sheet
        # Clear previous generated files when loading new content
        st.session_state.pdf_generated = False
    else:
        ly_text = st.session_state.get('ly_text', '')
    
    text_area = st.text_area("LilyPond Code", value=ly_text, height=400)
    
    # Clear previous generated files if text changes
    if 'ly_text' in st.session_state and st.session_state.ly_text != text_area:
        st.session_state.pdf_generated = False
    
    st.session_state['ly_text'] = text_area
    
    # Try to extract title from the LilyPond code for the default filename
    extracted_title = extract_title_from_lilypond(text_area)
    default_filename = extracted_title if extracted_title else "my_sheet_music"
    
    # Output options
    output_filename = st.text_input("Output Filename", value=default_filename)

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
        # Try to extract title from the uploaded file
        uploaded_content = uploaded_file.getvalue().decode("utf-8")
        extracted_title = extract_title_from_lilypond(uploaded_content)
        if extracted_title:
            default_name = extracted_title
        else:
            # Use filename if no title in header
            default_name = os.path.splitext(uploaded_file.name)[0]
    else:
        default_name = "output"
        
    output_filename_file = st.text_input("Output Filename", value=default_name, key="file_output")

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
    
    st.info("PDF preview is not available due to browser security restrictions. Please download the PDF to view it.")

# Convert buttons
convert_text = st.button("Convert to PDF", key="convert_text", disabled=not lilypond_path)
convert_file = st.button("Convert to PDF", key="convert_file", disabled=not lilypond_path or uploaded_file is None)

# Processing logic
if (convert_text or convert_file) and lilypond_path:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get LilyPond content
            if convert_text:
                ly_content = text_area
                output_name = output_filename
            else:  # convert_file
                if uploaded_file is None:
                    st.error("Please upload a LilyPond file.")
                    st.stop()
                    
                # Read uploaded file
                ly_content = uploaded_file.getvalue().decode("utf-8")
                output_name = output_filename_file
            
            # Create temporary LilyPond file
            temp_ly_path = os.path.join(temp_dir, "score.ly")
            with open(temp_ly_path, 'w') as f:
                f.write(ly_content)
            
            # Run LilyPond
            status_container.info("Running LilyPond...")
            result = subprocess.run(
                [lilypond_path, '--output=' + temp_dir, temp_ly_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                status_container.error(f"LilyPond Error: {result.stderr}")
                st.stop()
            
            # Check if PDF was generated
            temp_pdf_path = os.path.join(temp_dir, "score.pdf")
            if not os.path.exists(temp_pdf_path):
                status_container.error("LilyPond did not generate a PDF.")
                st.stop()
            
            # Copy to a more permanent location within the streamlit cache
            cache_dir = os.path.join(tempfile.gettempdir(), "streamlit_lilypond_cache")
            os.makedirs(cache_dir, exist_ok=True)
            final_pdf_path = os.path.join(cache_dir, f"{output_name}.pdf")
            
            import shutil
            shutil.copy2(temp_pdf_path, final_pdf_path)
            
            # Store PDF data in session state
            with open(final_pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
                st.session_state.pdf_data = pdf_data
                st.session_state.pdf_filename = f"{output_name}.pdf"
            
            # Also generate MIDI if available
            temp_midi_path = os.path.join(temp_dir, "score.midi")
            if os.path.exists(temp_midi_path):
                final_midi_path = os.path.join(cache_dir, f"{output_name}.midi")
                shutil.copy2(temp_midi_path, final_midi_path)
                
                with open(final_midi_path, "rb") as midi_file:
                    midi_data = midi_file.read()
                    st.session_state.midi_data = midi_data
                    st.session_state.midi_filename = f"{output_name}.midi"
            else:
                st.session_state.midi_data = None
                st.session_state.midi_filename = None
            
            # Mark as successful
            st.session_state.pdf_generated = True
            
            # Remove status message as we'll show success in the permanent UI
            status_container.empty()
            
            # Force a rerun to show the download buttons
            st.rerun()
    
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")


if st.session_state.midi_data is not None:
    st.subheader("MIDI Preview")
    midi_b64 = base64.b64encode(st.session_state.midi_data).decode()
    midi_player = f"""
    <div style='margin-bottom: 20px;'>
        <audio controls>
            <source src="data:audio/midi;base64,{midi_b64}" type="audio/midi">
            Your browser does not support the audio element.
        </audio>
    </div>
    """
    st.markdown(midi_player, unsafe_allow_html=True)
    
    # Alternative HTML5 player for better MIDI support
    st.markdown("### Advanced MIDI Player")
    st.markdown(f"""
    <div id="player-container" style="width:100%; margin-bottom:20px;">
        <script src="https://cdn.jsdelivr.net/npm/midi-player-js@2.0.16/build/midi-player-js.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/soundfont-player@0.12.0/dist/soundfont-player.min.js"></script>
        
        <div style="padding: 20px; border-radius: 5px; background-color: #f8f9fa;">
            <button id="play" class="button">Play</button>
            <button id="pause" class="button">Pause</button>
            <button id="stop" class="button">Stop</button>
            <div id="loading">Loading MIDI...</div>
        </div>
        
        <script>
            const midiData = "data:audio/midi;base64,{midi_b64}";
            
            // Wait for the page to load
            window.addEventListener('load', function() {{
                const Player = new MidiPlayer.Player(function(event) {{
                    // Handle events
                }});
                
                // Load MIDI file
                fetch(midiData)
                    .then(response => response.arrayBuffer())
                    .then(buffer => {{
                        const loadingMessage = document.getElementById('loading');
                        loadingMessage.innerHTML = "MIDI loaded successfully";
                        Player.loadArrayBuffer(buffer);
                        
                        // Setup player controls
                        document.getElementById('play').addEventListener('click', function() {{
                            Player.play();
                        }});
                        
                        document.getElementById('pause').addEventListener('click', function() {{
                            Player.pause();
                        }});
                        
                        document.getElementById('stop').addEventListener('click', function() {{
                            Player.stop();
                        }});
                    }})
                    .catch(error => {{
                        console.error('Error loading MIDI:', error);
                        document.getElementById('loading').innerHTML = "Error loading MIDI";
                    }});
            }});
        </script>
        <style>
            .button {{
                padding: 8px 16px;
                margin-right: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
        </style>
    </div>
    """, unsafe_allow_html=True)



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