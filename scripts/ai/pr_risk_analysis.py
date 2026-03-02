import os
import json
import requests
import subprocess
import sys

OPENAI_KEY = os.environ["OPENAI_API_KEY"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["GITHUB_REPOSITORY"]
GH_TOKEN = os.environ["GH_TOKEN"]

# Read delta package.xml
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
# Call OpenAI
# ===============================
response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
)

# 🔒 HTTP Status Check
if response.status_code != 200:
    print("OpenAI HTTP Error:", response.status_code)
    print(response.text)
    sys.exit(1)

result = response.json()

# 🔒 KeyError Protection for 'choices'
if "choices" not in result:
    print("Unexpected OpenAI response structure:")
    print(json.dumps(result, indent=2))
    sys.exit(1)

if not result["choices"]:
    print("OpenAI returned empty choices array.")
    print(json.dumps(result, indent=2))
    sys.exit(1)

ai_text = result["choices"][0]["message"]["content"]

comment_body = f"""
## 🤖 AI Deployment Risk Analysis

{ai_text}
"""

# ===============================
# Post comment to PR
# ===============================
comment_response = requests.post(
    f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments",
    headers={
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    },
    json={"body": comment_body}
)

# Optional: Validate GitHub response
if comment_response.status_code not in [200, 201]:
    print("Failed to post PR comment:", comment_response.status_code)
    print(comment_response.text)
    sys.exit(1)

print("AI PR Risk Analysis comment posted successfully.")
