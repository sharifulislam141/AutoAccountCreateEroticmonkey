import requests
import cloudscraper
import random
import string
import time
import re
import json

MAIL_GW_BASE = "https://api.mail.gw"

def generate_random_identity():
    print("[1] Fetching temp mail domain...")
    domain_resp = requests.get(f"{MAIL_GW_BASE}/domains")
    domain = domain_resp.json()["hydra:member"][0]["domain"]

    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"{username}@{domain}"
    password = username
    print(f"[2] Creating temp mailbox for: {email}")

    register_payload = {"address": email, "password": password}
    reg_res = requests.post(f"{MAIL_GW_BASE}/accounts", json=register_payload)
    if reg_res.status_code != 201:
        raise Exception(f"Failed to register mailbox: {reg_res.text}")

    print("[3] Requesting JWT token...")
    token_resp = requests.post(f"{MAIL_GW_BASE}/token", json=register_payload)
    token = token_resp.json()["token"]

    return {
        "email": email,
        "username": username,
        "password": password,
        "token": token
    }

def signup_with_temp_email(identity):
    print(f"[4] Registering on EroticMonkey.ch with {identity['email']}...")
    url = "https://www.eroticmonkey.ch/signup"
    scraper = cloudscraper.create_scraper()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.eroticmonkey.ch/"
    }

    payload = {
        "pay": "NO",
        "duration": "1month",
        "user_type": "1",
        "email": identity["email"],
        "username": identity["username"],
        "password": identity["password"],
        "defaultReal": "JX6F0C",
        "defaultRealHash": "-1160512426",
        "agree": "yes",
        "duplicate_email": "",
        "duplicate_username": ""
    }

    response = scraper.post(url, headers=headers, data=payload)
    if response.status_code == 200 and "thank you" in response.text.lower():
        print(f"[✓] Signup submitted for {identity['username']}")
        return scraper
    else:
        print(f"[X] Signup failed. Status: {response.status_code}")
        return None

def poll_verification_link(identity, max_wait=60):
    headers = {"Authorization": f"Bearer {identity['token']}"}
    print("[5] Polling for verification email...")
    for attempt in range(int(max_wait / 4)):
        print(f"    → Checking inbox... (try {attempt + 1})")
        inbox = requests.get(f"{MAIL_GW_BASE}/messages", headers=headers).json()
        if inbox["hydra:member"]:
            message_id = inbox["hydra:member"][0]["id"]
            print(f"    ✓ Email received! Fetching message ID: {message_id}")
            message = requests.get(f"{MAIL_GW_BASE}/messages/{message_id}", headers=headers).json()
            content = message["text"]
            match = re.search(r"https://www\.eroticmonkey\.ch/users-confirm-account-[a-z0-9]+", content)
            if match:
                print(f"    ✓ Found verification link!")
                return match.group(0)
        time.sleep(4)
    print("[X] Timed out waiting for verification email.")
    return None

def confirm_account(url, scraper):
    print(f"[6] Confirming account with: {url}")
    resp = scraper.get(url)
    if resp.status_code == 200:
        print("[✓] Account confirmed!")
        return True
    else:
        print(f"[X] Confirmation failed. Status: {resp.status_code}")
        return False

def save_account(identity, json_file="valid_accounts.txt", username_file="usernames.txt"):
    print(f"[💾] Saving to files: {identity['username']}")
    with open(json_file, "a") as f:
        f.write(json.dumps(identity) + "\n")
    with open(username_file, "a") as f:
        f.write(identity["username"] + "\n")

def generate_accounts_forever():
    count = 1
    while True:
        print(f"\n======= Account {count} =======")
        try:
            identity = generate_random_identity()
            scraper = signup_with_temp_email(identity)
            if not scraper:
                continue
            verify_url = poll_verification_link(identity)
            if not verify_url:
                continue
            if confirm_account(verify_url, scraper):
                save_account(identity)
        except Exception as e:
            print(f"[X] Exception occurred: {e}")
        count += 1
        print(f"[→] Waiting 5 seconds before next account...\n")
        time.sleep(5)

# Run it
generate_accounts_forever()
