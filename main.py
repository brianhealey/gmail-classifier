# main.py - Gmail Email Scorer with LM Studio
import os
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

import openai
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import email
from email.mime.text import MIMEText
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EmailScore:
    importance_score: float
    spam_score: float
    category: str
    reasoning: str
    confidence: float = 0.5

class EmailScorer:
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1", model_name: str = "qwen3-32b"):
        self.lm_studio_url = lm_studio_url
        self.model_name = model_name
        self.client = openai.OpenAI(
            base_url=lm_studio_url,
            api_key="lm-studio"  # LM Studio accepts any key
        )

    def score_email(self, sender: str, subject: str, body: str, email_date: str) -> EmailScore:
        """Score an email using the local LM Studio model"""

        # Truncate body to avoid context limits
        body_preview = body[:1500] if body else ""

        prompt = f"""Classify this email. Output JSON only, no thinking or explanation.

SENDER: {sender}
SUBJECT: {subject}
CONTENT: {body_preview}

Rules:
- Work emails: importance 7-9
- Orders/shipping/deliveries: importance 6-7
- Personal emails: importance 6-8
- Notifications: importance 3-5
- Marketing/newsletters: importance 1-3
- Unknown/suspicious senders: higher spam score

Orders category includes: Amazon, retailers, shipping companies (UPS/FedEx/USPS), order confirmations, delivery updates, tracking info.

Output this exact JSON format:
{{"importance_score": [0-10], "spam_score": [0-10], "category": "[work/personal/orders/newsletter/promotion/spam/notification]", "reasoning": "[brief]", "confidence": [0.0-1.0]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a precise email classifier. Respond with JSON only, no thinking or explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()

            # Debug: print what we actually received
            logger.info(f"Raw response length: {len(result_text)} chars")
            logger.info(f"Raw response preview: '{result_text[:300]}...'")

            # Handle empty responses
            if not result_text:
                logger.warning("Empty response from Qwen model")
                raise ValueError("Empty response from model")

            # Extract JSON from response - handle Qwen's <think> tags
            json_text = result_text

            # Remove Qwen thinking tags if present
            if '<think>' in json_text and '</think>' in json_text:
                # Get content after </think>
                think_end = json_text.find('</think>') + 8
                json_text = json_text[think_end:].strip()
                logger.info(f"Removed thinking tags, remaining: '{json_text}'")

            # Remove markdown code blocks
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.rfind('```')
                if end > start:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text:
                start = json_text.find('```') + 3
                end = json_text.rfind('```')
                if end > start:
                    json_text = json_text[start:end].strip()

            # Find JSON object in the text
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, json_text, re.DOTALL)

            if json_matches:
                json_text = json_matches[0]
                logger.info(f"Found JSON match: '{json_text}'")
            else:
                logger.warning(f"No JSON found in response: '{json_text}'")
                raise ValueError("No JSON found in model response")

            # Clean up the JSON text
            json_text = json_text.strip()

            logger.info(f"Final JSON to parse: '{json_text}'")

            # Parse the JSON
            result = json.loads(json_text)

            return EmailScore(
                importance_score=float(result.get('importance_score', 5)),
                spam_score=float(result.get('spam_score', 0)),
                category=result.get('category', 'unknown'),
                reasoning=result.get('reasoning', 'No reasoning provided'),
                confidence=float(result.get('confidence', 0.5))
            )

        except Exception as e:
            logger.error(f"Error scoring email: {e}")
            # Return default safe scores on error
            return EmailScore(
                importance_score=5.0,
                spam_score=0.0,
                category='unknown',
                reasoning=f'Error during scoring: {str(e)}',
                confidence=0.1
            )

class GmailManager:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self, credentials_file: str = 'credentials.json'):
        self.credentials_file = credentials_file
        self.service = None
        self.labels = {}
        self._authenticate()
        self._setup_labels()

    def _authenticate(self):
        """Authenticate with Gmail API"""
        creds = None

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Please download OAuth2 credentials from Google Cloud Console "
                        f"and save as '{self.credentials_file}'"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully authenticated with Gmail API")

    def _setup_labels(self):
        """Create scoring labels if they don't exist"""
        # Gmail only allows specific predefined hex colors
        required_labels = {
            'EmailScorer/High-Importance': '#cc3a21',    # Red
            'EmailScorer/Medium-Importance': '#f2c960',  # Yellow
            'EmailScorer/Low-Importance': '#cccccc',     # Gray
            'EmailScorer/Orders-Shipping': '#4a86e8',    # Blue
            'EmailScorer/Likely-Spam': '#ffad47',        # Orange
            'EmailScorer/Needs-Review': '#8e63ce',       # Purple
            'EmailScorer/Training-Data/Correct': '#16a766',   # Green
            'EmailScorer/Training-Data/Incorrect': '#e66550', # Red-Orange
        }

        # Get existing labels
        results = self.service.users().labels().list(userId='me').execute()
        existing_labels = {label['name']: label['id'] for label in results.get('labels', [])}

        # Create missing labels
        for label_name, color in required_labels.items():
            if label_name not in existing_labels:
                label_body = {
                    'name': label_name,
                    'messageListVisibility': 'show',
                    'labelListVisibility': 'labelShow',
                    'color': {
                        'textColor': '#000000',  # Black text
                        'backgroundColor': color
                    }
                }

                try:
                    result = self.service.users().labels().create(
                        userId='me', body=label_body).execute()
                    existing_labels[label_name] = result['id']
                    logger.info(f"Created label: {label_name}")
                except Exception as e:
                    logger.error(f"Error creating label {label_name}: {e}")

        self.labels = existing_labels

    def get_recent_emails(self, hours_back: int = 24, max_results: int = 1000) -> List[Dict]:
        """Get recent emails from Gmail"""

        # Calculate date filter
        since_date = datetime.now() - timedelta(hours=hours_back)
        date_str = since_date.strftime('%Y/%m/%d')

        query = f'after:{date_str} -in:chats'

        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])

            emails = []
            for msg in messages:
                try:
                    email_data = self._get_email_details(msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {msg['id']}: {e}")
                    continue

            logger.info(f"Retrieved {len(emails)} emails from last {hours_back} hours")
            return emails

        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed email information"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message_id, format='full').execute()

            headers = msg['payload'].get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}

            # Extract body
            body = self._extract_body(msg['payload'])

            # Clean body text
            body_text = self._clean_text(body) if body else ""

            return {
                'id': message_id,
                'sender': header_dict.get('from', ''),
                'subject': header_dict.get('subject', ''),
                'date': header_dict.get('date', ''),
                'body': body_text,
                'labels': msg.get('labelIds', []),
                'thread_id': msg.get('threadId', ''),
                'snippet': msg.get('snippet', '')
            }

        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None

    def _extract_body(self, payload) -> str:
        """Extract email body from payload"""
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data and not body:  # Use HTML if no plain text
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        body = self._strip_html(html_body)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body

    def _strip_html(self, html_text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common email artifacts
        text = re.sub(r'On .* wrote:', '', text)
        text = re.sub(r'From: .*\n', '', text)
        return text.strip()

    def apply_label(self, email_id: str, label_name: str):
        """Apply a label to an email"""
        if label_name not in self.labels:
            logger.error(f"Label {label_name} not found")
            return False

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [self.labels[label_name]]}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error applying label {label_name} to {email_id}: {e}")
            return False

