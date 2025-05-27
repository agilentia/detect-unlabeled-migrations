import os

import slack_sdk
from slack_sdk.errors import SlackApiError


class SlackException(Exception):
    pass


def post_message(*, channel: str, message: str, **kwargs) -> None:

    token = os.getenv("SLACK_BOT_TOKEN")

    client = slack_sdk.WebClient(token)
    kwargs.setdefault("link_names", True)
    try:
        client.chat_postMessage(channel=channel, text=message, **kwargs)
    except SlackApiError as error:
        error_msg = error.response.get("error", "unknown")
        if error_msg in ("invalid_auth", "not_authed"):
            raise SlackException(f"SLACK_API_AUTH_KEY is invalid: {error_msg}")
        raise SlackException(f"Error posting to channel {channel}: {error_msg}")
