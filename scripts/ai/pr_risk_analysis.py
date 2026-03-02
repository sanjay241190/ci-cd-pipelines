import os
import json
import requests
import subprocess

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

ai_text = response.json()["choices"][0]["message"]["content"]

comment_body = f"""
##  AI Deployment Risk Analysis

{ai_text}
"""

# Post comment to PR
requests.post(
    f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments",
    headers={
        "Authorization": f"token {GH_TOKEN}"
    },
    json={"body": comment_body}
)