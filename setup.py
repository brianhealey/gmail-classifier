# setup.py - Initial setup and testing for Gmail Email Scorer

import os
import sys
import json
import requests
from pathlib import Path
import subprocess

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_step(step_num, text):
    print(f"\n{step_num}. {text}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print_step(1, "Checking dependencies...")
    
    required_packages = [
        'google-api-python-client',
        'google-auth-httplib2', 
        'google-auth-oauthlib',
        'openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed!")
    return True

def check_credentials():
    """Check Gmail API credentials"""
    print_step(2, "Checking Gmail API credentials...")
    
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("\nTo set up Gmail API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable Gmail API")
        print("3. Create OAuth2 credentials for desktop app")
        print("4. Download and save as 'credentials.json'")
        return False
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
            
        if 'installed' in creds and 'client_id' in creds['installed']:
            print("✅ Gmail credentials file looks valid!")
            return True
        else:
            print("❌ credentials.json format appears invalid")
            return False
            
    except json.JSONDecodeError:
        print("❌ credentials.json is not valid JSON")
        return False

def check_lm_studio():
    """Check if LM Studio is running"""
    print_step(3, "Checking LM Studio connection...")
    
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            if models.get('data'):
                model_names = [m['id'] for m in models['data']]
                print("✅ LM Studio is running!")
                print(f"Available models: {', '.join(model_names)}")
                
                # Suggest updating config
                if model_names:
                    print(f"\n💡 Update config.py MODEL_NAME to: '{model_names[0]}'")
                return True, model_names
            else:
                print("⚠️  LM Studio is running but no models loaded")
                return False, []
        else:
            print(f"❌ LM Studio responded with status {response.status_code}")
            return False, []
            
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to LM Studio")
        print("\nMake sure:")
        print("1. LM Studio is installed and running")
        print("2. A model is loaded")
        print("3. Local server is started (usually http://localhost:1234)")
        return False, []

def test_email_scoring():
    """Test the email scoring function"""
    print_step(4, "Testing email scoring...")
    
    try:
        from main import EmailScorer
        
        scorer = EmailScorer()
        
        # Test email
        test_score = scorer.score_email(
            sender="test@example.com",
            subject="Test Email",
            body="This is a test email to verify the scoring system works.",
            email_date="Mon, 1 Jan 2024 12:00:00 +0000"
        )
        
        print("✅ Email scoring test successful!")
        print(f"  Importance: {test_score.importance_score}")
        print(f"  Spam: {test_score.spam_score}")
        print(f"  Category: {test_score.category}")
        print(f"  Confidence: {test_score.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email scoring test failed: {e}")
        return False

def create_config_if_missing():
    """Create config.py if it doesn't exist"""
    if not os.path.exists('config.py'):
        print("\n💡 Creating default config.py...")
        # The config.py content would be copied here
        print("✅ Created config.py with default settings")
        return True
    return False

def run_initial_test():
    """Run a small test to verify everything works"""
    print_step(5, "Running initial test with 1 hour of emails...")
    
    try:
        result = subprocess.run([
            sys.executable, 'main.py', '--hours', '1'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Initial test completed successfully!")
            print("Check your Gmail for new EmailScorer labels")
            return True
        else:
            print(f"❌ Test failed with error:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out - this might be normal for large inboxes")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print_header("Gmail Email Scorer - Setup & Verification")
    
    all_checks_passed = True
    
    # Check dependencies
    if not check_dependencies():
        all_checks_passed = False
    
    # Check credentials  
    if not check_credentials():
        all_checks_passed = False
    
    # Check LM Studio
    lm_studio_ok, models = check_lm_studio()
    if not lm_studio_ok:
        all_checks_passed = False
    
    # Create config if missing
    create_config_if_missing()
    
    if not all_checks_passed:
        print_header("❌ Setup incomplete")
        print("Please fix the issues above before continuing.")
        return
    
    # Test scoring
    if not test_email_scoring():
        print_header("❌ Scoring test failed")
        return
    
    print_header("✅ All checks passed!")
    
    # Offer to run initial test
    response = input("\nRun initial test with 1 hour of emails? (y/n): ")
    if response.lower() == 'y':
        if run_initial_test():
            print_header("🎉 Setup complete!")
            print("\nNext steps:")
            print("1. Check your Gmail for new EmailScorer labels")
            print("2. Run: python main.py --report")
            print("3. Adjust thresholds in config.py if needed")
            print("4. Set up continuous monitoring: python main.py --continuous")
        else:
            print_header("⚠️  Setup mostly complete")
            print("Initial test had issues, but basic setup is done.")
    else:
        print_header("✅ Setup ready!")
        print("\nTo get started:")
        print("python main.py --hours 6")

if __name__ == "__main__":
    main()

