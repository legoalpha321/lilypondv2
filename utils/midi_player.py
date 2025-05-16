import streamlit as st
import base64

def add_midi_player(midi_data):
    """
    Add a MIDI player widget to the Streamlit app.
    """
    if midi_data is None:
        return
    
    # Convert MIDI data to base64
    b64_midi = base64.b64encode(midi_data).decode()
    
    # Use a JavaScript library to play MIDI in the browser
    st.markdown("### MIDI Preview")
    st.info("Player loading... If you don't see the player below, your browser may not support MIDI playback.")
    
    # Add the midi.js library
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