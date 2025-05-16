import os
import tempfile
import subprocess
import shutil

def convert_lilypond_to_pdf_midi(lily_content, output_name, lilypond_path):
    """
    Convert LilyPond content to PDF and MIDI files.
    Returns tuple of (pdf_data, pdf_filename, midi_data, midi_filename) or (None, error_message)
    """
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary LilyPond file
            temp_ly_path = os.path.join(temp_dir, "score.ly")
            with open(temp_ly_path, 'w') as f:
                f.write(lily_content)
            
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
            
            shutil.copy2(temp_pdf_path, final_pdf_path)
            
            # Read PDF data
            with open(final_pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
                pdf_filename = f"{output_name}.pdf"
            
            # Check for MIDI
            midi_data = None
            midi_filename = None
            
            temp_midi_path = os.path.join(temp_dir, "score.midi")
            if os.path.exists(temp_midi_path):
                final_midi_path = os.path.join(cache_dir, f"{output_name}.midi")
                shutil.copy2(temp_midi_path, final_midi_path)
                
                with open(final_midi_path, "rb") as midi_file:
                    midi_data = midi_file.read()
                    midi_filename = f"{output_name}.midi"
            
            return pdf_data, pdf_filename, midi_data, midi_filename, None
    
    except Exception as e:
        return None, None, None, None, f"Error during conversion: {str(e)}"