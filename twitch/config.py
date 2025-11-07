import os

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID") or os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET") or os.environ.get("CLIENT_SECRET", "")
CHANNEL_LOGIN = os.environ.get("TWITCH_CHANNEL_LOGIN") or os.environ.get("CHANNEL_LOGIN", "")
