import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import h5py
import os
import glob
import math
import traceback
import locale
from pathlib import Path

# Set up localization
try:
    locale_setting = os.getenv('APP_LOCALE', '')
    if locale_setting:
        locale.setlocale(locale.LC_ALL, locale_setting)
    else:
        locale.setlocale(locale.LC_ALL, '')
    print(f"[INFO] Locale set to: {locale.getlocale()}")
except Exception as e:
    print(f"[WARNING] Failed to set locale: {str(e)}")

# Localization dictionary for UI text
TRANSLATIONS = {
    'en': {
        'app_title': 'H5 Data Visualization Dashboard',
        'select_file': 'Select a file to visualize',
        'no_files': 'No H5 files found. Please add files to the data directory.',
        'file_input_placeholder': 'Enter file name (e.g., test.h5)',
        'load_button': 'Load',
        'back_button': 'BACK',
        'visualization_title': 'Your visualization',
        'scroll_hint': 'Scroll horizontally to view more columns.',
        'jump_to_row': 'Jump to blank info',
        'go_button': 'GO',
        'previous_button': 'Previous Row',
        'next_button': 'Next Row',
        'page': 'Page',
        'of': 'of',
        'error_title': 'Error',
        'back_to_home': 'Back to Home',
        'no_data': 'No data available. Please select a file first.',
        'no_data_table': 'No data available for table',
        'missing_data': 'Missing {0} data',
        'tab_screwdown': 'Screwdown',
        'tab_bending': 'Bending Data',
        'tab_profile': 'Profile Data',
        'tab_all_data': 'All Data',
        'currently_viewing': 'Currently viewing:',
        'no_file_selected': 'No file selected',
        'ref_label': 'REF',
        'actual_label': 'ACTUAL',
        'graph_title': '{0} Graph - Row {1}',
        'all_data_graph_title': 'All Data Graph - Row {0}',
        'actual_vs_ref': '{0} Actual vs Reference (Row {1})',
        'position_label': 'Position [mm]',
        'thickness_label': 'Thickness [μm]',
        'bending_label': 'Bending [N]',
        'coil_selection': 'Select Coil:',
        'auto_scale': 'Auto Scale',
        'reset_zoom': 'Reset Zoom',
        'fit_to_view': 'Fit to View',
        'zoom_in': 'Zoom In',
        'zoom_out': 'Zoom Out',
        'fullscreen_mode': 'Fullscreen Mode',
        'exit_fullscreen': 'Exit Fullscreen',
        'auto_advance': 'Auto-advance to next row',
        'auto_advance_enabled': 'Auto-advance enabled',
        'auto_advance_disabled': 'Auto-advance disabled',
        'current_row': 'Row {0}'
    },
    'de': {
        'app_title': 'H5-Datenvisualisierungs-Dashboard',
        'select_file': 'Wählen Sie eine Datei zur Visualisierung aus',
        'no_files': 'Keine H5-Dateien gefunden. Bitte fügen Sie Dateien zum Datenverzeichnis hinzu.',
        'file_input_placeholder': 'Dateinamen eingeben (z.B. test.h5)',
        'load_button': 'Laden',
        'back_button': 'ZURÜCK',
        'visualization_title': 'Ihre Visualisierung',
        'scroll_hint': 'Horizontal scrollen, um weitere Spalten anzuzeigen.',
        'jump_to_row': 'Springe zu Blechinfo',
        'go_button': 'Los',
        'previous_button': 'Vorherige',
        'next_button': 'Nächste',
        'page': 'Seite',
        'von': 'von',
        'error_title': 'Fehler',
        'back_to_home': 'Zurück zur Startseite',
        'no_data': 'Keine Daten verfügbar. Bitte wählen Sie zuerst eine Datei aus.',
        'no_data_table': 'Keine Daten für Tabelle verfügbar',
        'missing_data': '{0}-Daten fehlen',
        'tab_screwdown': 'Anstellung',
        'tab_bending': 'Biegedaten',
        'tab_profile': 'Profildaten',
        'tab_all_data': 'Alle Daten',
        'currently_viewing': 'Aktuelle Ansicht:',
        'no_file_selected': 'Keine Datei ausgewählt',
        'ref_label': 'SOLL',
        'actual_label': 'IST',
        'graph_title': '{0}-Diagramm - Zeile {1}',
        'all_data_graph_title': 'Alle Daten-Diagramm - Zeile {0}',
        'actual_vs_ref': '{0} Ist vs. Soll (Zeile {1})',
        'position_label': 'Position [mm]',
        'thickness_label': 'Blechdicke [μm]',
        'bending_label': 'Biegung [N]',
        'coil_selection': 'Coil auswählen:',
        'auto_scale': 'Auto-Skalierung',
        'reset_zoom': 'Zoom zurücksetzen',
        'fit_to_view': 'An Ansicht anpassen',
        'zoom_in': 'Vergrößern',
        'zoom_out': 'Verkleinern',
        'fullscreen_mode': 'Vollbildmodus',
        'exit_fullscreen': 'Vollbild verlassen',
        'auto_advance': 'Automatisch zur nächsten Zeile',
        'auto_advance_enabled': 'Auto-Weiterschalten aktiviert',
        'auto_advance_disabled': 'Auto-Weiterschalten deaktiviert',
        'current_row': 'Zeile {0}'
    }
}

# Global language management
LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
if LANGUAGE not in TRANSLATIONS:
    print(f"[WARNING] Language {LANGUAGE} not supported, defaulting to English")
    LANGUAGE = 'en'

def switch_language(new_language):
    """Properly switch the global language"""
    global LANGUAGE
    if new_language in TRANSLATIONS:
        LANGUAGE = new_language
        print(f"[INFO] Language switched to: {LANGUAGE}")
        return True
    return False

def _(key, *args):
    """Get translated text using current global language"""
    global LANGUAGE
    if key not in TRANSLATIONS[LANGUAGE]:
        if key in TRANSLATIONS['en']:
            text = TRANSLATIONS['en'][key]
        else:
            return key
    else:
        text = TRANSLATIONS[LANGUAGE][key]
    
    if args:
        return text.format(*args)
    return text

# Constants
REF_COLOR = "#FFFFD0"
ACTUAL_COLOR = "#C0F0C0"
BORDER_COLOR = "#DDDDDD"

SCREWDOWN_REF_COLOR = "#0000FF"
SCREWDOWN_ACTUAL_COLOR = "#00AAFF"
BENDING_REF_COLOR = "#FF0000"
BENDING_ACTUAL_COLOR = "#FF6666"
PROFILE_REF_COLOR = "#00AA00"
PROFILE_ACTUAL_COLOR = "#66CC66"

# Dynamic coil blank info ranges - calculated based on actual data
COIL_BLANK_INFO_RANGES = {}

class Config:
    def __init__(self):
        self.data_points = 41
        self.ref_points = 21
        self.x_max = 100.0
        self.ref_cycles = 2.0
        self.amplitude = 10.0
        self.offset = 50.0
        self.profile_scale = 0.5
        self.x_noise_scale = 0.5
        self.z_noise_scale = 1.0
        self.secret_key = 'h5_visualization_dashboard'
        self.default_h5_file = os.getenv('DEFAULT_H5_FILE', '')
        self.h5_files_dir = os.getenv('H5_DATA_DIR', './data')
        self.additional_search_paths = [os.getenv("H5_SEARCH_DIR", "./data")]
        self.data_rows = None
        self.rows_per_page = 10
        self.display_points = 3
        self.debug_mode = False

config = Config()

# Global data store
data_store = {}
current_file_name = None
file_history = []
error_message = None
available_coils = ["coil 50", "coil 51", "coil 52"]
selected_coil = "coil 50"
selected_row = 0  # Global selected_row variable

def calculate_coil_ranges(file_path, available_coils):
    """Dynamically calculate blank info ranges for all coils based on actual data"""
    global COIL_BLANK_INFO_RANGES
    
    if not available_coils:
        return
    
    COIL_BLANK_INFO_RANGES = {}
    current_start = 1
    
    print(f"[INFO] Calculating dynamic ranges for coils: {available_coils}")
    
    # Sort coils by numeric value to ensure consistent ordering
    def extract_coil_number(coil_name):
        numbers = ''.join(filter(str.isdigit, coil_name))
        return int(numbers) if numbers else 0
    
    sorted_coils = sorted(available_coils, key=extract_coil_number)
    
    for coil_name in sorted_coils:
        try:
            # Load data for this coil to get actual row count
            coil_data = load_data_from_h5_dynamic(file_path, coil_name)
            
            if coil_data and any(coil_data.values()):
                # Get the actual number of rows for this coil
                num_rows = 0
                for key in ["screwdown", "bending", "profile"]:
                    if coil_data.get(key) and "actual_x" in coil_data[key]:
                        num_rows = max(num_rows, coil_data[key]["actual_x"].shape[0])
                
                if num_rows > 0:
                    end_num = current_start + num_rows - 1
                    COIL_BLANK_INFO_RANGES[coil_name] = {
                        "start": current_start,
                        "end": end_num,
                        "count": num_rows
                    }
                    
                    print(f"[INFO] {coil_name}: {current_start}-{end_num} ({num_rows} rows)")
                    current_start = end_num + 1
                else:
                    print(f"[WARNING] No valid data found for {coil_name}, skipping")
            else:
                print(f"[WARNING] No data found for {coil_name}, skipping")
                
        except Exception as e:
            print(f"[ERROR] Error calculating range for {coil_name}: {e}")
    
    print(f"[INFO] Final coil ranges: {COIL_BLANK_INFO_RANGES}")

def validate_h5_file(file_path):
    """Quick validation to check if H5 file is readable and has expected structure."""
    try:
        with h5py.File(file_path, 'r') as f:
            if len(f.keys()) == 0:
                return False, "Empty H5 file"
            
            file_size = os.path.getsize(file_path)
            if file_size < 1024:
                return False, "File too small"
            
            return True, "Valid"
    
    except Exception as e:
        return False, f"Invalid H5 file: {str(e)}"

def find_h5_files_improved():
    """Improved H5 file discovery with proper deduplication and filtering."""
    h5_files = []
    seen_filenames = set()
    
    search_dirs = [
        os.getenv('H5_DATA_DIR', './data'),
        './data',
        './valid',
        './input',
        '.',
    ]
    
    search_dirs = [d for d in dict.fromkeys(search_dirs) if os.path.exists(d)]
    
    print(f"[INFO] Searching in directories: {search_dirs}")
    
    for search_dir in search_dirs:
        try:
            pattern = os.path.join(search_dir, '*.h5')
            found_files = glob.glob(pattern)
            
            for file_path in found_files:
                filename = os.path.basename(file_path)
                
                if filename in seen_filenames:
                    print(f"[INFO] Skipping duplicate: {filename}")
                    continue
                
                is_valid, message = validate_h5_file(file_path)
                if not is_valid:
                    print(f"[WARNING] Skipping invalid file {filename}: {message}")
                    continue
                
                seen_filenames.add(filename)
                h5_files.append(file_path)
                print(f"[INFO] Found unique file: {filename} at {file_path}")
        
        except Exception as e:
            print(f"[WARNING] Error searching in {search_dir}: {e}")
    
    h5_files.sort(key=lambda x: os.path.basename(x).lower())
    
    print(f"[INFO] Total unique H5 files found: {len(h5_files)}")
    return h5_files

