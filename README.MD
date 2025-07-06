# Gmail Email Scorer with LM Studio

A Python application that automatically scores your Gmail emails for importance and spam likelihood using a local LLM via LM Studio. Now with dedicated **Orders/Shipping** detection!

## Features

- 🏠 **Completely Local**: Uses LM Studio - your emails never leave your machine
- 🏷️ **Smart Labeling**: Automatically applies colored Gmail labels based on scores
- 📦 **Order Tracking**: Dedicated category for online orders, shipping, and deliveries
- 📊 **Learning System**: Tracks performance and allows for iterative improvement
- 🔄 **Long-running**: Can run continuously or on schedule
- 📈 **Analytics**: Built-in performance reporting
- 🔍 **Efficient Processing**: Skips already processed emails by default, with option to reprocess

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
    - Go to "APIs & Services" > "Library"
    - Search for "Gmail API" and enable it
4. Create credentials:
    - Go to "APIs & Services" > "Credentials"
    - Click "Create Credentials" > "OAuth 2.0 Client IDs"
    - Choose "Desktop application"
    - Download the JSON file and save as `credentials.json` in your project folder

### 3. Set Up LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a good instruct model (current only optimized for Qwen 3 28b):
    - **Llama 3.1 8B Instruct** - Best balance of speed/accuracy
    - **Mistral 7B Instruct** - Faster option
    - **Qwen 3 18B Instruct** - Great instruction following
3. Load the model in LM Studio
4. Start the local server (usually runs on `http://localhost:1234`)
5. Note the model name shown in LM Studio

### 4. Configure the Application

Edit the model name in `main.py` if needed:

```python
# In EmailScorer.__init__()
self.model_name = "your-actual-model-name"  # Update this
```

### 5. First Run

```bash
# Test with last 6 hours of emails
python main.py --hours 6

# Generate a performance report
python main.py --report

# Run continuously (checks every 15 minutes)
python main.py --continuous
```

## How It Works

### Scoring System

The system analyzes each email and provides:

- **Importance Score** (0-10): How important is this email?
    - 8-10: High importance (urgent work, important personal emails)
    - 6-7: Medium-high importance (orders, shipping, deliveries)
    - 5-7: Medium importance (regular work, notifications)
    - 0-4: Low importance (newsletters, promotions)

- **Spam Score** (0-10): Likelihood this is spam
    - 8-10: Very likely spam
    - 0-3: Legitimate email

- **Category**: work, personal, **orders**, newsletter, promotion, spam, notification, **travel**, **finance**, **calendar**, **software_license**

### Gmail Labels Applied

The system creates and applies these labels:

- 🔴 **EmailScorer/High-Importance** - Important emails (score 8+)
- 🟡 **EmailScorer/Medium-Importance** - Medium priority (score 5-7)
- ⚪ **EmailScorer/Low-Importance** - Low priority (score <5)
- 🔵 **EmailScorer/Orders-Shipping** - Online orders, deliveries, tracking
- 🟢 **EmailScorer/Travel** - Flight confirmations, hotel bookings, itineraries
- 🟤 **EmailScorer/Finance** - Banking, payments, invoices, bills, receipts
- 🟣 **EmailScorer/Calendar-Events** - Meeting invites, event reminders, RSVPs
- 🔷 **EmailScorer/Software-License** - Software activation keys, digital licenses
- 🚫 **EmailScorer/Likely-Spam** - Probable spam (spam score 7+)
- ❓ **EmailScorer/Needs-Review** - Low confidence scores

### Learning & Feedback

The system learns from your behavior:

- **Implicit feedback**: When you star, archive, or delete labeled emails
- **Performance tracking**: SQLite database tracks all scores and decisions
- **Iterative improvement**: Analyze patterns to refine scoring

### 📦 Orders & Shipping Detection

The system automatically detects and labels order-related emails with a dedicated blue label:

**What gets classified as "orders":**
- Amazon order confirmations & shipping updates
- Retail order confirmations (Best Buy, Target, etc.)
- Shipping notifications (UPS, FedEx, USPS, DHL)
- Delivery updates and tracking information
- Package pickup notifications
- Return/refund confirmations

