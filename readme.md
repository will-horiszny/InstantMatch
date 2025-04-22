# UTD Instant Match

Automate the UTD Student Organizations Match Card using LLMs!

## Prerequisites

*   Python 3.x installed
*   pip (Python package installer)
*   A Google Account
*   A Google Cloud Platform (GCP) Project
*   A Google Form you have owner/editor access to
*   A Gemini API Key

## Setup Instructions

Follow these steps to set up and run the project:

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies**
    Make sure you have Python and pip installed. Then, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Google Cloud Project & Credentials**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   **Enable APIs:** Ensure the following APIs are enabled for your project:
        *   Google Forms API
        *   Gmail API
    *   **Configure OAuth Consent Screen:**
        *   Navigate to "APIs & Services" -> "OAuth consent screen".
        *   Choose "External" (unless all users are within your Google Workspace org).
        *   Fill in the required application details (App name, User support email, Developer contact information).
        *   **Add Scopes:** Click "Add or Remove Scopes" and add the following scopes manually:
            *   `https://www.googleapis.com/auth/forms.body.readonly`
            *   `https://www.googleapis.com/auth/forms.responses.readonly`
            *   `https://www.googleapis.com/auth/gmail.send`
        *   Add Test Users if your app is in "Testing" mode (include the Google account you will use to run the script).
        *   Save and continue through the screens.
    *   **Create OAuth 2.0 Client ID:**
        *   Navigate to "APIs & Services" -> "Credentials".
        *   Click "+ CREATE CREDENTIALS" -> "OAuth client ID".
        *   Select "Desktop app" as the Application type.
        *   Give it a name (e.g., "Forms Gemini Responder Credentials").
        *   Click "Create".
    *   **Download Credentials:** After creation, click the download button (JSON icon) for the newly created Client ID. Rename the downloaded file to `credentials.json` and place it in the root directory of this project. **Do not commit this file to public version control.**

4.  **Configure Google Form ID**
    *   Open the `forms.py` file in your editor.
    *   Find the variable holding the Form ID (it might be named `FORM_ID` or similar).
    *   Replace the placeholder value with your actual Google Form ID. You can find the ID in the URL of your form when editing it (it's the long string between `/d/` and `/edit`).
    ```python
    # Example in forms.py
    FORM_ID = 'YOUR_GOOGLE_FORM_ID_HERE'
    ```

5.  **Configure Gemini API Key**
    *   You need to provide your Gemini API Key to the application. For now, the application just reads from a file named `secrets`.
## Running the Code

1.  Navigate to the project's root directory in your terminal.
2.  Run the main script:
    ```bash
    python forms.py
    ```
3.  **First Run - Google Authentication:**
    *   When you run the script for the first time, it will likely open a web browser window asking you to log in to your Google Account.
    *   **Log in using the Google Account that has owner/editor access to the Google Form specified in `forms.py`.**
    *   Review the permissions requested (they should match the scopes you configured: view forms, view responses, send email).
    *   Grant access.
    *   The script should then proceed. A `token.json` (or similar) file might be created in the project directory to store your authorization credentials for future runs. **Do not commit this `token.json` file to version control.**

4.  **Subsequent Runs:** On subsequent runs, the script should use the saved `token.json` file and won't require you to log in via the browser again, unless the token expires or is revoked.

## How it Works

*   The script authenticates with Google using OAuth 2.0 (`credentials.json`, `token.json`).
*   It uses the Google Forms API to fetch responses from the specified form.
*   Each response is processed, calling Gemini API using your `GEMINI_API_KEY`.
*   Results emails are constructed and sent using the Gmail API via the authenticated user's account.