def filter_h5_files_by_pattern(h5_files, max_files=15):
    """Filter H5 files to show only the most relevant ones."""
    if len(h5_files) <= max_files:
        return h5_files
    
    priority_patterns = [
        'test.h5',
        'sample',
        'data',
        'coil',
        'main',
        'primary'
    ]
    
    priority_files = []
    regular_files = []
    
    for file_path in h5_files:
        filename = os.path.basename(file_path).lower()
        
        is_priority = any(pattern in filename for pattern in priority_patterns)
        
        if is_priority:
            priority_files.append(file_path)
        else:
            regular_files.append(file_path)
    
    filtered_files = priority_files[:max_files//2] + regular_files[:max_files//2]
    
    remaining_slots = max_files - len(filtered_files)
    if remaining_slots > 0:
        remaining_files = [f for f in h5_files if f not in filtered_files]
        filtered_files.extend(remaining_files[:remaining_slots])
    
    return filtered_files[:max_files]

def get_available_coils_dynamic(file_path):
    """Dynamically discover available coils in the H5 file."""
    available_coils = []
    
    try:
        with h5py.File(file_path, 'r') as f:
            print(f"[INFO] Searching for coils in {file_path}")
            
            def find_coils(name, obj):
                if isinstance(obj, h5py.Group):
                    path_parts = name.split('/')
                    for part in path_parts:
                        part_lower = part.lower()
                        if ('coil' in part_lower and 
                            any(char.isdigit() for char in part) and
                            len(part) < 20):
                            
                            try:
                                if ('x' in obj and 'z' in obj) or any('x' in child or 'z' in child for child in obj.keys()):
                                    if part not in available_coils:
                                        available_coils.append(part)
                                        print(f"[INFO] Found valid coil: {part}")
                            except:
                                continue
            
            f.visititems(find_coils)
            
            if not available_coils:
                print("[INFO] No coils found with standard pattern, trying alternative search...")
                
                def find_coils_alternative(name, obj):
                    if isinstance(obj, h5py.Group):
                        path_parts = name.split('/')
                        for part in path_parts:
                            if (part.isdigit() and 
                                int(part) >= 50 and int(part) <= 60 and
                                ('x' in obj and 'z' in obj)):
                                coil_name = f"coil {part}"
                                if coil_name not in available_coils:
                                    available_coils.append(coil_name)
                                    print(f"[INFO] Found numeric coil: {coil_name}")
                
                f.visititems(find_coils_alternative)
        
        def extract_number(coil_name):
            numbers = ''.join(filter(str.isdigit, coil_name))
            return int(numbers) if numbers else 0
        
        available_coils = sorted(list(set(available_coils)), key=extract_number)
        
        print(f"[INFO] Final available coils: {available_coils}")
        
    except Exception as e:
        print(f"[ERROR] Error getting available coils: {e}")
        available_coils = []
    
    return available_coils

def find_file_path(file_name):
    """Dynamically find the full path of an H5 file"""
    all_h5_files = find_h5_files_improved()
    
    for file_path in all_h5_files:
        if os.path.basename(file_path) == file_name:
            return file_path
    
    return None

def generate_reference_display(ref_x, ref_z):
    if ref_x is None or ref_z is None:
        return np.array([]), np.array([]), np.array([])

    display_x, display_z, is_midpoint = [], [], []

    for i in range(len(ref_x) - 1):
        display_x.append(ref_x[i])
        display_z.append(ref_z[i])
        is_midpoint.append(False)

        mx = (ref_x[i] + ref_x[i+1]) / 2
        mz = (ref_z[i] + ref_z[i+1]) / 2
        display_x.append(mx)
        display_z.append(mz)
        is_midpoint.append(True)

    display_x.append(ref_x[-1])
    display_z.append(ref_z[-1])
    is_midpoint.append(False)

    return np.array(display_x), np.array(display_z), np.array(is_midpoint)

def get_coil_data_paths(file_path, coil_name):
    """Dynamically find data paths for a specific coil in the H5 file."""
    data_paths = {}
    
    try:
        with h5py.File(file_path, 'r') as f:
            def find_coil_data(name, obj):
                if isinstance(obj, h5py.Group):
                    if coil_name in name:
                        for data_type in ['bending', 'screwdown', 'profile']:
                            if data_type in name.lower():
                                if 'x' in obj and 'z' in obj:
                                    data_paths[data_type] = name
                                    print(f"[INFO] Found {data_type} data at: {name}")
            
            f.visititems(find_coil_data)
            
    except Exception as e:
        print(f"[ERROR] Error finding coil data paths: {e}")
        traceback.print_exc()
    
    return data_paths

def generate_coil_blank_info(coil_name, num_rows):
    """Generate continuous blank info numbers for a specific coil"""
    if coil_name in COIL_BLANK_INFO_RANGES:
        start_num = COIL_BLANK_INFO_RANGES[coil_name]["start"]
        
        # Generate exactly num_rows blank info numbers starting from start_num
        blank_info = np.arange(start_num, start_num + num_rows)
        print(f"[INFO] Generated blank info for {coil_name}: {start_num} to {start_num + num_rows - 1} ({num_rows} rows)")
        
        return blank_info
    else:
        # Handle missing coil ranges gracefully - ensure uniqueness across sessions
        if COIL_BLANK_INFO_RANGES:
            max_end = max([info["end"] for info in COIL_BLANK_INFO_RANGES.values()])
            start_num = max_end + 1
        else:
            start_num = 1
        
        end_num = start_num + num_rows - 1
        COIL_BLANK_INFO_RANGES[coil_name] = {
            "start": start_num,
            "end": end_num,
            "count": num_rows
        }
        
        blank_info = np.arange(start_num, start_num + num_rows)
        print(f"[INFO] Generated dynamic blank info for {coil_name}: {start_num} to {end_num} ({num_rows} rows)")
        
        return blank_info

def load_data_from_h5_dynamic(file_path, selected_coil=''):
    """Dynamically load data from H5 file without hardcoded paths."""
    result = {
        "screwdown": None,
        "bending": None,
        "profile": None,
        "blank_info": None
    }

    try:
        with h5py.File(file_path, 'r') as f:
            print(f"[INFO] Loading data for coil: {selected_coil}")
            
            if selected_coil:
                coil_data_paths = get_coil_data_paths(file_path, selected_coil)
            else:
                coil_data_paths = {}
                
                def find_any_data(name, obj):
                    if isinstance(obj, h5py.Group):
                        for data_type in ['bending', 'screwdown', 'profile']:
                            if data_type in name.lower():
                                if 'x' in obj and 'z' in obj:
                                    coil_data_paths[data_type] = name
                                    print(f"[INFO] Found {data_type} data at: {name}")
                
                f.visititems(find_any_data)
            
            if not coil_data_paths:
                print(f"[WARNING] No data paths found for {selected_coil}")
                return result
            
            # Load real data from H5 file
            for data_type, data_path in coil_data_paths.items():
                try:
                    data_group = f[data_path]
                    
                    actual_x = data_group['x'][:]
                    actual_z = data_group['z'][:]
                    
                    if len(actual_x.shape) == 1:
                        actual_x = actual_x.reshape(1, -1)
                    if len(actual_z.shape) == 1:
                        actual_z = actual_z.reshape(1, -1)
                    
                    ref_x = None
                    ref_z = None
                    
                    # Try to find reference data in attributes
                    ref_attr_names = [
                        f"{data_type.capitalize()} ref x",
                        f"{data_type} ref x",
                        "ref_x",
                        "reference_x"
                    ]
                    
                    for attr_name in ref_attr_names:
                        if attr_name in data_group.attrs:
                            ref_x = np.array(data_group.attrs[attr_name])
                            break
                    
                    ref_attr_names_z = [
                        f"{data_type.capitalize()} ref z",
                        f"{data_type} ref z",
                        "ref_z",
                        "reference_z"
                    ]
                    
                    for attr_name in ref_attr_names_z:
                        if attr_name in data_group.attrs:
                            ref_z = np.array(data_group.attrs[attr_name])
                            break
                    
                    # Try to find reference data in datasets
                    if ref_x is None or ref_z is None:
                        if 'ref_x' in data_group:
                            ref_x = data_group['ref_x'][:]
                        if 'ref_z' in data_group:
                            ref_z = data_group['ref_z'][:]
                    
                    # If still no reference data, create fallback from actual data
                    if ref_x is None and actual_x.size > 0:
                        ref_x = np.mean(actual_x, axis=0) if actual_x.ndim > 1 else actual_x
                        print(f"[INFO] Generated fallback ref_x from actual_x for {data_type}")

                    if ref_z is None and actual_z.size > 0:
                        ref_z = np.mean(actual_z, axis=0) if actual_z.ndim > 1 else actual_z
                        print(f"[INFO] Generated fallback ref_z from actual_z for {data_type}")

                    # Validate that ref_x and ref_z have same length
                    if ref_x is None or ref_z is None or len(ref_x) != len(ref_z):
                        print(f"[ERROR] Inconsistent reference data in {data_type}: ref_x={len(ref_x) if ref_x is not None else 'None'}, ref_z={len(ref_z) if ref_z is not None else 'None'}")
                        continue

                                        
                    disp_x, disp_z, is_mid = generate_reference_display(ref_x, ref_z)
                    
                    result[data_type] = {
                        "actual_x": actual_x,
                        "actual_z": actual_z,
                        "ref_x": disp_x,
                        "ref_z": disp_z,
                        "is_midpoint": is_mid
                    }
                    
                    print(f"[INFO] Successfully loaded {data_type} data: {actual_x.shape[0]} rows, {actual_x.shape[1]} points")
                    
                except Exception as e:
                    print(f"[ERROR] Error loading {data_type} data: {e}")
                    continue
            
            # Generate continuous blank info for the selected coil
            num_rows = 0
            for key in ["screwdown", "bending", "profile"]:
                if result[key] and "actual_x" in result[key]:
                    num_rows = max(num_rows, result[key]["actual_x"].shape[0])
            
            # Ensure blank_info indexing is 1-to-1 with actual_x rows
            if num_rows > 0:
                result["blank_info"] = generate_coil_blank_info(selected_coil, num_rows)
                print(f"[DEBUG] Blank info assigned: length={len(result['blank_info'])}, range={result['blank_info'][0] if len(result['blank_info']) > 0 else 'N/A'}-{result['blank_info'][-1] if len(result['blank_info']) > 0 else 'N/A'}")
            else:
                result["blank_info"] = np.array([])

    except Exception as e:
        print(f"[ERROR] Error loading data from {file_path}: {e}")
        traceback.print_exc()

    return result

def find_h5_files():
    """Find all available H5 files with proper deduplication and filtering."""
    all_h5_files = find_h5_files_improved()
    filtered_files = filter_h5_files_by_pattern(all_h5_files, max_files=15)
    
    unique_filenames = []
    seen_names = set()
    
    for file_path in filtered_files:
        filename = os.path.basename(file_path)
        if filename not in seen_names:
            unique_filenames.append(filename)
            seen_names.add(filename)
    
    print(f"[INFO] Returning {len(unique_filenames)} unique files for display")
    return unique_filenames

def handle_h5_file_loading(file_path):
    global data_store, current_file_name, config, selected_coil, available_coils, selected_row

    file_name = os.path.basename(file_path)
    current_file_name = file_name

    try:
        print(f"[INFO] Attempting to load HDF5 file: {file_path}")
        
        file_coils = get_available_coils_dynamic(file_path)
        
        if file_coils:
            available_coils = file_coils
            print(f"[INFO] Available coils in file: {available_coils}")
            
            # Calculate dynamic ranges for all coils
            calculate_coil_ranges(file_path, available_coils)
            
            if selected_coil not in available_coils:
                selected_coil = available_coils[0]
                print(f"[INFO] Selected coil set to: {selected_coil}")
        else:
            print("[WARNING] No coils found in file, attempting to load data directly")
            available_coils = []
            selected_coil = ""

        # Reset selected_row when coil changes
        selected_row = 0

        if available_coils:
            dynamic_data = load_data_from_h5_dynamic(file_path, selected_coil)
        else:
            dynamic_data = load_data_from_h5_dynamic(file_path, "")

        if dynamic_data and any(dynamic_data.values()):
            print(f"[INFO] Successfully loaded data")

            # Get the actual number of rows from the loaded data
            actual_num_rows = 0
            for key in ["screwdown", "bending", "profile"]:
                if dynamic_data.get(key) and "actual_x" in dynamic_data[key]:
                    actual_num_rows = max(actual_num_rows, dynamic_data[key]["actual_x"].shape[0])

            # Ensure blank_info matches the actual data rows
            if dynamic_data.get("blank_info") is not None:
                blank_info_data = dynamic_data["blank_info"]
                if len(blank_info_data) != actual_num_rows:
                    print(f"[WARNING] Blank info length ({len(blank_info_data)}) doesn't match data rows ({actual_num_rows}), regenerating...")
                    blank_info_data = generate_coil_blank_info(selected_coil, actual_num_rows)
            else:
                blank_info_data = generate_coil_blank_info(selected_coil, actual_num_rows)

            data_store = {
                "screwdown": dynamic_data.get("screwdown", {}),
                "bending": dynamic_data.get("bending", {}),
                "profile": dynamic_data.get("profile", {}),
                "blank_info": {
                    "label": "Blank Info",
                    "data": blank_info_data
                },
                "boolean_info": {
                    "label": "Boolean Info",
                    "data": pd.DataFrame({'value': np.zeros(len(blank_info_data))}),
                }
            }

            config.data_rows = actual_num_rows
            return True
        else:
            print("[ERROR] Dynamic loading failed, no data found.")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during H5 loading: {e}")
        traceback.print_exc()
        return False

# Create the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
                ],
                suppress_callback_exceptions=True)
