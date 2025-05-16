import streamlit as st
import os
import subprocess
import tempfile
import base64
from pathlib import Path
import platform

# ===== CONFIGURATION =====
st.set_page_config(
    page_title="LilyPond to PDF Converter",
    page_icon="🎵",
    layout="wide"
)

# ===== UTILITY FUNCTIONS =====
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

def convert_lilypond(ly_content, output_name, lilypond_path):
    """Convert LilyPond content to PDF and MIDI files."""
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary LilyPond file
            temp_ly_path = os.path.join(temp_dir, "score.ly")
            with open(temp_ly_path, 'w') as f:
                f.write(ly_content)
            
            # Run LilyPond
            result = subprocess.run(
                [lilypond_path, '--output=' + temp_dir, temp_ly_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return None, None, None, None, f"LilyPond Error: {result.stderr}"
            
            # Check if PDF was generated
            temp_pdf_path = os.path.join(temp_dir, "score.pdf")
            if not os.path.exists(temp_pdf_path):
                return None, None, None, None, "LilyPond did not generate a PDF."
            
            # Copy to a more permanent location within the streamlit cache
            cache_dir = os.path.join(tempfile.gettempdir(), "streamlit_lilypond_cache")
            os.makedirs(cache_dir, exist_ok=True)
            final_pdf_path = os.path.join(cache_dir, f"{output_name}.pdf")
            
            import shutil
            shutil.copy2(temp_pdf_path, final_pdf_path)
            
            # Store PDF data in session state
            with open(final_pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
                pdf_filename = f"{output_name}.pdf"
            
            # Also generate MIDI if available
            temp_midi_path = os.path.join(temp_dir, "score.midi")
            midi_data = None
            midi_filename = None
            
            if os.path.exists(temp_midi_path):
                final_midi_path = os.path.join(cache_dir, f"{output_name}.midi")
                shutil.copy2(temp_midi_path, final_midi_path)
                
                with open(final_midi_path, "rb") as midi_file:
                    midi_data = midi_file.read()
                    midi_filename = f"{output_name}.midi"
            
            return pdf_data, pdf_filename, midi_data, midi_filename, None
            
    except Exception as e:
        return None, None, None, None, f"Error during conversion: {str(e)}"

def add_midi_player(midi_data):
    """Add a MIDI player widget to the Streamlit app."""
    if midi_data is None:
        return
    
    # Convert MIDI data to base64
    b64_midi = base64.b64encode(midi_data).decode()
    
    # Use JavaScript to play MIDI in the browser
    st.markdown("### MIDI Preview")
    st.info("Player loading... If you don't see the player below, your browser may not support MIDI playback.")
    
    midi_js = """
    <script src="https://cdn.jsdelivr.net/npm/midi-player-js@2.0.16/browser/midiplayer.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/soundfont-player@0.12.0/dist/soundfont-player.min.js"></script>
    
    <div id="midi-player" style="width:100%; padding:10px; border:1px solid #ddd; border-radius:5px;">
        <button id="play-button" style="padding:5px 15px; margin-right:10px;">Play</button>
        <button id="stop-button" style="padding:5px 15px;">Stop</button>
        <div id="midi-status" style="margin-top:10px;">Ready to play</div>
    </div>
    
    <script>
        // Decode base64 MIDI
        const midiBase64 = "%s";
        const midiBlob = base64ToBlob(midiBase64, 'audio/midi');
        const midiURL = URL.createObjectURL(midiBlob);
        
        // Initialize player
        const player = new MidiPlayer.Player();
        let instrument;
        
        // Load soundfont
        Soundfont.instrument(new AudioContext(), 'acoustic_grand_piano').then(function(piano) {
            instrument = piano;
            document.getElementById('midi-status').textContent = 'MIDI loaded and ready';
            
            // Load the MIDI file
            fetch(midiURL)
                .then(response => response.arrayBuffer())
                .then(buffer => {
                    const midiArrayBuffer = new Uint8Array(buffer);
                    player.loadArrayBuffer(midiArrayBuffer);
                    
                    // Set up event handlers
                    player.on('midiEvent', function(event) {
                        if (event.name === 'Note on') {
                            instrument.play(event.noteNumber, 0, {gain: event.velocity/100});
                        }
                    });
                });
        });
        
        // Event listeners
        document.getElementById('play-button').addEventListener('click', function() {
            if (player.isPlaying()) {
                player.pause();
                this.textContent = 'Resume';
                document.getElementById('midi-status').textContent = 'Paused';
            } else {
                player.play();
                this.textContent = 'Pause';
                document.getElementById('midi-status').textContent = 'Playing...';
            }
        });
        
        document.getElementById('stop-button').addEventListener('click', function() {
            player.stop();
            document.getElementById('play-button').textContent = 'Play';
            document.getElementById('midi-status').textContent = 'Stopped';
        });
        
        // Helper function to convert base64 to Blob
        function base64ToBlob(base64, mimeType) {
            const byteString = atob(base64);
            const ab = new ArrayBuffer(byteString.length);
            const ia = new Uint8Array(ab);
            
            for (let i = 0; i < byteString.length; i++) {
                ia[i] = byteString.charCodeAt(i);
            }
            
            return new Blob([ab], { type: mimeType });
        }
    </script>
    """ % b64_midi
    
    st.components.v1.html(midi_js, height=150)

# ===== INSTRUMENT TEMPLATES =====
# Create a dictionary of templates
instrument_templates = {
    "Piano Solo": r"""[Your piano template goes here]""",
    "String Quartet": r"""[Your string quartet template goes here]""",
    # Add more templates
}

def create_chord_helper():
    """Create the chord progression helper UI."""
    st.header("Chord Progression Helper")
    
    # Key selection
    keys = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
    selected_key = st.selectbox("Select Key", keys)
    
    # Scale type
    scale_types = ["Major", "Minor", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian"]
    selected_scale = st.selectbox("Scale Type", scale_types)
    
    # Chord progression style
    progression_styles = {
        "Pop/Rock I-V-vi-IV": ["I", "V", "vi", "IV"],
        "Jazz ii-V-I": ["ii", "V", "I"],
        "Blues I-IV-I-V-IV-I": ["I", "IV", "I", "V", "IV", "I"],
        "50s Doo-Wop I-vi-IV-V": ["I", "vi", "IV", "V"],
        "Canon in D": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
        "Emotional vi-IV-I-V": ["vi", "IV", "I", "V"],
        "Custom": []
    }
    
    selected_style = st.selectbox("Chord Progression Style", list(progression_styles.keys()))
    
    # Custom progression input
    if selected_style == "Custom":
        custom_progression = st.text_input("Enter custom progression (e.g., I IV V vi):")
        if custom_progression:
            progression = custom_progression.split()
        else:
            progression = []
    else:
        progression = progression_styles[selected_style]
        st.write(f"Progression: {' - '.join(progression)}")

    # Display chords in the selected key
    if progression:
        st.subheader("Chords in this progression:")
        
        # Define notes for each key
        all_notes = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
        key_index = keys.index(selected_key)
        
        # Define scale degree offsets based on scale type
        scale_offsets = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor": [0, 2, 3, 5, 7, 8, 10],
            "Dorian": [0, 2, 3, 5, 7, 9, 10],
            "Phrygian": [0, 1, 3, 5, 7, 8, 10],
            "Lydian": [0, 2, 4, 6, 7, 9, 11],
            "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "Locrian": [0, 1, 3, 5, 6, 8, 10]
        }
        
        # Define chord qualities based on scale type
        chord_qualities = {
            "Major": ["", "m", "m", "", "", "m", "dim"],
            "Minor": ["m", "dim", "", "m", "m", "", ""],
            "Dorian": ["m", "m", "", "", "m", "dim", ""],
            "Phrygian": ["m", "", "", "m", "dim", "", "m"],
            "Lydian": ["", "", "", "dim", "", "m", "m"],
            "Mixolydian": ["", "m", "dim", "", "m", "m", ""],
            "Locrian": ["dim", "", "m", "m", "", "", "m"]
        }
        
        # Roman numeral to index mapping
        numeral_to_index = {
            "I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6,
            "i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6
        }
        
        # Generate chord chart
        chords = []
        chord_notes = []
        
        offsets = scale_offsets[selected_scale]
        qualities = chord_qualities[selected_scale]
        
        for numeral in progression:
            # Strip any modifiers for index lookup
            base_numeral = ''.join(c for c in numeral if c.isalpha())
            idx = numeral_to_index.get(base_numeral, 0)
            
            # Get the note for this degree
            note_idx = (key_index + offsets[idx]) % 12
            note = all_notes[note_idx]
            
            # Determine quality, handling any accidentals in the numeral
            quality = qualities[idx]
            if 'dim' in numeral:
                quality = 'dim'
            elif 'aug' in numeral:
                quality = 'aug'
            elif '°' in numeral:
                quality = 'dim'
            elif '+' in numeral:
                quality = 'aug'
            elif 'sus' in numeral:
                quality = 'sus4'
            
            chords.append(f"{note}{quality}")
            
            # Get chord notes (simplified for display)
            if quality == "":  # Major
                third_idx = (note_idx + 4) % 12
                fifth_idx = (note_idx + 7) % 12
                chord_notes.append(f"{note} {all_notes[third_idx]} {all_notes[fifth_idx]}")
            elif quality == "m":  # Minor
                third_idx = (note_idx + 3) % 12
                fifth_idx = (note_idx + 7) % 12
                chord_notes.append(f"{note} {all_notes[third_idx]} {all_notes[fifth_idx]}")
            elif quality == "dim":  # Diminished
                third_idx = (note_idx + 3) % 12
                fifth_idx = (note_idx + 6) % 12
                chord_notes.append(f"{note} {all_notes[third_idx]} {all_notes[fifth_idx]}")
            elif quality == "aug":  # Augmented
                third_idx = (note_idx + 4) % 12
                fifth_idx = (note_idx + 8) % 12
                chord_notes.append(f"{note} {all_notes[third_idx]} {all_notes[fifth_idx]}")
            else:
                chord_notes.append("Custom chord")
        
        # Display the results in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Chord Names")
            for i, chord in enumerate(chords):
                st.write(f"{progression[i]}: **{chord}**")
                
        with col2:
            st.write("### Chord Notes")
            for i, notes in enumerate(chord_notes):
                st.write(f"{progression[i]}: {notes}")
                
        # Generate LilyPond representation
        st.subheader("LilyPond Representation")
        lily_chords = []
        
        for chord in chords:
            # Convert chord name to LilyPond notation
            note, *quality = chord[0], chord[1:]
            note = note.lower()  # LilyPond uses lowercase
            
            quality_str = ''.join(quality)
            
            if "dim" in quality_str:
                lily_chords.append(f"{note}:dim")
            elif "m" in quality_str:
                lily_chords.append(f"{note}:m")
            elif "aug" in quality_str:
                lily_chords.append(f"{note}:aug")
            elif "sus4" in quality_str:
                lily_chords.append(f"{note}:sus4")
            else:
                lily_chords.append(f"{note}")
        
        # Create basic LilyPond snippet
        lily_code = f"""\\version "2.20.0"

\\header {{
  title = "{selected_style} in {selected_key} {selected_scale}"
}}

\\score {{
  \\new ChordNames {{
    \\chordmode {{
      {" | ".join(lily_chords)} |
    }}
  }}
  \\new Staff {{
    \\clef treble
    \\key {selected_key.lower().replace('#', 'is').replace('b', 'es')} \\{selected_scale.lower()}
    \\time 4/4
    \\improvisationOn
    c'1 | c' | c' | c' |
  }}
  \\layout {{ }}
}}
"""
        
        st.code(lily_code, language="lilypond")
        
        if st.button("Use This Progression"):
            st.session_state.ly_text = lily_code
            st.success("Chord progression added to editor! Switch to the Input Text tab to view and edit.")

# Add instrument reference function and version history functions
# [Add those functions here]

# ===== MAIN APP =====
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

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Input Text", "📂 Upload File", "🎹 Chord Helper"])

# Tab 1: Input Text
with tab1:
    st.subheader("Enter LilyPond Notation")
    
    # Template selector
    st.subheader("Choose Template")
    template_choice = st.selectbox(
        "Select an instrument ensemble template",
        options=list(instrument_templates.keys()),
        index=0
    )
    
    # Button to load selected template
    if st.button("Load Template"):
        st.session_state.ly_text = instrument_templates[template_choice]
        st.session_state.pdf_generated = False
        st.rerun()
    
    # Text input area
    piano_sheet = r"""[Your sample piano sheet code]"""
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
    
    # Output options
    output_filename = st.text_input("Output Filename", value="my_sheet_music")
    
    # Convert button
    convert_text = st.button("Convert to PDF", key="convert_text", disabled=not lilypond_path)

# Tab 2: File Upload
with tab2:
    # File upload functionality
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
    
    st.info("PDF preview is not available due to browser security restrictions. Please download the PDF to view it.")

# Processing logic
if convert_text and lilypond_path:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    # Get LilyPond content
    ly_content = text_area
    output_name = output_filename
    
    # Convert to PDF/MIDI
    pdf_data, pdf_filename, midi_data, midi_filename, error = convert_lilypond(
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

elif convert_file and lilypond_path and uploaded_file is not None:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    # Read uploaded file
    ly_content = uploaded_file.getvalue().decode("utf-8")
    output_name = output_filename_file
    
    # Convert to PDF/MIDI
    pdf_data, pdf_filename, midi_data, midi_filename, error = convert_lilypond(
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