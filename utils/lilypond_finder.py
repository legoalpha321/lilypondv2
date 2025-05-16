import os
import subprocess
import platform

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