**Why this matters:**
- Easy to track your online purchases
- Quick identification of delivery updates
- Separate from promotional emails from the same retailers
- Medium-high importance (6-7) - important but not urgent

**Example emails that get the Orders label:**
- "Your Amazon order has shipped"
- "UPS tracking update for package 1Z..."
- "Best Buy order confirmation #12345"
- "Your package will arrive today"

### ✈️ Travel Detection

The system identifies and labels travel-related emails with a dedicated green label:

**What gets classified as "travel":**
- Flight confirmations and boarding passes
- Hotel reservations and check-in information
- Rental car bookings and confirmations
- Travel itineraries and trip summaries
- Airline status updates and gate changes
- Tour and activity bookings
- Travel insurance documents

**Why this matters:**
- Keep all your travel documents in one place
- Quickly find important booking information
- High importance (7-9) - critical for travel planning
- Separate from marketing emails from the same travel companies

**Example emails that get the Travel label:**
- "Your flight confirmation for NYC to LAX"
- "Hotel reservation confirmation #12345"
- "Your boarding pass is ready"
- "Important information about your upcoming trip"

### 💰 Finance Detection

The system identifies and labels finance-related emails with a dedicated brown label:

**What gets classified as "finance":**
- Bank statements and account notifications
- Payment confirmations and receipts
- Credit card statements and alerts
- Invoice and bill notifications
- Tax documents and filing confirmations
- Investment updates and portfolio summaries
- Payroll and salary information

**Why this matters:**
- Keep track of your financial communications
- Quickly find important payment information
- High importance (7-9) - critical for financial management
- Easily distinguish from marketing emails from the same financial institutions

**Example emails that get the Finance label:**
- "Your monthly bank statement is ready"
- "Payment confirmation for your utility bill"
- "Important tax document available"
- "Transaction alert: $500 withdrawal"

### 📅 Calendar & Events Detection

The system identifies and labels calendar and event-related emails with a dedicated purple-blue label:

**What gets classified as "calendar":**
- Meeting invites and calendar appointments
- Event RSVPs and ticket confirmations
- Appointment reminders and scheduling updates
- Webinar and conference registrations
- Class and course schedules
- Deadline notifications and time-sensitive reminders

**Why this matters:**
- Never miss an important meeting or event
- Quickly identify schedule changes
- Medium-high importance (6-8) - important for planning
- Separate from other notifications and updates

**Example emails that get the Calendar-Events label:**
- "Meeting invitation: Project Review"
- "Your appointment is confirmed for tomorrow"
- "RSVP: Company Holiday Party"
- "Reminder: Webinar starts in 1 hour"

### 🔑 Software License Detection

The system identifies and labels software license-related emails with a dedicated teal label:

**What gets classified as "software_license":**
- Software activation keys and registration codes
- Digital license certificates and product keys
- Software purchase confirmations with license information
- License renewal notices and expiration warnings
- Software registration confirmations
- Digital product delivery emails with access credentials

**Why this matters:**
- Keep all your software licenses in one place
- Easily find activation keys when reinstalling software
- High importance (7-9) - critical for software access
- Prevent license loss that could require repurchase
- Quickly identify when licenses need renewal

**Example emails that get the Software-License label:**
- "Your Adobe Creative Cloud license key"
- "Microsoft Office 365 activation information"
- "Your software purchase: Download and license key"
- "License renewal reminder: Your subscription expires in 30 days"
- "Your game key for Steam: XXXX-XXXX-XXXX"

## Usage Examples

### Daily Processing
```bash
# Process last 24 hours - great for catching all your daily orders
python main.py --hours 24
```

### Weekly Review
```bash
# See how the system is performing, including orders breakdown
python main.py --report
```

### Continuous Monitoring
```bash
# Run in background, checking every 15 minutes for new orders & emails
python main.py --continuous
```

