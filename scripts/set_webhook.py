from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    app_url = os.getenv("VERCEL_APP_URL", "").strip().rstrip("/")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()

    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")
    if not app_url:
        raise SystemExit("VERCEL_APP_URL is required, for example https://your-app.vercel.app")

    params = {
        "url": f"{app_url}/api/webhook",
        "allowed_updates": json.dumps(["message", "callback_query"]),
        "drop_pending_updates": "true",
    }
    if secret:
        params["secret_token"] = secret

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/setWebhook",
        data=urllib.parse.urlencode(params).encode("utf-8"),
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")

    print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