server = app.server
server.secret_key = config.secret_key

app.enable_dev_tools(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# Create data directory if it doesn't exist
os.makedirs(config.h5_files_dir, exist_ok=True)

# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Div(id='data-store', style={'display': 'none'}),
    html.Div(id='page-store', children='1', style={'display': 'none'}),
    html.Div(id='selected-row', children=None, style={'display': 'none'}),
    html.Div(id='max-row', children='0', style={'display': 'none'}),
    html.Div(id='selected-coil', style={'display': 'none'}),
    html.Div(id='zoom-state', children='default', style={'display': 'none'}),
    html.Div(id='fullscreen-state', children='false', style={'display': 'none'}),
    html.Div(id='current-language', children=LANGUAGE, style={'display': 'none'}),
    html.Div(id='auto-advance-state', children='false', style={'display': 'none'}),
    dcc.Interval(
        id='auto-advance-interval',
        interval=2000,  # 2 seconds
        n_intervals=0,
        disabled=True
    ),
    # Dummy hidden tabs to prevent layout validation error
    dcc.Tabs(id='tabs', value='screwdown', children=[], style={'display': 'none'}),
])

# Define the file selection layout
def create_file_selection_layout():
    h5_files = find_h5_files()
    
    return html.Div([
        html.Div([
            html.H1(_('app_title'), className="text-center mb-4"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H4(_('select_file'), className="mb-0")
                ], className="bg-success text-white"),
                dbc.CardBody([
                    html.Div([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.I(className="bi bi-file-earmark-binary me-3", style={"fontSize": "1.5rem", "color": "#0d6efd"}),
                                    html.Span(file, className="fs-5"),
                                    html.I(className="bi bi-chevron-right ms-auto", style={"color": "#6c757d"})
                                ], className="d-flex align-items-center")
                            ], href=f"/load/{file}", action=True) 
                            for file in h5_files
                        ]) if h5_files else html.P(_('no_files'), className="text-center")
                    ]),
                    
                    html.Hr(),
                    
                    dbc.Form([
                        dbc.InputGroup([
                            dbc.Input(id="file-name-input", placeholder=_('file_input_placeholder'), type="text"),
                            dbc.Button(_('load_button'), id="load-file-button", color="primary")
                        ])
                    ], className="mt-3")
                ])
            ], className="shadow")
        ], className="container py-5", style={"maxWidth": "800px"})
    ], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh"})

# Define the visualization layout
def create_visualization_layout():
    global LANGUAGE
    
    return html.Div([
        # Language switcher
        html.Div([
            html.Span("Language: ", className="me-2"),
            html.Button("English", 
                       id="btn-lang-en", 
                       className="btn btn-sm me-1 " + ("btn-primary" if LANGUAGE == 'en' else "btn-outline-primary")),
            html.Button("Deutsch", 
                       id="btn-lang-de", 
                       className="btn btn-sm " + ("btn-primary" if LANGUAGE == 'de' else "btn-outline-primary"))
        ], className="d-flex justify-content-end m-2"),
        
        html.H1(_('visualization_title'), className="mb-4", 
               style={"backgroundColor": "#1e8449", "color": "white", "padding": "10px", "textAlign": "center"}),
        html.Button(_('back_button'), id="back-button", className="btn btn-outline-secondary", style={"marginBottom": "20px", "marginLeft": "10px"}),
        
        html.Div(id='file-info', className="mb-3 alert alert-info py-2", style={"margin": "0 10px"}),
        
        html.Div(id='coil-selection-container', className="mb-3", style={"margin": "0 10px"}),
        
        dcc.Tabs(id='tabs', value='screwdown', children=[
            dcc.Tab(label=_('tab_screwdown'), value='screwdown'),
            dcc.Tab(label=_('tab_bending'), value='bending'),
            dcc.Tab(label=_('tab_profile'), value='profile'),
            dcc.Tab(label=_('tab_all_data'), value='all_data'),
        ]),
        
        html.Div([
            html.Div(_('scroll_hint'), 
                    className="alert alert-info py-2", style={"margin": "10px 0"}),
            
            html.Div(id='table-container', style={"overflowX": "auto", "width": "100%"}),
            
            # Row navigation section
            html.Div([
                html.Div([
                    # Current row display
                    html.Div(id='current-row-display', className="badge bg-primary fs-5 px-3 py-2 me-3"),
                    
                    # Row navigation buttons
                    html.Button(
                        _('previous_button'),
                        id="jump-previous-button",
                        n_clicks=0,
                        className="btn btn-outline-primary",
                        style={
                            "borderRadius": "8px",
                            "padding": "10px 20px",
                            "marginRight": "15px",
                            "fontWeight": "bold",
                            "minWidth": "120px"
                        }
                    ),
                    html.Div([
                        html.Label(_('jump_to_row'), className="me-2", style={"fontWeight": "bold", "fontSize": "16px"}),
                        dcc.Input(
                            id="jump-to-row-input",
                            type="number",
                            min=1,
                            className="form-control",
                            style={
                                "width": "100px", 
                                "display": "inline-block", 
                                "marginRight": "10px",
                                "textAlign": "center",
                                "borderRadius": "4px",
                                "border": "2px solid #ddd"
                            }
                        ),
                        html.Button(
                            _('go_button'),
                            id="jump-to-row-button",
                            n_clicks=0,
                            className="btn btn-primary",
                            style={
                                "borderRadius": "8px",
                                "padding": "8px 20px",
                                "fontWeight": "bold",
                                "minWidth": "60px"
                            }
                        )
                    ], className="d-flex align-items-center", style={"margin": "0 15px"}),
                    html.Button(
                        _('next_button'),
                        id="jump-next-button",
                        n_clicks=0,
                        className="btn btn-outline-primary",
                        style={
                            "borderRadius": "8px",
                            "padding": "10px 20px",
                            "marginLeft": "15px",
                            "fontWeight": "bold",
                            "minWidth": "120px"
                        }
                    )
                ], className="d-flex align-items-center justify-content-center mt-3 mb-4", 
                   style={
                       "padding": "20px",
                       "backgroundColor": "#f8f9fa",
                       "borderRadius": "10px",
                       "border": "1px solid #dee2e6",
                       "margin": "20px 10px"
                   }),
            ]),
            
            # FIXED: Ensure pagination controls always exist
            html.Div([
                html.Button(_('previous_button'), id="prev-button", 
                          className="btn btn-outline-primary me-2",
                          disabled=True),
                html.Span(f"{_('page')} 1", id="page-display", className="mx-2"),
                html.Button(_('next_button'), id="next-button", 
                          className="btn btn-outline-primary ms-2")
            ], id='pagination-controls', className="d-flex justify-content-center mb-4"),
        ], className="mb-4"),

        # Enhanced zoom controls with better auto-advance
        html.Div([
            html.Div([
                html.Div([
                    dbc.Checklist(
                        options=[{"label": _('auto_advance'), "value": "auto_advance"}],
                        value=[],
                        id="auto-advance-checkbox",
                        className="me-3",
                        inline=True,
                        style={"fontSize": "16px", "fontWeight": "bold"}
                    ),
                    html.Div(
                        id="auto-advance-status",
                        className="me-3",
                        style={"fontSize": "14px", "color": "#666", "fontWeight": "bold"}
                    )
                ], className="d-flex align-items-center me-3"),
                html.Button(
                    html.I(className="bi bi-fullscreen", style={"fontSize": "1.2rem"}),
                    id="fullscreen-button",
                    className="btn btn-outline-primary me-2",
                    title=_('fullscreen_mode')
                ),
                html.Button(
                    html.I(className="bi bi-arrows-fullscreen", style={"fontSize": "1.2rem"}),
                    id="auto-scale-button",
                    className="btn btn-outline-primary me-2",
                    title=_('auto_scale')
                ),
                html.Button(
                    html.I(className="bi bi-zoom-in", style={"fontSize": "1.2rem"}),
                    id="zoom-in-button",
                    className="btn btn-outline-primary me-2",
                    title=_('zoom_in')
                ),
                html.Button(
                    html.I(className="bi bi-zoom-out", style={"fontSize": "1.2rem"}),
                    id="zoom-out-button",
                    className="btn btn-outline-primary me-2",
                    title=_('zoom_out')
                ),
                html.Button(
                    html.I(className="bi bi-arrow-counterclockwise", style={"fontSize": "1.2rem"}),
                    id="reset-zoom-button",
                    className="btn btn-outline-primary",
                    title=_('reset_zoom')
                ),
            ], className="d-flex justify-content-end align-items-center mb-2", style={"margin": "0 10px"}),
        ], id='zoom-controls', style={"display": "none"}),

        html.Div(id='graph-container', style={"display": "none"})
    ], style={"width": "100%", "padding": "0", "margin": "0"})

