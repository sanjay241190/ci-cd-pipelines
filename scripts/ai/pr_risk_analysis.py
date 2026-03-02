import os
import requests
import sys


def get_env_variable(name):
    value = os.environ.get(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value


def main():
    # ==============================
    # Load Environment Variables
    # ==============================
    OPENAI_KEY = get_env_variable("OPENAI_API_KEY")
    PR_NUMBER = get_env_variable("PR_NUMBER")
    REPO = get_env_variable("GITHUB_REPOSITORY")
    GH_TOKEN = get_env_variable("GH_TOKEN")

    print(f"Running AI PR Risk Analysis for PR #{PR_NUMBER}")
    print(f"Repository: {REPO}")

    # ==============================
    # Get PR Details from GitHub
    # ==============================
    pr_url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    pr_response = requests.get(pr_url, headers=headers)

    if pr_response.status_code != 200:
        print("GitHub API Error:", pr_response.status_code)
        print(pr_response.text)
        raise Exception("Failed to fetch PR details from GitHub")

    pr_data = pr_response.json()

    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body", "")

    print("PR Title:", pr_title)

    # ==============================
    # Call OpenAI API
    # ==============================
    openai_headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    openai_payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a senior Salesforce DevOps architect performing pull request risk analysis."
            },
            {
                "role": "user",
                "content": f"""
Analyze this Salesforce Pull Request and provide:

1. Risk Level (Low / Medium / High)
2. Short reasoning (2-4 lines)
3. Any recommended review focus areas

PR Title:
{pr_title}

PR Description:
{pr_body}
"""
            }
        ],
        "temperature": 0.2
    }

    ai_response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=openai_headers,
        json=openai_payload
    )

    if ai_response.status_code != 200:
        print("OpenAI HTTP Error:", ai_response.status_code)
        print(ai_response.text)
        raise Exception("OpenAI API request failed")

    ai_result = ai_response.json()

    if "choices" not in ai_result:
        print("Unexpected OpenAI response:")
        print(ai_result)
        raise Exception("No 'choices' found in OpenAI response")

    ai_message = ai_result["choices"][0]["message"]["content"]

    print("AI Analysis generated successfully.")

    # ==============================
    # Post Comment on PR
    # ==============================
    comment_url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    comment_payload = {
        "body": f"""🤖 **AI PR Risk Analysis**

{ai_message}

---
_Automated analysis generated during CI validation._"""
    }

    comment_response = requests.post(
        comment_url,
        headers=headers,
        json=comment_payload
    )

    if comment_response.status_code not in [200, 201]:
        print("Failed to post PR comment:", comment_response.status_code)
        print(comment_response.text)
        raise Exception("Failed to post PR comment")

    print("AI PR comment posted successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ Script failed:", str(e))
        sys.exit(1)