### Focus on Recent Orders
```bash
# Process last 3 hours - perfect for tracking morning deliveries
python main.py --hours 3
```

### Reprocessing Emails
```bash
# Process all emails in the time window, including already processed ones
python main.py --hours 24 --process-all
```

## Configuration Options

### LM Studio Settings

In `main.py`, you can adjust:

```python
class EmailScorer:
    def __init__(self, 
                 lm_studio_url="http://localhost:1234/v1",  # LM Studio URL
                 model_name="your-model-name"):              # Model name from LM Studio
```

### Scoring Prompt

Modify the prompt in `score_email()` method to adjust how emails are evaluated:

```python
prompt = f"""Your custom scoring instructions here...
```

### Label Thresholds

Adjust when labels are applied in `_apply_scoring_labels()`:

```python
if score.importance_score >= 8:  # Change threshold
    # Apply high importance label

# Orders get their own special label regardless of importance score
if score.category == 'orders':
    # Apply blue Orders-Shipping label
```

### Category Scoring

Modify scoring rules in the prompt or `config.py`:

```python
# Adjust importance ranges for different categories
- Work emails: importance 7-9
- Orders/shipping: importance 6-7  
- Personal emails: importance 6-8
- Notifications: importance 3-5
- Marketing: importance 1-3
```

### Processing Options

Configure email processing behavior in `config.py`:

```python
# Skip emails that have already been processed
SKIP_PROCESSED_EMAILS = True  # Set to False to always reprocess emails

# Hours to look back for emails
DEFAULT_HOURS_BACK = 1

# Maximum emails to process in one batch
MAX_EMAILS_PER_BATCH = 100
```

## Database Schema

The system stores all data locally in SQLite:

- **email_scores**: All email scores and metadata
- **processing_state**: Last processed timestamps

View your data:
```bash
sqlite3 email_scores.db
.tables
SELECT * FROM email_scores LIMIT 10;
```

## Troubleshooting

### "Model not found" error
- Check the model name in LM Studio matches your config
- Ensure LM Studio server is running on the correct port

### "Credentials not found"
- Make sure `credentials.json` is in the project directory
- Follow the Gmail API setup steps completely

### "Rate limit exceeded"
- The system includes delays to avoid Gmail API limits
- For large backlogs, process in smaller chunks

### Low scoring accuracy
- Check your prompt in `score_email()` method
- Consider using a larger/better model
- Review the performance report to identify patterns

## Advanced Usage

### Custom Label Actions

Once you're confident in the scoring, you can add automatic actions:

```python
def _apply_scoring_labels(self, email, score):
    # After Phase 1 observation period...
    if score.spam_score > 9.5 and score.confidence > 0.9:
        # Auto-move obvious spam
        self.gmail.move_to_spam(email['id'])

    if score.importance_score < 2 and 'newsletter' in email['sender']:
        # Auto-archive newsletters
        self.gmail.archive_email(email['id'])
```

### Performance Monitoring

Set up automatic reports:

```bash
# Add to crontab for daily reports
0 9 * * * python /path/to/main.py --report | mail -s "Email Scorer Report" you@email.com
```

### Integration with Other Tools

The SQLite database makes it easy to integrate with other tools:

```python
import sqlite3
conn = sqlite3.connect('email_scores.db')
# Export high-importance emails to your task manager
# Build custom dashboards
# Analyze email patterns
```

## Security & Privacy

- ✅ All processing happens locally on your machine
- ✅ No emails or data sent to external services
- ✅ Gmail API uses OAuth2 (revokable access)
- ✅ SQLite database stored locally
- ✅ LM Studio runs completely offline

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all dependencies are installed
3. Ensure Gmail API credentials are properly set up
4. Confirm LM Studio is running and accessible
5. Check the SQLite database for any stored errors

## Contributing

Feel free to modify and improve:

- Enhance the scoring prompts
- Add new label categories
- Implement additional feedback mechanisms
- Create custom reports and dashboards

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: Start with small batches (6-24 hours) to test the system before processing large email backlogs. The system is designed to be safe and reversible - it only adds labels initially.
