# config.py - Configuration for Gmail Email Scorer

# LM Studio Configuration
LM_STUDIO_URL = "http://localhost:1234/v1"
MODEL_NAME = "qwen3-32b"  # Update this to match your LM Studio model name

# Gmail API Configuration
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# Database Configuration
DATABASE_PATH = "email_scores.db"

# Processing Configuration
DEFAULT_HOURS_BACK = 1
CONTINUOUS_CHECK_INTERVAL = 900  # 15 minutes in seconds
MAX_EMAILS_PER_BATCH = 100
SKIP_PROCESSED_EMAILS = True  # Skip emails that have already been processed

# Scoring Thresholds (adjust these based on your preferences)
IMPORTANCE_THRESHOLDS = {
    'high': 8.0,      # Score >= 8.0 for high importance
    'medium': 5.0,    # Score >= 5.0 for medium importance
    # Everything else is low importance
}

SPAM_THRESHOLD = 7.0          # Score >= 7.0 for likely spam
CONFIDENCE_THRESHOLD = 0.6    # Confidence < 0.6 needs review

# Label Configuration
LABELS = {
    'high_importance': 'EmailScorer/High-Importance',
    'medium_importance': 'EmailScorer/Medium-Importance',
    'low_importance': 'EmailScorer/Low-Importance',
    'orders_shipping': 'EmailScorer/Orders-Shipping',
    'travel': 'EmailScorer/Travel',
    'finance': 'EmailScorer/Finance',
    'calendar_events': 'EmailScorer/Calendar-Events',
    'software_license': 'EmailScorer/Software-License',
    'likely_spam': 'EmailScorer/Likely-Spam',
    'needs_review': 'EmailScorer/Needs-Review',
    'training_correct': 'EmailScorer/Training-Data/Correct',
    'training_incorrect': 'EmailScorer/Training-Data/Incorrect'
}

# Label Colors (Gmail allowed hex colors only)
LABEL_COLORS = {
    'EmailScorer/High-Importance': '#cc3a21',    # Red
    'EmailScorer/Medium-Importance': '#f2c960',  # Yellow
    'EmailScorer/Low-Importance': '#cccccc',     # Gray
    'EmailScorer/Orders-Shipping': '#4a86e8',    # Blue
    'EmailScorer/Travel': '#16a766',             # Green
    'EmailScorer/Finance': '#ffad47',            # Brown
    'EmailScorer/Calendar-Events': '#8e63ce',    # Purple-Blue
    'EmailScorer/Software-License': '#e66550',   # Teal
    'EmailScorer/Likely-Spam': '#ffad47',        # Orange
    'EmailScorer/Needs-Review': '#8e63ce',       # Purple
    'EmailScorer/Training-Data/Correct': '#16a766',   # Green
    'EmailScorer/Training-Data/Incorrect': '#e66550', # Red-Orange
}

# Email Processing Rules
SKIP_SENDERS = [
    # Add email addresses or domains to skip processing
    # 'noreply@example.com',
    # '@socialnetwork.com',
]

PRIORITY_SENDERS = [
    # Add important senders that should always score high
    # 'boss@company.com',
    # '@important-client.com',
]

# Prompt Template - Customize this to change how emails are scored
SCORING_PROMPT_TEMPLATE = """Classify this email and provide scores. Be consistent and practical.

SENDER: {sender}
SUBJECT: {subject}
DATE: {email_date}
CONTENT: {body_preview}

Provide scores as JSON:
{{
    "importance_score": 0-10,
    "spam_score": 0-10,
    "category": "work|personal|orders|newsletter|promotion|spam|notification|travel|finance|calendar|software_license",
    "reasoning": "brief explanation",
    "confidence": 0.0-1.0
}}

Scoring Guidelines:
- Work emails from colleagues/clients = 7-9 importance
- Orders/shipping/deliveries = 6-7 importance (Amazon, retailers, UPS/FedEx/USPS, tracking)
- Travel emails (flights, hotels, itineraries) = 7-9 importance
- Finance emails (banking, payments, invoices) = 7-9 importance
- Calendar/Events (meetings, invites, RSVPs) = 6-8 importance
- Software License emails (activation keys, digital licenses) = 7-9 importance
- Personal emails from friends/family = 6-8 importance
- Automated notifications = 3-5 importance
- Newsletters/promotions = 1-3 importance
- Suspicious/unknown senders = higher spam score
- Professional tone + known sender = higher confidence

Category descriptions:
- Orders: Amazon, retailers, shipping companies, order confirmations, delivery updates, tracking info
- Travel: Flight confirmations, hotel bookings, rental cars, travel itineraries, boarding passes, trip updates
- Finance: Bank statements, payment confirmations, invoices, bills, receipts, tax documents, financial alerts
- Calendar: Meeting invites, event reminders, RSVPs, appointment confirmations, schedule updates
- Software License: Software activation keys, digital license certificates, product keys, registration confirmations, license renewal notices

JSON:"""

# Advanced Options
ENABLE_HTML_PARSING = True
MAX_EMAIL_BODY_LENGTH = 1500  # Truncate long emails
PROCESSING_DELAY = 0.1        # Seconds between emails to avoid rate limits
LOG_LEVEL = "INFO"            # DEBUG, INFO, WARNING, ERROR

# Auto-action Configuration (WARNING: Use carefully!)
ENABLE_AUTO_ACTIONS = False   # Set to True to enable automatic actions

AUTO_ACTION_RULES = {
    # Only enable these after validating system accuracy!
    'auto_spam': {
        'enabled': False,
        'min_spam_score': 9.5,
        'min_confidence': 0.9,
        'action': 'move_to_spam'  # or 'add_label'
    },
    'auto_archive_newsletters': {
        'enabled': False,
        'max_importance_score': 2.0,
        'required_category': 'newsletter',
        'min_confidence': 0.8,
        'action': 'archive'
    },
    'auto_star_important': {
        'enabled': False,
        'min_importance_score': 9.0,
        'min_confidence': 0.9,
        'action': 'add_star'
    }
}

# Reporting Configuration
REPORT_DAYS_BACK = 7
INCLUDE_SAMPLE_EMAILS = True