class EmailDatabase:
    def __init__(self, db_path: str = 'email_scores.db'):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT UNIQUE,
                sender TEXT,
                subject TEXT,
                date_processed TIMESTAMP,
                importance_score REAL,
                spam_score REAL,
                category TEXT,
                reasoning TEXT,
                confidence REAL,
                model_version TEXT,
                labels_applied TEXT,
                user_feedback TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized")

    def save_score(self, email: Dict, score: EmailScore, labels_applied: List[str]):
        """Save email score to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO email_scores
            (email_id, sender, subject, date_processed, importance_score,
             spam_score, category, reasoning, confidence, model_version, labels_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email['id'],
            email['sender'],
            email['subject'],
            datetime.now(),
            score.importance_score,
            score.spam_score,
            score.category,
            score.reasoning,
            score.confidence,
            'v1.0',
            ','.join(labels_applied)
        ))

        conn.commit()
        conn.close()

    def is_email_processed(self, email_id: str) -> bool:
        """Check if an email has already been processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM email_scores WHERE email_id = ?', (email_id,))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    def get_last_processed_time(self) -> Optional[datetime]:
        """Get timestamp of last processed email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM processing_state WHERE key = "last_processed"')
        result = cursor.fetchone()
        conn.close()

        if result:
            return datetime.fromisoformat(result[0])
        return None

    def update_last_processed_time(self, timestamp: datetime):
        """Update last processed timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO processing_state (key, value)
            VALUES ("last_processed", ?)
        ''', (timestamp.isoformat(),))

        conn.commit()
        conn.close()

    def get_performance_stats(self, days_back: int = 7) -> Dict:
        """Get performance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_date = datetime.now() - timedelta(days=days_back)

        cursor.execute('''
            SELECT
                COUNT(*) as total_emails,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN importance_score >= 7 THEN 1 END) as high_importance,
                COUNT(CASE WHEN spam_score >= 7 THEN 1 END) as likely_spam,
                category,
                COUNT(*) as category_count
            FROM email_scores
            WHERE date_processed >= ?
            GROUP BY category
        ''', (since_date,))

        results = cursor.fetchall()
        conn.close()

        return {
            'total_processed': sum(r[5] for r in results),
            'avg_confidence': sum(r[1] * r[5] for r in results) / sum(r[5] for r in results) if results else 0,
            'high_importance_count': sum(r[2] for r in results),
            'spam_count': sum(r[3] for r in results),
            'categories': {r[4]: r[5] for r in results}
        }

class EmailScoringSystem:
    def __init__(self):
        from config import SKIP_PROCESSED_EMAILS
        self.scorer = EmailScorer()
        self.gmail = GmailManager()
        self.db = EmailDatabase()
        self.skip_processed_emails = SKIP_PROCESSED_EMAILS

    def process_emails(self, hours_back: int = 1):
        """Main processing function"""
        logger.info(f"Starting email processing for last {hours_back} hours")

        # Get recent emails
        emails = self.gmail.get_recent_emails(hours_back=hours_back)

        if not emails:
            logger.info("No new emails to process")
            return

        processed_count = 0
        skipped_count = 0

        for email in emails:
            try:
                # Check if email has already been processed
                if self.skip_processed_emails and self.db.is_email_processed(email['id']):
                    logger.info(f"Skipping already processed email: {email['subject'][:50]}...")
                    skipped_count += 1
                    continue

                # Score the email
                score = self.scorer.score_email(
                    sender=email['sender'],
                    subject=email['subject'],
                    body=email['body'],
                    email_date=email['date']
                )

                # Determine and apply labels
                labels_applied = self._apply_scoring_labels(email, score)

                # Save to database
                self.db.save_score(email, score, labels_applied)

                processed_count += 1

                logger.info(f"Processed: {email['subject'][:50]}... | "
                           f"Importance: {score.importance_score:.1f} | "
                           f"Spam: {score.spam_score:.1f} | "
                           f"Category: {score.category}")

                # Small delay to avoid rate limits
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing email {email['id']}: {e}")
                continue

        self.db.update_last_processed_time(datetime.now())
        logger.info(f"Successfully processed {processed_count} emails, skipped {skipped_count} already processed emails")

    def _apply_scoring_labels(self, email: Dict, score: EmailScore) -> List[str]:
        """Apply appropriate labels based on score"""
        labels_applied = []

        # Special category labels first
        if score.category == 'orders':
            if self.gmail.apply_label(email['id'], 'EmailScorer/Orders-Shipping'):
                labels_applied.append('EmailScorer/Orders-Shipping')

        # Importance labels
        if score.importance_score >= 8:
            if self.gmail.apply_label(email['id'], 'EmailScorer/High-Importance'):
                labels_applied.append('EmailScorer/High-Importance')
        elif score.importance_score >= 5:
            if self.gmail.apply_label(email['id'], 'EmailScorer/Medium-Importance'):
                labels_applied.append('EmailScorer/Medium-Importance')
        else:
            if self.gmail.apply_label(email['id'], 'EmailScorer/Low-Importance'):
                labels_applied.append('EmailScorer/Low-Importance')

        # Spam labels
        if score.spam_score >= 7:
            if self.gmail.apply_label(email['id'], 'EmailScorer/Likely-Spam'):
                labels_applied.append('EmailScorer/Likely-Spam')

        # Low confidence needs review
        if score.confidence < 0.6:
            if self.gmail.apply_label(email['id'], 'EmailScorer/Needs-Review'):
                labels_applied.append('EmailScorer/Needs-Review')

        return labels_applied

    def generate_report(self) -> str:
        """Generate performance report"""
        stats = self.db.get_performance_stats()

        report = f"""
Email Scoring System - Weekly Report
=====================================

Total Emails Processed: {stats['total_processed']}
Average Confidence: {stats['avg_confidence']:.2f}
High Importance Emails: {stats['high_importance_count']}
Likely Spam: {stats['spam_count']}

Category Breakdown:
{'-' * 20}
"""

        for category, count in stats['categories'].items():
            percentage = (count / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0
            report += f"{category:15s}: {count:3d} ({percentage:5.1f}%)\n"

        return report

def main():
    """Main entry point"""
    import argparse
    from config import SKIP_PROCESSED_EMAILS

    parser = argparse.ArgumentParser(description='Gmail Email Scoring System')
    parser.add_argument('--hours', type=int, default=1,
                       help='Hours back to process emails (default: 1)')
    parser.add_argument('--report', action='store_true',
                       help='Generate performance report')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously (check every 15 minutes)')
    parser.add_argument('--process-all', action='store_true',
                       help='Process all emails, including already processed ones')

    args = parser.parse_args()

    system = EmailScoringSystem()

    # Override skip_processed_emails if --process-all is specified
    if args.process_all:
        system.skip_processed_emails = False
        logger.info("Processing all emails, including already processed ones")

    if args.report:
        print(system.generate_report())
        return

    if args.continuous:
        logger.info("Starting continuous monitoring mode...")
        while True:
            try:
                system.process_emails(hours_back=1)
                logger.info("Sleeping for 15 minutes...")
                time.sleep(900)  # 15 minutes
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        system.process_emails(hours_back=args.hours)

if __name__ == "__main__":
    main()
