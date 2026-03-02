import os
import json
import requests
import sys

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["GITHUB_REPOSITORY"]
GH_TOKEN = os.environ["GH_TOKEN"]

package_path = "force-app-delta/package/package.xml"
destructive_path = "force-app-delta/destructiveChanges/destructiveChanges.xml"

def read_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "None"

package_xml = read_file(package_path)
destructive_xml = read_file(destructive_path)

prompt = f"""
You are a Salesforce DevOps risk analyzer.

Analyze the following delta changes and provide:

1. Risk Level (Low / Medium / High)
2. Why
3. Recommended reviewer focus areas

Package.xml:
{package_xml}

DestructiveChanges.xml:
{destructive_xml}
"""

# ===============================
# Call Gemini API
# ===============================

response = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
    headers={"Content-Type": "application/json"},
    json={
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
)

if response.status_code != 200:
    print("Gemini HTTP Error:", response.status_code)
    print(response.text)
    sys.exit(1)

result = response.json()

if "candidates" not in result:
    print("Unexpected Gemini response:")
    print(json.dumps(result, indent=2))
    sys.exit(1)

ai_text = result["candidates"][0]["content"]["parts"][0]["text"]

comment_body = f"""
## 🤖 AI Deployment Risk Analysis (Gemini)

{ai_text}
"""

comment_response = requests.post(
    f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments",
    headers={
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    },
    json={"body": comment_body}
)

if comment_response.status_code not in [200, 201]:
    print("Failed to post PR comment:", comment_response.status_code)
    print(comment_response.text)
    sys.exit(1)

print("Gemini PR Risk Analysis comment posted successfully.")
