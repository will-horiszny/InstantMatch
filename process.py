import base64
import json
import random
import sqlite3
from email.mime.text import MIMEText

import google.generativeai as genai
from googleapiclient.errors import HttpError

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/forms.body.readonly',  # NEW
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
FORM_ID = 'YOUR_FORM_ID'
POLL_INTERVAL = 60
PROCESSED_FILE = 'processed_responses.txt'
GEMINI_API_KEY = None
with open('secrets') as f:
    GEMINI_API_KEY = f.read()
DB_NAME = 'orgs.sqlite'

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)


def query_organizations(selected_categories):
    """Query organizations matching any selected category"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if not selected_categories:
        return []

    query = ("""SELECT Title, Description, Contact
             FROM orgs
             WHERE """)
    conditions = ["Category LIKE ?" for _ in selected_categories]
    params = [f'%{cat}%' for cat in selected_categories]

    cursor.execute(query + " OR ".join(conditions), params)
    organizations = cursor.fetchall()
    conn.close()

    random.shuffle(organizations)

    # Convert to list of dicts
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, org)) for org in organizations]


def all_organizations():
    """Query organizations matching any selected category"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = ("""SELECT Title, Description, Contact
             FROM orgs""")

    cursor.execute(query)
    organizations = cursor.fetchall()
    conn.close()

    random.shuffle(organizations)

    # Convert to list of dicts
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, org)) for org in organizations]


def generate_recommendations(form_data, organizations):
    """Use Gemini to generate personalized recommendations without PII"""
    # Sanitize inputs
    safe_profile = f"{form_data['first_name']}"  # First name only
    safe_answers = "\n".join(
        f"- {q}: {a}"
        for q, a in form_data['other_answers'].items()
        if 'name' not in q.lower() and 'email' not in q.lower()  # Filter sensitive questions
    )

    prompt = f"""Analyze this student's preferences and recommend 10 organizations for {safe_profile},
    ensuring balanced coverage across all selected categories:

    Available Organizations:
    {json.dumps(organizations, indent=2)}
    
    Student Profile:
    - Preferred Categories: {', '.join(form_data['categories'])}

    Filtered Q&A:
    {safe_answers}

    Recommendation Requirements:
    1. Prioritize category distribution - include organizations from each selected category proportionally
    2. Never suggest more than 3 organizations from the same category unless essential
    3. Consider all organizations equally regardless of their position in the list
    4. Highlight unique value propositions for similar organizations in the same category

    Format each recommendation as:
    Organization Name
    Match Reasoning: [concise 1-line explanation]
    Key Benefits: [2-3 comma-separated points]
    Contact: [direct contact info]

    Maintain strict formatting:
    - The ONLY output is the recommendations
    - No markdown or special characters
    - Separate recommendations with two newlines
    - Use only student's first name
    - Keep tone encouraging but professional
    """

    print(prompt)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text


def send_recommendation_email(gmail_service, form_data, recommendations):
    """Send personalized email"""
    body = f"""
Hi {form_data['first_name']},

Here are your organization recommendations:

{recommendations}

Best regards,
Student Support Team"""

    message = MIMEText(body)
    message['To'] = form_data['email']
    message['From'] = 'utdinstantmatch@gmail.com'
    message['Subject'] = f"{form_data['first_name']}, Your Organization Recommendations"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        return True
    except HttpError as error:
        print(f'Gmail API error: {error}')
        return False


def process_response(response, gmail_service, question_map):
    """Process a single form response"""
    form_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'categories': [],
        'other_answers': {}
    }

    answers = response.get('answers', {})
    for qid, answer in answers.items():
        # Get question text from mapping
        question_text = question_map.get(qid, f"Unknown Question (ID: {qid})")

        # Store both question and answer
        form_data['other_answers'][question_text] = answer.get(
            'textAnswers', {}
        ).get('answers', [{}])[0].get('value', '')

        # Extract first name (Question 1)
        if qid == '1fda0f0f':  # Replace with actual ID
            form_data['first_name'] = answer.get('textAnswers', {}).get('answers', [{}])[0].get('value', '')

        # Extract last name (Question 2)
        elif qid == '46b2c70a':  # Replace with actual ID
            form_data['last_name'] = answer.get('textAnswers', {}).get('answers', [{}])[0].get('value', '')

        # Email (Question 3)
        elif qid == '653da8f0':
            form_data['email'] = answer.get('textAnswers', {}).get('answers', [{}])[0].get('value', '')

        # Categories (Question 7)
        elif qid == '0aadaafa':
            form_data['categories'] = [
                item.get('value', '')
                for item in answer.get('textAnswers', {}).get('answers', [])
            ]

    # Validate required fields
    if not all([form_data['first_name'], form_data['last_name'], form_data['email']]):
        print("Missing required fields")
        print("First name", form_data['first_name'])
        print("Last name", form_data['last_name'])
        print("Email", form_data['email'])
        return False

    # Query database
    # organizations = query_organizations(form_data['categories'])
    organizations = all_organizations()
    if not organizations:
        print("No organizations found")
        return False

    # Generate recommendations
    recommendations = generate_recommendations(form_data, organizations)

    # Send email
    return send_recommendation_email(gmail_service, form_data, recommendations)
