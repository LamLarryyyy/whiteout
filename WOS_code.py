import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from lxml import html

# Configuration
URL = "https://wosgiftcodes.com/"
CHECK_INTERVAL = 3600  # Check every hour (in seconds)
HISTORY_FILE = "wos_codes.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Email settings
SEND_EMAIL = True  # Set to True to enable email notifications
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "lamlarryyyy@gmail.com"
SMTP_USERNAME = "lamlarryyyy@gmail.com"
SMTP_PASSWORD = "krsl ilvy hsir xjqg"

EMAIL_RECIPIENTS = [
    "lamlarryyyy@gmail.com",
    "kinfaiwong@icloud.com",
    "samuelgyc@gmail.com"
]

def get_page_content():
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_active_codes(html_content):
    tree = html.fromstring(html_content)
    active_codes_header = tree.xpath('//div[contains(@class, "card-header")]//h5[contains(text(), "Active Codes")]')
    if not active_codes_header:
        print("Could not find Active Codes header")
        return set()

    code_table = active_codes_header[0].xpath('../../div[contains(@class, "card-body")]//table')
    if not code_table:
        print("Could not find codes table")
        return set()

    code_cells = code_table[0].xpath('.//tbody/tr/td[1]')
    return {code.text.strip() for code in code_cells if code.text and code.text.strip()}

def load_tracked_codes():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_tracked_codes(codes):
    with open(HISTORY_FILE, 'w') as f:
        f.write('\n'.join(codes))

def send_new_codes_notification(new_codes):
    if not SEND_EMAIL or not new_codes:
        return

    subject = f"🎁 {len(new_codes)} New Whiteout Survival Codes!"
    body = f"""
    <html>
      <body>
        <h2>New Whiteout Survival Codes Available!</h2>
        <p><strong>Source:</strong> <a href="{URL}">{URL}</a></p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h3>New Codes:</h3>
        <ul>
          {''.join(f'<li><strong>{code}</strong></li>' for code in new_codes)}
        </ul>

        <p>Redeem these in-game as soon as possible!</p>
      </body>
    </html>
    """

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = ", ".join(EMAIL_RECIPIENTS)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_RECIPIENTS, msg.as_string())
        print(f"Notification sent to {len(EMAIL_RECIPIENTS)} recipients")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    print(f"Starting Whiteout Survival Code tracker for {URL}")
    print(f"Checking for updates every {CHECK_INTERVAL//3600} hours")

    while True:
        print(f"\nChecking at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        content = get_page_content()
        if content:
            current_codes = extract_active_codes(content)
            tracked_codes = load_tracked_codes()

            new_codes = current_codes - tracked_codes
            expired_codes = tracked_codes - current_codes

            if new_codes:
                print(f"New codes detected: {', '.join(new_codes)}")
                send_new_codes_notification(new_codes)

            if expired_codes:
                print(f"Expired codes removed silently: {', '.join(expired_codes)}")

            # Always update the file to reflect current state
            if new_codes or expired_codes:
                save_tracked_codes(current_codes)
            else:
                print("No changes detected")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
