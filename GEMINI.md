# PG Machine Application

## Project Overview
This project is a Streamlit application named "PG Machine" (v116 Core), designed to manage leads and opportunities. It provides a user interface to:
- **Import data from Excel files:** Supports two formats: "Leads Propios" and "Forecast BMC".
- **Manually add individual entries:** For accounts, projects, amounts, and categories.
- **Categorize and display opportunities:** Organized into "LEADS", "OFFICIAL", and "GTM" categories.
- **Manage activities for each opportunity:** Users can add and track activities (Email, Call, Meeting, Assignment) with associated SLAs, dates, and descriptions. Activities can be marked as "Completed" or "Answered".

The application uses Streamlit's session state for in-memory data storage, meaning data is persistent for the duration of a user's session but not saved permanently to disk.

## Building and Running
This is a Python Streamlit application. To run it, you need to have Python and Streamlit installed.

### Prerequisites
- Python 3.x
- Streamlit (`pip install streamlit`)
- Pandas (`pip install pandas`)
- openpyxl (`pip install openpyxl`) - for reading Excel files

### How to Run
1.  Ensure you have all prerequisites installed.
2.  Navigate to the project directory in your terminal.
3.  Run the Streamlit application using the following command:
    ```bash
    streamlit run pg_machine_app.py
    ```
4.  The application will open in your web browser.

## Development Conventions
- **Language:** The code, comments, and user interface elements are primarily in Spanish.
- **Frameworks:** Streamlit for the web application, Pandas for data manipulation.
- **Styling:** Custom CSS is embedded within the Streamlit application using `st.markdown` to define styles for various UI components.
