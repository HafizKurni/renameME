import streamlit as st
import pandas as pd
import os
import zipfile
import io

def process_and_rename_zip(uploaded_zip, new_names_list):
    """
    Renames files inside an uploaded zip file based on a list of new names
    and returns a new zip file containing the renamed files.
    """
    try:
        # Create an in-memory byte buffer for the output zip file
        output_buffer = io.BytesIO()

        # Open the uploaded zip file
        with zipfile.ZipFile(uploaded_zip, 'r') as input_zip, \
             zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as output_zip:

            # Get the list of original files in the zip
            original_files = input_zip.namelist()
            
            # Filter out any directory entries from the file list
            original_files = [f for f in original_files if not f.endswith('/')]
            
            # --- MODIFIED: Sort files numerically instead of alphabetically ---
            # This ensures that files like '10.jpg' don't come before '2.jpg'.
            # We extract the number from the filename (e.g., '10' from '10.jpg')
            # and use it as the key for sorting.
            def get_number(filename):
                try:
                    name, _ = os.path.splitext(filename)
                    return int(name)
                except ValueError:
                    # If the filename isn't a number (e.g., 'image.jpg'),
                    # return a large number to put it at the end.
                    return float('inf')

            original_files.sort(key=get_number)
            
            # Check if the number of new names matches the number of files
            if len(original_files) != len(new_names_list):
                st.error(f"Error: The number of new names ({len(new_names_list)}) "
                         f"does not match the number of files in the zip ({len(original_files)}).")
                return None

            # Iterate through the files and rename them
            for i, original_filename in enumerate(original_files):
                # Get the file extension from the original name
                _, ext = os.path.splitext(original_filename)
                
                # Get the new name from the list and append the original extension
                new_name_with_ext = new_names_list[i].strip() + ext
                
                # Read the content of the original file
                with input_zip.open(original_filename) as file_content:
                    # Write the content to the new zip file with the new name
                    output_zip.writestr(new_name_with_ext, file_content.read())
                    st.success(f"Renamed '{original_filename}' to '{new_name_with_ext}'")
        
        output_buffer.seek(0)
        return output_buffer
    except Exception as e:
        st.error(f"An error occurred during file processing: {e}")
        return None

# --- STREAMLIT APP LAYOUT ---

st.set_page_config(page_title="Bulk File Renamer", page_icon="📝")

st.title("Bulk File Renamer")

st.markdown("""
This app renames files in a ZIP archive based on a list of new names.
You can provide the names by either uploading a data file or pasting them directly.
""")

st.subheader("1. Upload your files")
uploaded_zip = st.file_uploader(
    "Upload a ZIP file containing the files to rename.",
    type=['zip']
)

st.subheader("2. Provide the new names")
name_input_method = st.radio(
    "Choose how to provide the list of new names:",
    ("Paste names manually", "Upload a data file (Excel/CSV)")
)

new_names_list = []
if name_input_method == "Upload a data file (Excel/CSV)":
    uploaded_data_file = st.file_uploader(
        "Upload an Excel (.xlsx) or CSV (.csv) file.",
        type=['xlsx', 'csv']
    )
    if uploaded_data_file:
        col1, col2 = st.columns(2)
        with col1:
            old_name_col = st.text_input("Column name for old filenames:", value="namafile")
        with col2:
            new_name_col = st.text_input("Column name for new filenames:", value="nama")
        
        try:
            if uploaded_data_file.name.endswith('.csv'):
                rename_df = pd.read_csv(uploaded_data_file)
            else:
                rename_df = pd.read_excel(uploaded_data_file)
            
            if old_name_col in rename_df.columns and new_name_col in rename_df.columns:
                new_names_list = rename_df[new_name_col].tolist()
            else:
                st.error("Error: The specified column names were not found in the data file.")
                st.stop()
        except Exception as e:
            st.error(f"An error occurred while reading the data file: {e}")
            st.stop()

elif name_input_method == "Paste names manually":
    new_names_input = st.text_area(
        "Paste the list of new names here, one name per line.",
        height=300
    )
    if new_names_input:
        new_names_list = [name.strip() for name in new_names_input.split('\n') if name.strip()]

if st.button("Start Renaming"):
    if uploaded_zip and new_names_list:
        st.subheader("Renaming in progress...")
        
        renamed_zip = process_and_rename_zip(uploaded_zip, new_names_list)
        
        if renamed_zip:
            st.subheader("4. Download your renamed files")
            st.download_button(
                label="Download Renamed Files",
                data=renamed_zip,
                file_name="renamed_files.zip",
                mime="application/zip"
            )
            st.success("Your files have been successfully renamed and are ready for download!")
    else:
        st.warning("Please upload a ZIP file and provide a list of new names to start renaming.")
