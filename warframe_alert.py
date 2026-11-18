#!/usr/bin/env python3
"""Send Discord alerts for Steel Path Void Cascade at Tuvul Commons."""
import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.warframestat.us/pc/fissures"
LIVE_URL = "https://browse.wf/live"
STATE_FILE = Path(__file__).with_name("notified_fissures.json")
KST = ZoneInfo("Asia/Seoul")


def get_json(url):
    request = Request(url, headers={"User-Agent": "warframe-tuvul-alert/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_state():
    if not STATE_FILE.exists():
        return {}
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid state file format")
    return data


def target(fissure):
    return (
        fissure.get("isHard") is True
        and fissure.get("isStorm") is not True
        and fissure.get("node") == "Tuvul Commons (Zariman)"
        and fissure.get("missionType") == "Void Cascade"
    )


def post_webhook(webhook_url, payload):
    request = Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "warframe-tuvul-alert/1.0"},
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f"Discord returned HTTP {response.status}")


def format_kst(value):
    return parse_time(value).astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def alert_payload(fissure):
    started_at = format_kst(fissure["activation"])
    expires_at = format_kst(fissure["expiry"])
    expiry_timestamp = int(parse_time(fissure["expiry"]).timestamp())
    return {
        "username": "Warframe 균열 알림",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "🔔 강철의 길 보이드 범람 등장!",
            "description": (
                "**미션:** 보이드 범람 (Void Cascade)\n"
                "**위치:** 투불 광장, 자리만 (Tuvul Commons)\n"
                "**적 레벨:** 150–155\n"
                "**난이도:** 강철의 길 (Steel Path)\n"
                f"**등장 시간:** {started_at}\n"
                f"**종료 시간:** {expires_at}\n"
                f"**남은 시간:** <t:{expiry_timestamp}:R>\n\n"
                f"[현재 균열 확인하기]({LIVE_URL})"
            ),
            "color": 0x3498DB,
            "footer": {"text": "새로 발견된 균열당 한 번만 알림"},
        }],
    }


def main():
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook.startswith("https://discord.com/api/webhooks/") and not webhook.startswith("https://discordapp.com/api/webhooks/"):
        raise ValueError("DISCORD_WEBHOOK_URL secret is missing or invalid")

    if os.environ.get("TEST_NOTIFICATION") == "true":
        post_webhook(webhook, {
            "username": "Warframe 균열 알림",
            "allowed_mentions": {"parse": []},
            "content": "✅ 워프레임 균열 알림 웹훅 연결 테스트 성공!",
        })
        print("Test notification sent")
        return

    now = datetime.now(timezone.utc)
    state = load_state()
    # Keep only active IDs; discarded IDs cannot represent an active duplicate.
    state = {fid: expiry for fid, expiry in state.items() if parse_time(expiry) > now}

    fissures = get_json(API_URL)
    if not isinstance(fissures, list):
        raise TypeError("Unexpected API response: expected list")

    matched = 0
    sent = 0
    for fissure in fissures:
        if not isinstance(fissure, dict) or not target(fissure):
            continue
        if any(k not in fissure for k in ("id", "activation", "expiry")):
            raise ValueError("Target fissure missing id, activation or expiry")
        if parse_time(fissure["expiry"]) <= now:
            continue
        matched += 1
        fid = str(fissure["id"])
        if fid in state:
            print("Already notified:", fid)
            continue
        # Only remember IDs after Discord has accepted the message.
        post_webhook(webhook, alert_payload(fissure))
        state[fid] = fissure["expiry"]
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sent += 1
        print("Notified:", fid)

    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Active matches: {matched}; new alerts: {sent}")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
