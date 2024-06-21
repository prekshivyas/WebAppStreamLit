import streamlit as st
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PIL import Image


# Initialize SessionState to track dynamic QA pairs
class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# Google Drive API credentials setup
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'D:\streamlit\WebAppStreamLit\cred\dynamic-poet-427110-n5-e4bd45401364.json'  # Update with your credentials file path

# Authenticate and create a Google Drive API service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Function to get folder ID by name
def get_folder_id(parent_folder_id, folder_name):
    """Searches for a folder by name within the specified parent folder."""
    results = drive_service.files().list(
        q=f"'{parent_folder_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive', 
        fields='nextPageToken, files(id, name)'
    ).execute()

    items = results.get('files', [])
    if items:
        return items[0]['id']
    else:
        return None

# Function to list files in a specific folder
def list_files_in_folder(folder_id):
    """Lists all files in a specific folder."""
    query = f"'{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])
    return items

# Function to download image by file ID
@st.cache_data(show_spinner=False)
def download_image(file_id, file_name):
    """Downloads an image file given its file ID."""
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = io.BytesIO(request.execute())
    return Image.open(downloader)

# Streamlit setup
st.set_page_config(layout="wide")
st.title("MultiChart QA Generation")

# Display instructions in an expander
with st.expander("QA Generation Instructions/Rubric"):
    st.markdown("Instructions and Examples: [Click here](https://google.com)")

# Text input for Anchor Chart ID
chart_id = st.text_input("Enter Chart ID (0 to 100)", "")

# Display Anchor Chart images based on input ID
if st.button("Display") and chart_id.strip():  # Check if Display button is clicked and chart_id is not empty
    images_final_id = '11Ewq0e2Z7j4MkbLcuXWTUItL3DlCi5JB'

    # Get folder IDs for 'anchor_0' and 'similar_0'
    anchor_chart_id = get_folder_id(images_final_id, f'anchor_{chart_id}')
    similar_chart_id = get_folder_id(images_final_id, f'anchor_{chart_id}_0')

    # List to store folder IDs
    ids_to_display = [anchor_chart_id, similar_chart_id]

    # Display images side by side
    if anchor_chart_id and similar_chart_id:
        st.subheader("MultiChartPair")

        # Create columns for each folder ID
        col1, col2 = st.columns(2)

        # Display images for each folder ID in separate columns
        for idx, folder_id in enumerate(ids_to_display):
            files = list_files_in_folder(folder_id)

            with col1 if idx == 0 else col2:
                if files:
                    st.subheader(f"Chart {idx + 1}:")
                    for file in files:
                        if file['mimeType'] == 'image/png':
                            image = download_image(file['id'], file['name'])
                            st.image(image, caption=file['name'], use_column_width=True)
                else:
                    st.warning(f"No files found in Folder {idx + 1}.")
    else:
        st.warning("One or both folder IDs not found. Please check your folder names.")

# QA Category selection
selected_category = st.selectbox("Category", [
    "Abstract Numerical Analysis", 
    "Entity Inference", 
    "Contextual and Lexical Reasoning with Range Estimation"
])

# Initialize or get existing SessionState
if 'session_state' not in st.session_state:
    st.session_state.session_state = SessionState(qa_pairs={})

session_state = st.session_state.session_state

# Display existing QA pairs and allow user to add new pairs
for i, qa_pair in enumerate(session_state.qa_pairs.get(selected_category, [])):
    st.write(f"{selected_category} - Question {i + 1}")
    question_key = f"{selected_category.lower().replace(' ', '_')}_question_{i}"
    answer_key = f"{selected_category.lower().replace(' ', '_')}_answer_{i}"
    qa_pair["question"] = st.text_area(f"{selected_category} - Question {i + 1}", value=qa_pair.get("question", ""), key=question_key)
    qa_pair["answer"] = st.text_area(f"{selected_category} - Answer {i + 1}", value=qa_pair.get("answer", ""), key=answer_key)

# Add new QA pair button
if len(session_state.qa_pairs.get(selected_category, [])) < 2:
    add_button = st.button("Add QA Pair", on_click=lambda: add_qa_pair(session_state))
else:
    st.warning(f"Maximum 2 QA pairs allowed per category.")
    add_button = None  # Use this to control re-rendering behavior

# Submit QA Pair button for the current category
if any(qa_pair["question"] and qa_pair["answer"] for qa_pair in session_state.qa_pairs.get(selected_category, [])):
    submit_button = st.button(f"Submit {selected_category} QA Pair")
else:
    submit_button = st.button(f"Submit {selected_category} QA Pair", disabled=True)

# Check if all categories have at least 1 QA pair filled and max 2 QA pairs
min_qa_pairs_per_category = 1
max_qa_pairs_per_category = 2
categories_completed = all(
    min_qa_pairs_per_category <= len(session_state.qa_pairs.get(category, [])) <= max_qa_pairs_per_category
    for category in ["Abstract Numerical Analysis", "Entity Inference", "Contextual and Lexical Reasoning with Range Estimation"]
)

# Submit All button when conditions are met
if categories_completed:
    if all(
        any(qa_pair["question"] and qa_pair["answer"] for qa_pair in session_state.qa_pairs.get(category, []))
        for category in ["Abstract Numerical Analysis", "Entity Inference", "Contextual and Lexical Reasoning with Range Estimation"]
    ):
        submit_all_button = st.button("Submit All QA for this MultiChart")
        if submit_all_button:
            # Lock answers or perform submission actions
            st.write("All QA pairs for this multichart submitted and locked.")
    else:
        submit_all_button = st.button("Submit All QA for this MultiChart", disabled=True)
else:
    submit_all_button = st.button("Submit All QA for this MultiChart", disabled=True)

# Function to add a new QA pair dynamically
def add_qa_pair(session_state):
    if selected_category not in session_state.qa_pairs:
        session_state.qa_pairs[selected_category] = []
    if len(session_state.qa_pairs[selected_category]) < 2:
        session_state.qa_pairs[selected_category].append({"question": "", "answer": ""})
    else:
        st.warning(f"Maximum 2 QA pairs allowed per category.")

# Ensure components are re-rendered appropriately
if add_button is None:
    st.experimental_rerun()

if submit_button:
    st.experimental_rerun()

if submit_all_button:
    st.experimental_rerun()