def create_error_layout(message):
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="bi bi-exclamation-triangle-fill", 
                      style={"color": "#f39c12", "fontSize": "64px", "marginBottom": "20px"}),
                html.H1(_('error_title'), className="mb-4"),
                html.P(message, className="lead mb-4"),
                html.A(_('back_to_home'), href="/", className="btn btn-primary")
            ], className="text-center py-5")
        ], className="container")
    ])

# Helper function to create the combined graph
def create_combined_graph(selected_row, zoom_state='default', is_fullscreen=False):
    """Create a single Plotly figure for all data types with dual y-axis"""
    try:
        fig = go.Figure()
        selected_row = int(selected_row) if isinstance(selected_row, (int, str)) else 0
        
        # Add Screwdown data (blue lines)
        sd_data = data_store.get('screwdown', {})
        if all(k in sd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            if len(sd_data['ref_x']) > 0 and len(sd_data['ref_z']) > 0:
                # Separate regular points and midpoints
                is_midpoint = sd_data.get('is_midpoint', [False] * len(sd_data['ref_x']))
                
                # Create arrays for regular points only (for visible line)
                regular_x = []
                regular_z = []
                
                # Create arrays for all points (for hover)
                all_x = sd_data['ref_x']
                all_z = sd_data['ref_z']
                
                for i, is_mid in enumerate(is_midpoint):
                    if not is_mid:  # Only regular points for visible line
                        regular_x.append(sd_data['ref_x'][i])
                        regular_z.append(sd_data['ref_z'][i])
                
                # Add visible line with only regular points
                fig.add_trace(go.Scatter(
                    x=regular_x,
                    y=regular_z,
                    mode='lines+markers',
                    name='Sollprofil',
                    line=dict(color=SCREWDOWN_REF_COLOR, width=2),
                    marker=dict(size=6)
                ))
                
                # Add invisible hover trace for all points (including midpoints)
                fig.add_trace(go.Scatter(
                    x=all_x,
                    y=all_z,
                    mode='markers',
                    name='Sollprofil (Hover)',
                    marker=dict(size=8, opacity=0),  # Invisible markers
                    hovertemplate='<b>Sollprofil</b><br>X: %{x:.1f}<br>Z: %{y:.1f}<extra></extra>',
                    showlegend=False
                ))
            
            if ('actual_x' in sd_data and 'actual_z' in sd_data and 
                sd_data['actual_x'].shape[0] > 0 and 
                selected_row >= 0 and selected_row < sd_data['actual_x'].shape[0]):
                
                row_data_x = sd_data['actual_x'][selected_row]
                row_data_z = sd_data['actual_z'][selected_row]
                
                fig.add_trace(go.Scatter(
                    x=row_data_x,
                    y=row_data_z,
                    mode='lines',
                    name='Istprofil',
                    line=dict(color=SCREWDOWN_ACTUAL_COLOR, width=2)
                ))
        
        # Add Profile data (green lines)
        pd_data = data_store.get('profile', {})
        if all(k in pd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            if len(pd_data['ref_x']) > 0 and len(pd_data['ref_z']) > 0:
                # Separate regular points and midpoints
                is_midpoint = pd_data.get('is_midpoint', [False] * len(pd_data['ref_x']))
                
                # Create arrays for regular points only (for visible line)
                regular_x = []
                regular_z = []
                
                # Create arrays for all points (for hover)
                all_x = pd_data['ref_x']
                all_z = pd_data['ref_z']
                
                for i, is_mid in enumerate(is_midpoint):
                    if not is_mid:  # Only regular points for visible line
                        regular_x.append(pd_data['ref_x'][i])
                        regular_z.append(pd_data['ref_z'][i])
                
                # Add visible line with only regular points
                fig.add_trace(go.Scatter(
                    x=regular_x,
                    y=regular_z,
                    mode='lines+markers',
                    name='Sollanstellung',
                    line=dict(color=PROFILE_REF_COLOR, width=2),
                    marker=dict(size=6)
                ))
                
                # Add invisible hover trace for all points (including midpoints)
                fig.add_trace(go.Scatter(
                    x=all_x,
                    y=all_z,
                    mode='markers',
                    name='Sollanstellung (Hover)',
                    marker=dict(size=8, opacity=0),  # Invisible markers
                    hovertemplate='<b>Sollanstellung</b><br>X: %{x:.1f}<br>Z: %{y:.1f}<extra></extra>',
                    showlegend=False
                ))
            
            if ('actual_x' in pd_data and 'actual_z' in pd_data and 
                pd_data['actual_x'].shape[0] > 0 and 
                selected_row >= 0 and selected_row < pd_data['actual_x'].shape[0]):
                
                row_data_x = pd_data['actual_x'][selected_row]
                row_data_z = pd_data['actual_z'][selected_row]
                
                fig.add_trace(go.Scatter(
                    x=row_data_x,
                    y=row_data_z,
                    mode='lines',
                    name='Istanstellung',
                    line=dict(color=PROFILE_ACTUAL_COLOR, width=2)
                ))
        
        # Add Bending data (red lines) - use secondary y-axis
        bd_data = data_store.get('bending', {})
        if all(k in bd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            if len(bd_data['ref_x']) > 0 and len(bd_data['ref_z']) > 0:
                # Separate regular points and midpoints
                is_midpoint = bd_data.get('is_midpoint', [False] * len(bd_data['ref_x']))
                
                # Create arrays for regular points only (for visible line)
                regular_x = []
                regular_z = []
                
                # Create arrays for all points (for hover)
                all_x = bd_data['ref_x']
                all_z = bd_data['ref_z']
                
                for i, is_mid in enumerate(is_midpoint):
                    if not is_mid:  # Only regular points for visible line
                        regular_x.append(bd_data['ref_x'][i])
                        regular_z.append(bd_data['ref_z'][i])
                
                # Add visible line with only regular points
                fig.add_trace(go.Scatter(
                    x=regular_x,
                    y=regular_z,
                    mode='lines+markers',
                    name='Sollbiegung',
                    line=dict(color=BENDING_REF_COLOR, width=2),
                    marker=dict(size=6),
                    yaxis="y2"
                ))
                
                # Add invisible hover trace for all points (including midpoints)
                fig.add_trace(go.Scatter(
                    x=all_x,
                    y=all_z,
                    mode='markers',
                    name='Sollbiegung (Hover)',
                    marker=dict(size=8, opacity=0),  # Invisible markers
                    hovertemplate='<b>Sollbiegung</b><br>X: %{x:.1f}<br>Z: %{y:.1f}<extra></extra>',
                    showlegend=False,
                    yaxis="y2"
                ))
            
            if ('actual_x' in bd_data and 'actual_z' in bd_data and 
                bd_data['actual_x'].shape[0] > 0 and 
                selected_row >= 0 and selected_row < bd_data['actual_x'].shape[0]):
                
                row_data_x = bd_data['actual_x'][selected_row]
                row_data_z = bd_data['actual_z'][selected_row]
                
                fig.add_trace(go.Scatter(
                    x=row_data_x,
                    y=row_data_z,
                    mode='lines',
                    name='Istbiegung',
                    line=dict(color=BENDING_ACTUAL_COLOR, width=2),
                    yaxis="y2"
                ))
        
        # Set axis ranges based on zoom state
        xaxis_config = dict(
            title=_('position_label'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
        
        yaxis_config = dict(
            title=_('thickness_label'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
        
        yaxis2_config = dict(
            title=_('bending_label'),
            overlaying="y",
            side="right"
        )
        
        # Apply zoom state
        if zoom_state == 'auto':
            xaxis_config['autorange'] = True
            yaxis_config['autorange'] = True
            yaxis2_config['autorange'] = True
        elif zoom_state == 'default':
            xaxis_config['range'] = [0, 1500]
            yaxis_config['range'] = [-1000, 2000]
            yaxis2_config['range'] = [-600, 600]
        elif zoom_state == 'zoom_in':
            xaxis_config['range'] = [200, 1300]
            yaxis_config['range'] = [-750, 1750]
            yaxis2_config['range'] = [-450, 450]
        elif zoom_state == 'zoom_out':
            xaxis_config['range'] = [-200, 1700]
            yaxis_config['range'] = [-1250, 2250]
            yaxis2_config['range'] = [-750, 750]
        
        # Proper fullscreen height
        height = 700 if is_fullscreen else 400
        
        fig.update_layout(
            xaxis=xaxis_config,
            yaxis=yaxis_config,
            yaxis2=yaxis2_config,
            legend=dict(
                orientation="h", 
                y=1.1,
                x=0.5,
                xanchor="center",
                font=dict(size=12 if is_fullscreen else 10),
                bgcolor="rgba(255,255,255,0.8)"
            ),
            margin=dict(l=50, r=50, t=50, b=50),
            height=height,
            hovermode="closest",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12 if is_fullscreen else 10)
        )
        
        return fig
    except Exception as e:
        print(f"[ERROR] Error creating combined graph: {str(e)}")
        print(traceback.format_exc())
        
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"Error creating graph: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        error_fig.update_layout(
            title="Graph Error",
            height=400
        )
        return error_fig

def create_graph_section(tab, selected_row, zoom_state='default', is_fullscreen=False):
    """Create a single Plotly figure for all data types with dual y-axis"""
    try:
        print(f"[DEBUG] Creating graph for tab={tab}, row={selected_row}, zoom_state={zoom_state}, fullscreen={is_fullscreen}")
        if not data_store:
            return html.Div("⚠️ No data for graph", className="alert alert-warning")
        
        # Ensure selected_row is an integer
        try:
            selected_row = int(selected_row)
        except (ValueError, TypeError):
            print(f"[ERROR] Invalid selected_row in create_graph_section: {selected_row}")
            selected_row = 0
        
        # Get the actual blank info number for display
        blank_info_data = data_store.get('blank_info', {}).get('data', [])
        if isinstance(blank_info_data, np.ndarray) and len(blank_info_data) > selected_row >= 0:
            actual_blank_info = blank_info_data[selected_row]
        else:
            actual_blank_info = selected_row + 1
        
        print(f"[DEBUG] Using row {selected_row} (blank info {actual_blank_info}) for graph")
        
        # For all_data tab, show a combined graph with all three data types
        if tab == 'all_data':
            if not all(k in data_store for k in ['screwdown', 'bending', 'profile']):
                return html.Div("⚠️ Missing data for combined graph", className="alert alert-warning")
            
            graph_panel = html.Div([
                html.Div([
                    html.H5(_('all_data_graph_title', actual_blank_info), className="m-0")
                ], className="d-flex justify-content-between align-items-center px-3 py-2", 
                   style={"backgroundColor": "#0275d8", "color": "white", "borderTopLeftRadius": "4px", "borderTopRightRadius": "4px"}),
                
                dcc.Graph(
                    id='combined-graph',
                    figure=create_combined_graph(selected_row, zoom_state, is_fullscreen),
                    config={
                        'displayModeBar': True,
                        'modeBarButtonsToAdd': ['autoScale2d', 'resetScale2d', 'zoomIn2d', 'zoomOut2d'],
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                        'displaylogo': False
                    },
                    style={"height": "700px" if is_fullscreen else "400px", "padding": "10px", "backgroundColor": "white"}
                )
            ], style={
                "border": "1px solid #ccc",
                "borderRadius": "4px",
                "overflow": "hidden",
                "marginTop": "20px",
                "marginBottom": "20px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "maxWidth": "100%",
                "width": "100%"
            })
            
            return graph_panel
            
        # For individual tabs, show a single graph
        if tab not in data_store:
            return html.Div(f"⚠️ No data for {tab} graph", className="alert alert-warning")

        data = data_store[tab]

        if not all(k in data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            return html.Div(f"⚠️ Missing data keys for {tab} graph", className="alert alert-warning")

        if (len(data['ref_x'])== 0 or len(data['ref_z']) == 0 or 
            data['actual_x'].size == 0 or data['actual_z'].size == 0):
            return html.Div(f"⚠️ Empty data arrays for {tab} graph", className="alert alert-warning")

        fig = go.Figure()

        # Set colors and names based on tab
        ref_color = SCREWDOWN_REF_COLOR
        actual_color = SCREWDOWN_ACTUAL_COLOR
        ref_name = "Sollprofil"
        actual_name = "Istprofil"
        tab_title = "Screwdown"
        
        if tab == 'bending':
            ref_color = BENDING_REF_COLOR
            actual_color = BENDING_ACTUAL_COLOR
            ref_name = "Sollbiegung"
            actual_name = "Istbiegung"
            tab_title = "Bending"
        elif tab == 'profile':
            ref_color = PROFILE_REF_COLOR
            actual_color = PROFILE_ACTUAL_COLOR
            ref_name = "Sollanstellung"
            actual_name = "Istanstellung"
            tab_title = "Profile"

        # Add reference data
        if 'is_midpoint' in data:
            is_midpoint = data['is_midpoint']
            
            #Create arrays for regular points only (for visible line)
            regular_x = []
            regular_z = []
            
            # Create arrays for all points (for hover)
            all_x = data['ref_x']
            all_z = data['ref_z']
            
            for i, is_mid in enumerate(is_midpoint):
                if not is_mid:  # Only regular points for visible line
                    regular_x.append(data['ref_x'][i])
                    regular_z.append(data['ref_z'][i])
            
            # Add visible line with only regular points
            fig.add_trace(go.Scatter(
                x=regular_x,
                y=regular_z,
                mode='lines+markers',
                name=ref_name,
                line=dict(color=ref_color, width=2),
                marker=dict(size=6)
            ))
            
            # Add invisible hover trace for all points (including midpoints)
            fig.add_trace(go.Scatter(
                x=all_x,
                y=all_z,
                mode='markers',
                name=f'{ref_name} (Hover)',
                marker=dict(size=8, opacity=0),  # Invisible markers
                hovertemplate=f'<b>{ref_name}</b><br>X: %{{x:.1f}}<br>Z: %{{y:.1f}}<extra></extra>',
                showlegend=False
            ))
        else:
            # Fallback for data without midpoint information
            fig.add_trace(go.Scatter(
                x=data['ref_x'],
                y=data['ref_z'],
                mode='lines+markers',
                name=ref_name,
                line=dict(color=ref_color, width=2)
            ))

        # Add actual data for selected row
        if selected_row >= 0 and selected_row < data['actual_x'].shape[0]:
            fig.add_trace(go.Scatter(
                x=data['actual_x'][selected_row],
                y=data['actual_z'][selected_row],
                mode='lines+markers',
                name=actual_name,
                line=dict(color=actual_color, width=2)
            ))
        else:
            fig.add_trace(go.Scatter(
                x=data['actual_x'][0],
                y=data['actual_z'][0],
                mode='lines+markers',
                name=actual_name,
                line=dict(color=actual_color, width=2)
            ))

        # Set appropriate y-axis title based on tab
        y_title = "Z Position"
        if tab == 'bending':
            y_title = _('bending_label')
        elif tab == 'profile':
            y_title = "Anstellung [mm]"
        elif tab == 'screwdown':
            y_title = "Z Position"

        # Set axis ranges based on zoom state
        xaxis_config = dict(
            title=_('position_label'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
        
        yaxis_config = dict(
            title=y_title,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
        
        # Apply zoom state
        if zoom_state == 'auto':
            xaxis_config['autorange'] = True
            yaxis_config['autorange'] = True
        elif zoom_state == 'default':
            pass
        elif zoom_state == 'zoom_in':
            x_values = []
            y_values = []
            
            for trace in fig.data:
                x_values.extend(trace.x)
                y_values.extend(trace.y)
            
            if x_values and y_values:
                x_min, x_max = min(x_values), max(x_values)
                y_min, y_max = min(y_values), max(y_values)
                
                x_range = x_max - x_min
                y_range = y_max - y_min
                
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                
                xaxis_config['range'] = [x_center - x_range * 0.375, x_center + x_range * 0.375]
                yaxis_config['range'] = [y_center - y_range * 0.375, y_center + y_range * 0.375]
        elif zoom_state == 'zoom_out':
            x_values = []
            y_values = []
            
            for trace in fig.data:
                x_values.extend(trace.x)
                y_values.extend(trace.y)
            
            if x_values and y_values:
                x_min, x_max = min(x_values), max(x_values)
                y_min, y_max = min(y_values), max(y_values)
                
                x_range = x_max - x_min
                y_range = y_max - y_min
                
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                
                xaxis_config['range'] = [x_center - x_range * 0.625, x_center + x_range * 0.625]
                yaxis_config['range'] = [y_center - y_range * 0.625, y_center + y_range * 0.625]

        # Proper fullscreen height
        height = 700 if is_fullscreen else 400

        fig.update_layout(
            xaxis=xaxis_config,
            yaxis=yaxis_config,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=40, r=40, t=40, b=40),
            height=height,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12 if is_fullscreen else 10)
        )

        graph_panel = html.Div([
            html.Div([
                html.H5(_('graph_title', tab_title, actual_blank_info), className="m-0")
            ], className="d-flex justify-content-between align-items-center px-3 py-2", 
               style={"backgroundColor": "#0275d8", "color": "white", "borderTopLeftRadius": "4px", "borderTopRightRadius": "4px"}),
            
            html.Div([
                html.P(_('actual_vs_ref', tab_title, actual_blank_info), className="m-0 text-muted")
            ], className="px-3 py-2 bg-light border-bottom"),
            
            dcc.Graph(
                id='individual-graph',
                figure=fig,
                config={
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': ['autoScale2d', 'resetScale2d', 'zoomIn2d', 'zoomOut2d'],
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'displaylogo': False
                },
                style={"height": "700px" if is_fullscreen else "400px", "padding": "10px", "backgroundColor": "white"}
            )
        ], style={
            "border": "1px solid #ccc",
            "borderRadius": "4px",
            "overflow": "hidden",
            "marginTop": "20px",
            "marginBottom": "20px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            "maxWidth": "100%",
            "width": "100%"
        })
        
        return graph_panel

    except Exception as e:
        error_msg = f"❌ Error in graph: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return html.Div([
            html.P(error_msg, className="alert alert-danger"),
            html.Pre(traceback.format_exc(), className="bg-light p-3 small")
        ])

# Callback to update the page content based on URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/' or pathname == '/select_database':
        return create_file_selection_layout()
    elif pathname == '/visualize':
        if not data_store:
            return create_error_layout(_('no_data'))
        return create_visualization_layout()
    elif pathname and pathname.startswith('/load/'):
        file_name = pathname.split('/load/')[1]
        file_path = find_file_path(file_name)
        if file_path and os.path.exists(file_path):
            print(f"[INFO] Found file at: {file_path}")
            if handle_h5_file_loading(file_path):
                return dcc.Location(pathname="/visualize", id="redirect-to-visualize")
        return create_error_layout(_('missing_data').format(file_name))
    elif pathname == '/back':
        if len(file_history) > 1:
            file_history.pop()
            previous_file = file_history[-1]
            file_path = find_file_path(previous_file)
            if file_path and os.path.exists(file_path):
                if handle_h5_file_loading(file_path):
                    return dcc.Location(pathname="/visualize", id="redirect-to-visualize")
        return dcc.Location(pathname="/", id="redirect-to-home")
    else:
        return create_error_layout("Page not found")

# Callback for the load file button
@app.callback(
    Output('url', 'pathname'),
    [Input('load-file-button', 'n_clicks')],
    [State('file-name-input', 'value')]
)
def load_file_button(n_clicks, file_name):
    if n_clicks is None or not file_name:
        return dash.no_update
    
    return f"/load/{file_name}"

# Callback for the back button
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('back-button', 'n_clicks')],
    prevent_initial_call=True
)
def back_button(n_clicks):
    if n_clicks is None:
        return dash.no_update
    
    return "/back"

# Callback to update file info
@app.callback(
    Output('file-info', 'children'),
    [Input('url', 'pathname')]
)
def update_file_info(pathname):
    if current_file_name:
        return html.Div([
            html.P(_('currently_viewing'), className="mb-0"),
            html.Strong(current_file_name)
        ])
    else:
        return html.Div(_('no_file_selected'), className="text-danger")

# Callback to update max row value
@app.callback(
    Output('max-row', 'children'),
    [Input('tabs', 'value')]
)
def update_max_row(tab):
    if not data_store:
        return "0"
    
    if tab == 'all_data' and 'screwdown' in data_store:
        data = data_store['screwdown']
    elif tab not in data_store:
        return "0"
    else:
        data = data_store[tab]
    
    if 'actual_x' not in data or not hasattr(data['actual_x'], 'shape'):
        return "0"
        
    return str(data['actual_x'].shape[0])

# FIXED: Simplified row selection callback that handles all navigation with proper blank info mapping
@app.callback(
    Output('selected-row', 'children'),
    [
        Input('jump-previous-button', 'n_clicks'),
        Input('jump-next-button', 'n_clicks'),
        Input({'type': 'row-select-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
        Input('auto-advance-interval', 'n_intervals'),
        Input('jump-to-row-button', 'n_clicks')
    ],
    [
        State('selected-row', 'children'),
        State('max-row', 'children'),
        State('auto-advance-state', 'children'),
        State('jump-to-row-input', 'value')
    ],
    prevent_initial_call=True
)
def handle_row_selection(prev_clicks, next_clicks, row_button_clicks, 
                        auto_intervals, jump_clicks, current_row, max_row, 
                        auto_advance_state, jump_value):
    """Handle all row selection and navigation with fixed jump functionality"""
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger = ctx.triggered[0]
    trigger_id = trigger['prop_id']
    
    print(f"[DEBUG] ROW SELECTION - Trigger: {trigger_id}")
    
    # Convert values safely
    try:
        current_row_int = int(current_row) if current_row and str(current_row) != '-1' else 0
        max_row_int = int(max_row) if max_row else 0
    except (ValueError, TypeError):
        print(f"[ERROR] Invalid row values: current_row={current_row}, max_row={max_row}")
        return "0"
    
    if max_row_int <= 0:
        print("[DEBUG] No data available")
        return "0"
    
    new_row = current_row_int
    
    # Handle Previous button
    if 'jump-previous-button' in trigger_id:
        new_row = max(0, current_row_int - 1)
        print(f"[DEBUG] PREVIOUS: {current_row_int} -> {new_row}")
    
    # Handle Next button
    elif 'jump-next-button' in trigger_id:
        new_row = min(max_row_int - 1, current_row_int + 1)
        print(f"[DEBUG] NEXT: {current_row_int} -> {new_row}")
    
    # Handle row selection buttons
    elif 'row-select-btn' in trigger_id:
        try:
            import json
            button_id = json.loads(trigger_id.split('.')[0])
            row_index = button_id['index']
            button_idx = next((i for i, x in enumerate(ctx.inputs_list[2]) if x['id'] == button_id), None)
            if button_idx is not None and row_button_clicks[button_idx] > 0:
                new_row = row_index
                print(f"[DEBUG] ROW SELECT BUTTON: selected row {new_row}")
            else:
                return dash.no_update
        except Exception as e:
            print(f"[ERROR] Failed to parse row button: {e}")
            return dash.no_update
    
    # FIXED: Handle jump to specific blank info number
    elif 'jump-to-row-button' in trigger_id:
        if jump_value is not None:
            try:
                target_blank_info = int(jump_value)
                print(f"[DEBUG] JUMP TO: Looking for blank info {target_blank_info}")
                
                # Get the blank info data to find the correct row index
                blank_info_data = data_store.get('blank_info', {}).get('data', [])
                
                if isinstance(blank_info_data, np.ndarray) and len(blank_info_data) > 0:
                    # Find the row index that corresponds to the target blank info number
                    matching_indices = np.where(blank_info_data == target_blank_info)[0]
                    
                    if len(matching_indices) > 0:
                        new_row = matching_indices[0]  # Take the first match
                        print(f"[DEBUG] JUMP TO: Found blank info {target_blank_info} at row index {new_row}")
                        
                        # Validate the row is within bounds
                        if 0 <= new_row < max_row_int:
                            print(f"[DEBUG] JUMP TO: Successfully jumping to row {new_row}")
                        else:
                            print(f"[WARNING] Jump target row {new_row} out of range (0-{max_row_int-1})")
                            return dash.no_update
                    else:
                        print(f"[WARNING] Blank info {target_blank_info} not found in data")
                        return dash.no_update
                else:
                    # Fallback to old logic if blank_info_data is not available
                    print("[WARNING] No blank info data available, using fallback logic")
                    new_row = target_blank_info - 1  # Convert 1-based to 0-based
                    if 0 <= new_row < max_row_int:
                        print(f"[DEBUG] JUMP TO: Fallback jump to row {new_row}")
                    else:
                        print(f"[WARNING] Fallback jump value {target_blank_info} out of range (1-{max_row_int})")
                        return dash.no_update
                        
            except (ValueError, TypeError):
                print(f"[ERROR] Invalid jump value: {jump_value}")
                return dash.no_update
        else:
            return dash.no_update
    
    # Handle auto-advance
    elif 'auto-advance-interval' in trigger_id:
        if auto_advance_state == 'true':
            new_row = (current_row_int + 1) % max_row_int
            print(f"[DEBUG] AUTO-ADVANCE: {current_row_int} -> {new_row}")
        else:
            return dash.no_update
    
    # Ensure new_row is within bounds
    new_row = max(0, min(new_row, max_row_int - 1))
    
    # Only update if the row actually changed
    if new_row != current_row_int:
        print(f"[DEBUG] FINAL ROW SELECTION: {current_row_int} -> {new_row}")
        return str(new_row)
    else:
        print(f"[DEBUG] No row change needed: staying at {current_row_int}")
        return dash.no_update

# Callback to update current row display
@app.callback(
    Output('current-row-display', 'children'),
    [Input('selected-row', 'children')]
)
def update_current_row_display(selected_row):
    if selected_row and selected_row != '-1':
        try:
            row_num = int(selected_row)
            # Get the actual blank info number for display
            blank_info_data = data_store.get('blank_info', {}).get('data', [])
            if isinstance(blank_info_data, np.ndarray) and len(blank_info_data) > row_num >= 0:
                actual_blank_info = blank_info_data[row_num]
                return _('current_row', actual_blank_info)
            else:
                return _('current_row', row_num + 1)
        except (ValueError, TypeError):
            return _('current_row', 1)
    else:
        return _('current_row', 1)

# Page navigation callback that properly updates table display
@app.callback(
    Output('page-store', 'children'),
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks'),
     Input('tabs', 'value'),
     Input('selected-row', 'children')],
    [State('page-store', 'children'),
     State('max-row', 'children')]
)
def update_page_navigation(prev_clicks, next_clicks, tab, selected_row, current_page, max_row):
    """Handle pagination with proper page calculation based on selected row"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return 1
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Reset to page 1 when tab changes
    if trigger_id == 'tabs':
        print(f"[DEBUG] Tab changed to {tab}, resetting to page 1")
        return 1
    
    current_page = int(current_page) if current_page else 1
    max_row = int(max_row) if max_row else 0
    rows_per_page = 5
    max_pages = math.ceil(max_row / rows_per_page) if max_row > 0 else 1
    
    # If selected row changed, calculate which page it should be on
    if trigger_id == 'selected-row' and selected_row and selected_row != '-1':
        try:
            selected_row_int = int(selected_row)
            # Calculate which page this row should be on (1-based)
            page_for_row = (selected_row_int // rows_per_page) + 1
            print(f"[DEBUG] Selected row {selected_row_int} should be on page {page_for_row}")
            return page_for_row
        except (ValueError, TypeError):
            return current_page
    
    # Handle pagination button clicks
    if trigger_id == 'prev-button' and prev_clicks:
        new_page = max(1, current_page - 1)
        print(f"[DEBUG] Previous page: {current_page} -> {new_page}")
        return new_page
    elif trigger_id == 'next-button' and next_clicks:
        new_page = min(current_page + 1, max_pages)
        print(f"[DEBUG] Next page: {current_page} -> {new_page}")
        return new_page
    
    return current_page

# Callback to update pagination controls
@app.callback(
    Output('pagination-controls', 'children'),
    [Input('page-store', 'children'),
     Input('max-row', 'children')]
)
def update_pagination_controls(page, max_row):
    page = int(page) if page else 1
    max_row = int(max_row) if max_row else 0
    rows_per_page = 5
    max_pages = math.ceil(max_row / rows_per_page) if max_row > 0 else 1
    
    print(f"[DEBUG] Pagination controls: page={page}, max_pages={max_pages}, max_row={max_row}")
    
    return html.Div([
        html.Button(_('previous_button'), id="prev-button", 
                  className="btn btn-outline-primary me-2",
                  disabled=page <= 1),
        html.Span(f"{_('page')} {page} {_('of')} {max_pages}", className="mx-2"),
        html.Button(_('next_button'), id="next-button", 
                  className="btn btn-outline-primary ms-2",
                  disabled=page >= max_pages)
    ])

# Table callback that properly uses page number for data filtering
@app.callback(
    Output('table-container', 'children'),
    [Input('tabs', 'value'),
     Input('page-store', 'children'),
     Input('selected-row', 'children')]
)
def update_table(tab, page, selected_row):
    try:
        print(f"[DEBUG] UPDATE TABLE - tab: {tab}, page: {page}, selected_row: {selected_row}")
        if not data_store:
            return html.Div(_('no_data_table'), className="alert alert-warning")

        page = int(page) if page else 1
        selected_row = int(selected_row) if selected_row and selected_row != '-1' else -1

        sd_data = data_store.get('screwdown', {})
        bd_data = data_store.get('bending', {})
        pd_data = data_store.get('profile', {})

        if not all(k in sd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            return html.Div(_('missing_data').format('screwdown'), className="alert alert-warning")
        if not all(k in bd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            return html.Div(_('missing_data').format('bending'), className="alert alert-warning")
        if not all(k in pd_data for k in ['actual_x', 'actual_z', 'ref_x', 'ref_z']):
            return html.Div(_('missing_data').format('profile'), className="alert alert-warning")

        max_rows = min(
            sd_data['actual_x'].shape[0],
            bd_data['actual_x'].shape[0],
            pd_data['actual_x'].shape[0]
        )

        # Get the continuous blank info data
        blank_info_data = data_store.get('blank_info', {}).get('data', [])
        
        rows_per_page = 5
        
        # Use the page number to determine which rows to show
        start_idx = (page - 1) * rows_per_page
        end_idx = min(start_idx + rows_per_page, max_rows)
        
        print(f"[DEBUG] Showing rows {start_idx} to {end_idx-1} (page {page})")

        table_container = html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "60px 100px 80px 1fr",
            "gap": "0px",
            "border": f"1px solid {BORDER_COLOR}",
            "width": "max-content",
            "minWidth": "100%"
        })
        
        # Create header row
        header_row = html.Div(style={
            "display": "contents",
            "fontWeight": "bold",
            "backgroundColor": "#f8f9fa"
        })
        
        # Add header cells
        header_row.children = [
            html.Div("Index", style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": "white",
                "position": "sticky",
                "left": "0",
                "zIndex": "2"
            }),
            html.Div("Blank Info", style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": "white",
                "position": "sticky",
                "left": "60px",
                "zIndex": "2"
            }),
            html.Div("Values", style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": "white",
                "position": "sticky",
                "left": "160px",
                "zIndex": "2"
            })
        ]
        
        # Add data column headers
        if tab == 'all_data':
            data_headers = []
            
            max_points = max(
                sd_data['actual_x'].shape[1] if 'actual_x' in sd_data and hasattr(sd_data['actual_x'], 'shape') else 0,
                bd_data['actual_x'].shape[1] if 'actual_x' in bd_data and hasattr(bd_data['actual_x'], 'shape') else 0,
                pd_data['actual_x'].shape[1] if 'actual_x' in pd_data and hasattr(pd_data['actual_x'], 'shape') else 0
            )
            
            max_display_points = min(max_points, 25)
            total_columns = max_display_points * 3
            
            for i in range(0, max_display_points):
                data_headers.append(html.Div(f"SD{i}", style={
                    "padding": "8px",
                    "textAlign": "center",
                    "border": f"1px solid {BORDER_COLOR}",
                    "minWidth": "120px"
                }))
                
                data_headers.append(html.Div(f"BD{i}", style={
                    "padding": "8px",
                    "textAlign": "center",
                    "border": f"1px solid {BORDER_COLOR}",
                    "minWidth": "120px"
                }))
                
                data_headers.append(html.Div(f"PD{i}", style={
                    "padding": "8px",
                    "textAlign": "center",
                    "border": f"1px solid {BORDER_COLOR}",
                    "minWidth": "120px"
                }))
            
            data_headers_container = html.Div(data_headers, style={
                "display": "grid",
                "gridTemplateColumns": f"repeat({total_columns}, minmax(120px, 1fr))",
                "gap": "0px"
            })
            
            header_row.children.append(data_headers_container)
        else:
            data = {'screwdown': sd_data, 'bending': bd_data, 'profile': pd_data}.get(tab, sd_data)
            prefix = {'screwdown': 'SD', 'bending': 'BD', 'profile': 'PD'}.get(tab, 'SD')
            
            num_columns = data['actual_x'].shape[1] if 'actual_x' in data and hasattr(data['actual_x'], 'shape') else 0
            num_display_columns = min(num_columns, 25)
            
            data_headers = []
            for i in range(0, num_display_columns):
                data_headers.append(html.Div(f"{prefix}{i}", style={
                    "padding": "8px",
                    "textAlign": "center",
                    "border": f"1px solid {BORDER_COLOR}",
                    "minWidth": "120px"
                }))
                
            data_headers_container = html.Div(data_headers, style={
                "display": "grid",
                "gridTemplateColumns": f"repeat({num_display_columns}, minmax(120px, 1fr))",
                "gap": "0px"
            })
            
            header_row.children.append(data_headers_container)
        
        table_container.children = [header_row]
        
        # Create data rows for the current page
        for i in range(start_idx, end_idx):
            is_selected = (i == selected_row)
            
            # Get the actual blank info number for this row
            if isinstance(blank_info_data, np.ndarray) and len(blank_info_data) > i:
                actual_blank_info = blank_info_data[i]
            else:
                actual_blank_info = i + 1
            
            ref_row_style = {
                "display": "contents",
                "backgroundColor": REF_COLOR
            }

            if is_selected:
                ref_row_style["backgroundColor"] = "#e6f7ff"
            
            ref_row = html.Div(style=ref_row_style)
            
            # Make row selection buttons more responsive
            index_cell = html.Div([
                html.Button(
                    "✓" if is_selected else str(i + 1),
                    id={'type': 'row-select-btn', 'index': i},
                    className="btn btn-sm btn-primary" if is_selected else "btn btn-sm btn-outline-secondary",
                    style={
                        "width": "40px", 
                        "height": "30px", 
                        "padding": "0", 
                        "borderRadius": "4px",
                        "fontWeight": "bold",
                        "fontSize": "12px"
                    }
                )
            ], style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": "#e6f7ff" if is_selected else "white",
                "position": "sticky",
                "left": "0",
                "zIndex": "1",
                "gridRow": "span 2"
            })
            
            # Display the continuous blank info number
            blank_info_cell = html.Div(str(actual_blank_info), style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": "#e6f7ff" if is_selected else "white",
                "position": "sticky",
                "left": "60px",
                "zIndex": "1",
                "gridRow": "span 2"
            })
            
            ref_label_cell = html.Div(html.Span(_('ref_label'), style={"color": "black", "fontWeight": "bold"}), style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": REF_COLOR if not is_selected else "#e6f7ff",
                "position": "sticky",
                "left": "160px",
                "zIndex": "1"
            })
            
            ref_row.children = [index_cell, blank_info_cell, ref_label_cell]
            
            actual_row_style = {
                "display": "contents",
                "backgroundColor": ACTUAL_COLOR
            }

            if is_selected:
                actual_row_style["backgroundColor"] = "#e6f7ff"
            
            actual_row = html.Div(style=actual_row_style)
            
            actual_label_cell = html.Div(html.Span(_('actual_label'), style={"color": "black", "fontWeight": "bold"}), style={
                "padding": "8px",
                "textAlign": "center",
                "border": f"1px solid {BORDER_COLOR}",
                "backgroundColor": ACTUAL_COLOR if not is_selected else "#e6f7ff",
                "position": "sticky",
                "left": "160px",
                "zIndex": "1"
            })
            
            actual_row.children = [actual_label_cell]
            
            # Add data cells - Remove Z values ONLY for reference midpoints
            if tab == 'all_data':
                ref_data_cells = []
                actual_data_cells = []
                
                max_points = max(
                    sd_data['actual_x'].shape[1] if 'actual_x' in sd_data and hasattr(sd_data['actual_x'], 'shape') else 0,
                    bd_data['actual_x'].shape[1] if 'actual_x' in bd_data and hasattr(bd_data['actual_x'], 'shape') else 0,
                    pd_data['actual_x'].shape[1] if 'actual_x' in pd_data and hasattr(pd_data['actual_x'], 'shape') else 0
                )
                
                max_display_points = min(max_points, 25)
                total_columns = max_display_points * 3

                for j in range(max_display_points):
                    # Add SD reference cell - Check if midpoint
                    if j < len(sd_data['ref_x']):
                        ref_x = sd_data['ref_x'][j]
                        ref_z = sd_data['ref_z'][j]
                        # Check if this is a midpoint using the is_midpoint array
                        is_midpoint = sd_data.get('is_midpoint', [False] * len(sd_data['ref_x']))
                        if j < len(is_midpoint) and is_midpoint[j]:
                            # For midpoints, show only X value
                            display_text = str(int(ref_x))
                        else:
                            # For regular points, show (x, z)
                            display_text = f"({int(ref_x)}, {int(ref_z)})"
                    else:
                        display_text = "0"
                    
                    ref_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": REF_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Add SD actual cell - Keep (x, z) format for actual data
                    if j < sd_data['actual_x'].shape[1] and i < sd_data['actual_x'].shape[0]:
                        actual_x = sd_data['actual_x'][i][j]
                        actual_z = sd_data['actual_z'][i][j]
                        display_text = f"({int(actual_x)}, {int(actual_z)})"
                    else:
                        display_text = "(0, 0)"
                    
                    actual_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": ACTUAL_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Add BD reference cell - Check if midpoint
                    if j < len(bd_data['ref_x']):
                        ref_x = bd_data['ref_x'][j]
                        ref_z = bd_data['ref_z'][j]
                        # Check if this is a midpoint using the is_midpoint array
                        is_midpoint = bd_data.get('is_midpoint', [False] * len(bd_data['ref_x']))
                        if j < len(is_midpoint) and is_midpoint[j]:
                            # For midpoints, show only X value
                            display_text = str(int(ref_x))
                        else:
                            # For regular points, show (x, z)
                            display_text = f"({int(ref_x)}, {int(ref_z)})"
                    else:
                        display_text = "0"
                    
                    ref_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": REF_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Add BD actual cell - Keep (x, z) format for actual data
                    if j < bd_data['actual_x'].shape[1] and i < bd_data['actual_x'].shape[0]:
                        actual_x = bd_data['actual_x'][i][j]
                        actual_z = bd_data['actual_z'][i][j]
                        display_text = f"({int(actual_x)}, {int(actual_z)})"
                    else:
                        display_text = "(0, 0)"
                    
                    actual_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": ACTUAL_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Add PD reference cell - Check if midpoint
                    if j < len(pd_data['ref_x']):
                        ref_x = pd_data['ref_x'][j]
                        ref_z = pd_data['ref_z'][j]
                        # Check if this is a midpoint using the is_midpoint array
                        is_midpoint = pd_data.get('is_midpoint', [False] * len(pd_data['ref_x']))
                        if j < len(is_midpoint) and is_midpoint[j]:
                            # For midpoints, show only X value
                            display_text = str(int(ref_x))
                        else:
                            # For regular points, show (x, z)
                            display_text = f"({int(ref_x)}, {int(ref_z)})"
                    else:
                        display_text = "0"
                    
                    ref_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": REF_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Add PD actual cell - Keep (x, z) format for actual data
                    if j < pd_data['actual_x'].shape[1] and i < pd_data['actual_x'].shape[0]:
                        actual_x = pd_data['actual_x'][i][j]
                        actual_z = pd_data['actual_z'][i][j]
                        display_text = f"({int(actual_x)}, {int(actual_z)})"
                    else:
                        display_text = "(0, 0)"
                    
                    actual_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": ACTUAL_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                
                ref_data_container = html.Div(ref_data_cells, style={
                    "display": "grid",
                    "gridTemplateColumns": f"repeat({total_columns}, minmax(120px, 1fr))",
                    "gap": "0px"
                })

                actual_data_container = html.Div(actual_data_cells, style={
                    "display": "grid",
                    "gridTemplateColumns": f"repeat({total_columns}, minmax(120px, 1fr))",
                    "gap": "0px"
                })
                
                ref_row.children.append(ref_data_container)
                actual_row.children.append(actual_data_container)
            else:
                data = {'screwdown': sd_data, 'bending': bd_data, 'profile': pd_data}.get(tab, sd_data)
                
                ref_data_cells = []
                actual_data_cells = []
                
                num_columns = data['actual_x'].shape[1] if 'actual_x' in data and hasattr(data['actual_x'], 'shape') else 0
                num_display_columns = min(num_columns, 25)

                for j in range(num_display_columns):
                    # Reference cell - Check if midpoint
                    if j < len(data['ref_x']):
                        ref_x = data['ref_x'][j]
                        ref_z = data['ref_z'][j]
                        # Check if this is a midpoint using the is_midpoint array
                        is_midpoint = data.get('is_midpoint', [False] * len(data['ref_x']))
                        if j < len(is_midpoint) and is_midpoint[j]:
                            # For midpoints, show only X value
                            display_text = str(int(ref_x))
                        else:
                            # For regular points, show (x, z)
                            display_text = f"({int(ref_x)}, {int(ref_z)})"
                    else:
                        display_text = "0"
                    
                    ref_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": REF_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                    
                    # Actual cell - Keep (x, z) format for actual data
                    if j < data['actual_x'].shape[1] and i < data['actual_x'].shape[0]:
                        actual_x = data['actual_x'][i][j]
                        actual_z = data['actual_z'][i][j]
                        display_text = f"({int(actual_x)}, {int(actual_z)})"
                    else:
                        display_text = "(0, 0)"
                    
                    actual_data_cells.append(html.Div(
                        display_text, 
                        style={
                            "padding": "8px",
                            "textAlign": "center",
                            "border": f"1px solid {BORDER_COLOR}",
                            "color": "black",
                            "minWidth": "120px",
                            "backgroundColor": ACTUAL_COLOR if not is_selected else "#e6f7ff"
                        }
                    ))
                
                ref_data_container = html.Div(ref_data_cells, style={
                    "display": "grid",
                    "gridTemplateColumns": f"repeat({num_display_columns}, minmax(120px, 1fr))",
                    "gap": "0px"
                })
                
                actual_data_container = html.Div(actual_data_cells, style={
                    "display": "grid",
                    "gridTemplateColumns": f"repeat({num_display_columns}, minmax(120px, 1fr))",
                    "gap": "0px"
                })
                
                ref_row.children.append(ref_data_container)
                actual_row.children.append(actual_data_container)
            
            table_container.children.extend([ref_row, actual_row])
        
        return html.Div(
            table_container,
            style={
                "overflowX": "auto",
                "width": "100%",
                "maxWidth": "100vw",
                "paddingBottom": "15px",
                "maxHeight": "70vh",
                "overflowY": "auto",
                "margin": "0",
                "padding": "0"
            }
        )
    except Exception as e:
        error_msg = f"Error in table: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return html.Div(error_msg, className="alert alert-danger")

# Callback to show/hide zoom controls when a row is selected
@app.callback(
    Output('zoom-controls', 'style'),
    [Input('selected-row', 'children')]
)
def toggle_zoom_controls(selected_row):
    if not selected_row or selected_row == '-1':
        return {"display": "none"}
    else:
        return {"display": "block"}

# Callback to handle zoom control buttons
@app.callback(
    Output('zoom-state', 'children'),
    [Input('auto-scale-button', 'n_clicks'),
     Input('zoom-in-button', 'n_clicks'),
     Input('zoom-out-button', 'n_clicks'),
     Input('reset-zoom-button', 'n_clicks')],
    [State('zoom-state', 'children')]
)
def update_zoom_state(auto_scale_clicks, zoom_in_clicks, zoom_out_clicks, reset_clicks, current_state):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_state
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'auto-scale-button':
        return 'auto'
    elif button_id == 'zoom-in-button':
        return 'zoom_in'
    elif button_id == 'zoom-out-button':
        return 'zoom_out'
    elif button_id == 'reset-zoom-button':
        return 'default'
    
    return current_state

# Callback to handle fullscreen toggle
@app.callback(
    Output('fullscreen-state', 'children'),
    [Input('fullscreen-button', 'n_clicks')],
    [State('fullscreen-state', 'children')]
)
def toggle_fullscreen(n_clicks, current_state):
    if n_clicks is None:
        return current_state
    
    return 'true' if current_state == 'false' else 'false'

# More responsive graph container callback
@app.callback(
    [Output('graph-container', 'children'),
     Output('graph-container', 'style')],
    [Input('tabs', 'value'),
     Input('selected-row', 'children'),
     Input('zoom-state', 'children'),
     Input('fullscreen-state', 'children')],
    prevent_initial_call=False
)
def update_graph_container_responsive(tab, selected_row, zoom_state, fullscreen_state):
    print(f"[DEBUG] *** GRAPH UPDATE *** tab: {tab}, row: {selected_row}, zoom: {zoom_state}")
    
    if not selected_row or str(selected_row) == '-1':
        print("[DEBUG] No row selected, hiding graph")
        return [], {"display": "none"}

    try:
        selected_row_int = int(selected_row)
        print(f"[DEBUG] Creating graph for row {selected_row_int}")
    except (ValueError, TypeError):
        print(f"[ERROR] Invalid selected_row: {selected_row}")
        return [], {"display": "none"}
    
    is_fullscreen = fullscreen_state == 'true'
    
    # Force graph recreation
    graph_content = create_graph_section(tab, selected_row_int, zoom_state, is_fullscreen)
    
    base_style = {"display": "block", "maxWidth": "100%", "width": "100%"}
    
    if is_fullscreen:
        # Fullscreen logic (keep existing)
        blank_info_data = data_store.get('blank_info', {}).get('data', [])
        if isinstance(blank_info_data, np.ndarray) and len(blank_info_data) > selected_row_int >= 0:
            actual_blank_info = blank_info_data[selected_row_int]
        else:
            actual_blank_info = selected_row_int + 1
        
        fullscreen_style = {
            **base_style,
            "position": "fixed",
            "top": "0",
            "left": "0", 
            "width": "100vw",
            "height": "100vh",
            "backgroundColor": "white",
            "zIndex": "9999",
            "padding": "20px",
            "boxSizing": "border-box",
            "overflow": "auto"
        }
        
        fullscreen_controls = html.Div([
            html.Div([
                html.Div([
                    html.Button(
                        [html.I(className="bi bi-chevron-left me-1"), _('previous_button')],
                        id="fullscreen-prev-row",
                        className="btn btn-outline-primary me-2",
                        style={"fontSize": "14px", "padding": "8px 16px"}
                    ),
                    html.Span(
                        f"Row {actual_blank_info}",
                        className="badge bg-primary fs-6 px-3 py-2 me-2",
                        style={"fontSize": "16px", "fontWeight": "bold"}
                    ),
                    html.Button(
                        [_('next_button'), html.I(className="bi bi-chevron-right ms-1")],
                        id="fullscreen-next-row",
                        className="btn btn-outline-primary me-3",
                        style={"fontSize": "14px", "padding": "8px 16px", "fontWeight": "bold"}
                    )
                ], className="d-flex align-items-center"),
                
                html.Button(
                    [html.I(className="bi bi-fullscreen-exit me-2"), _('exit_fullscreen')],
                    id="exit-fullscreen-button",
                    className="btn btn-danger",
                    style={"fontSize": "14px", "padding": "8px 16px", "fontWeight": "bold"}
                )
            ], className="d-flex justify-content-between align-items-center mb-3 p-3 bg-light rounded border"),
        ])
        
        graph_content = html.Div([
            fullscreen_controls,
            html.Div(graph_content, style={"marginTop": "10px"})
        ])
        
        return graph_content, fullscreen_style
    
    print(f"[DEBUG] Returning graph for row {selected_row_int}")
    return graph_content, base_style

# Callback to handle exit fullscreen button
@app.callback(
    Output('fullscreen-state', 'children', allow_duplicate=True),
    [Input('exit-fullscreen-button', 'n_clicks')],
    prevent_initial_call=True
)
def exit_fullscreen(n_clicks):
    if n_clicks:
        return 'false'
    return dash.no_update

# Language switching callback
@app.callback(
    [Output('current-language', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('btn-lang-en', 'n_clicks'),
     Input('btn-lang-de', 'n_clicks')],
    [State('url', 'pathname')],
    prevent_initial_call=True
)
def switch_language_callback(en_clicks, de_clicks, pathname):
    global LANGUAGE
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    print(f"[INFO] Language button clicked: {button_id}")

    if button_id == 'btn-lang-en':
        switch_language('en')
        print(f"[INFO] Language switched to English")
        return 'en', pathname
    elif button_id == 'btn-lang-de':
        switch_language('de')
        print(f"[INFO] Language switched to German")
        return 'de', pathname

    return dash.no_update, dash.no_update

# Callback to conditionally show coil dropdown
@app.callback(
    Output('coil-selection-container', 'children'),
    [Input('url', 'pathname')]
)
def update_coil_dropdown_visibility(pathname):
    global available_coils, selected_coil
    
    if not current_file_name or not available_coils:
        return []
    
    # Only show dropdown if there are multiple coils
    if len(available_coils) > 1:
        return html.Div([
            html.Label(_('coil_selection'), className="me-2", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id='coil-dropdown',
                options=[{'label': coil, 'value': coil} for coil in available_coils],
                value=selected_coil if selected_coil in available_coils else available_coils[0],
                clearable=False,
                style={"width": "300px", "display": "inline-block"}
            )
        ], className="d-flex align-items-center")
    else:
        # If only one coil, show it as text (no dropdown needed)
        if available_coils:
            return html.Div([
                html.Label(_('coil_selection'), className="me-2", style={"fontWeight": "bold"}),
                html.Span(available_coils[0], className="badge bg-primary fs-6 px-3 py-2")
            ], className="d-flex align-items-center")
        else:
            return []

# Add a callback to handle coil selection and reload the page
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('coil-dropdown', 'value')],
    [State('url', 'pathname')],
    prevent_initial_call=True
)
def update_coil_and_reload(coil_value, pathname):
    global selected_coil, selected_row

    if coil_value and coil_value != selected_coil:
        selected_coil = coil_value
        # Reset selected_row when coil changes
        selected_row = 0
        print(f"[INFO] Coil selection changed to: {selected_coil}")
        
        if current_file_name:
            file_path = find_file_path(current_file_name)
            if file_path and os.path.exists(file_path):
                handle_h5_file_loading(file_path)
        
        return pathname
    
    return dash.no_update

# Auto-advance state management
@app.callback(
    Output('auto-advance-state', 'children'),
    [Input('auto-advance-checkbox', 'value')]
)
def update_auto_advance_state(checkbox_value):
    is_checked = 'auto_advance' in (checkbox_value or [])
    auto_advance_state = 'true' if is_checked else 'false'
    
    print(f"[DEBUG] Auto-advance checkbox changed: {is_checked}, state: {auto_advance_state}")
    
    return auto_advance_state

# Interval control for auto-advance
@app.callback(
    Output('auto-advance-interval', 'disabled'),
    [Input('auto-advance-state', 'children'),
     Input('selected-row', 'children')]
)
def control_auto_advance_interval(auto_advance_state, selected_row):
    should_disable = not (auto_advance_state == 'true' and selected_row and selected_row != '-1')
    print(f"[DEBUG] Interval disabled: {should_disable}, auto_advance_state: {auto_advance_state}, selected_row: {selected_row}")
    return should_disable

# Callback to update auto-advance status indicator
@app.callback(
    Output('auto-advance-status', 'children'),
    [Input('auto-advance-state', 'children'),
     Input('selected-row', 'children')]
)
def update_auto_advance_status(auto_advance_state, selected_row):
    if auto_advance_state == 'true':
        if selected_row and selected_row != '-1':
            return html.Span("🔄 Auto-advancing...", style={"color": "#28a745"})
        else:
            return html.Span("⏸️ Select a row to start", style={"color": "#ffc107"})
    else:
        return html.Span("⏹️ Auto-advance off", style={"color": "#6c757d"})

# Callback for fullscreen navigation controls
@app.callback(
    Output('selected-row', 'children', allow_duplicate=True),
    [Input('fullscreen-prev-row', 'n_clicks'),
     Input('fullscreen-next-row', 'n_clicks')],
    [State('selected-row', 'children'),
     State('max-row', 'children')],
    prevent_initial_call=True
)
def handle_fullscreen_navigation(prev_clicks, next_clicks, current_row, max_row):
    ctx = dash.callback_context
    if not ctx.triggered or not current_row or current_row == '-1':
        return dash.no_update
    
    current_row_int = int(current_row)
    max_row_int = int(max_row) if max_row else 0
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'fullscreen-prev-row' and prev_clicks:
        new_row = max(0, current_row_int - 1)
        print(f"[DEBUG] Fullscreen previous: {current_row_int} -> {new_row}")
        return str(new_row)
    elif button_id == 'fullscreen-next-row' and next_clicks:
        new_row = min(max_row_int - 1, current_row_int + 1)
        print(f"[DEBUG] Fullscreen next: {current_row_int} -> {new_row}")
        return str(new_row)
    
    return dash.no_update

# Add this new callback after the existing callbacks
@app.callback(
    Output('selected-row', 'children', allow_duplicate=True),
    [Input('tabs', 'value')],
    [State('max-row', 'children')],
    prevent_initial_call=True
)
def initialize_first_row(tab, max_row):
    """Initialize to first row when tab changes or data loads"""
    max_row_int = int(max_row) if max_row else 0
    if max_row_int > 0:
        print(f"[DEBUG] Initializing to first row for tab: {tab}")
        return "0"
    return dash.no_update

# Main entry point
if __name__ == '__main__':
    h5_files = find_h5_files()
    
    if h5_files:
        print(f"[INFO] Found {len(h5_files)} H5 files: {h5_files}")
        
        loaded = False
        for file_name in h5_files:
            file_path = find_file_path(file_name)
            if file_path and os.path.exists(file_path):
                print(f"[INFO] Attempting to load: {file_path}")
                if handle_h5_file_loading(file_path):
                    print(f"[INFO] Successfully loaded data from {file_path}")
                    loaded = True
                    break
        
        if not loaded:
            print("[WARNING] Could not load any of the available H5 files.")
    else:
        print("[WARNING] No H5 files found.")

    print("[INFO] Starting Dash application on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
