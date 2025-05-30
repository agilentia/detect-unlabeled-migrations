import json
import os
import subprocess
import sys

import requests
import slack

# Environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_BRANCH = os.getenv("BASE_BRANCH")
WARNING_LABEL = os.getenv("WARNING_LABEL")
REQUIRED_LABELS = os.getenv("REQUIRED_LABELS")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

# todo: implement logging
# todo: make the action private
# todo: complete the README.md with the optional parameters


def _get_github_endpoint(repo: str, pr_number: int) -> str:
    return f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"


def load_pr_info(event_path: str) -> tuple[int, str]:
    with open(event_path, "r") as f:
        event = json.load(f)
    pr_number = int(event["pull_request"]["number"])
    repo = event["repository"]["full_name"]
    return pr_number, repo


def pr_has_label(repo: str, pr_number: int, required_labels: set[str]) -> bool:
    url = _get_github_endpoint(repo, pr_number)
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    pr_labels = set([lbl["name"] for lbl in response.json()])
    return bool(required_labels.intersection(pr_labels))


def send_slack_notification(pr_number: int, repo: str, required_labels: set[str]):
    pr_url = f"https://github.com/{repo}/pull/{pr_number}"
    line = "=" * 82
    msg = (
        f"{line}\n"
        f":alert-light: PR <{pr_url}|#{pr_number}> in {repo} is missing "
        f"the required label  `{' or '.join(required_labels)}`!"
        f"\n{line}"
    )
    slack.post_message(channel=SLACK_CHANNEL_ID, message=msg)


def check_for_migration_files() -> list[str]:
    subprocess.run(["git", "fetch", "origin", BASE_BRANCH], check=True)
    result = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{BASE_BRANCH}...HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    files = result.stdout.strip().split("\n")
    migration_files = [f for f in files if "/migrations/" in f and f.endswith(".py")]
    return migration_files


def add_label(repo: str, pr_number: int, warning_label: str):
    url = _get_github_endpoint(repo, pr_number)
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(url, json={"labels": [warning_label]}, headers=headers)
    if response.status_code >= 400:
        print(f"Failed to add label: {response.text}", file=sys.stderr)


def main():
    pr_number, repo = load_pr_info(EVENT_PATH)
    required_labels = set([label.strip() for label in REQUIRED_LABELS.split(",")])

    if pr_has_label(repo, pr_number, required_labels):
        print(f"Labels '{REQUIRED_LABELS}' present. Skipping check.")
        return

    if migration_files := check_for_migration_files():
        print(f"Migration files found:\n{migration_files}")
        add_label(repo, pr_number, WARNING_LABEL)
        send_slack_notification(pr_number, repo, required_labels)
    else:
        print("No migration files found.")


if __name__ == "__main__":
    main()
