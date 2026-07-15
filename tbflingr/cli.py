#!/usr/bin/env python3
"""
tbflingr — Packaged curl for flinging URLs to Ternbook web directory instances.

Usage:
    tbflingr fling <website_url> to <instance_url> [save profile <number>]
    tbflingr fling profile <number>
    tbflingr load profile <number>
    tbflingr profiles
    tbflingr help
"""

import sys
import json
import os
import urllib.request
import urllib.error


PROFILES_DIR = os.path.join(os.path.expanduser("~"), ".tbflingr", "profiles")
HEARTBEAT_PATH = "/api/heartbeat"
WELLKNOWN_PATH = "/.well-known/ternbook.json"


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def build_source_url(website_url: str) -> str:
    """Strip trailing slashes and append /.well-known/ternbook.json."""
    return website_url.rstrip("/") + WELLKNOWN_PATH


def build_target_url(instance_url: str) -> str:
    """Append /api/heartbeat to the instance URL, avoiding double slashes."""
    return instance_url.rstrip("/") + HEARTBEAT_PATH


# ---------------------------------------------------------------------------
# Profile management
# ---------------------------------------------------------------------------

def load_profile(number: int) -> dict | None:
    path = os.path.join(PROFILES_DIR, f"profile_{number}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_profile(number: int, website_url: str, instance_url: str) -> str:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f"profile_{number}.json")
    data = {
        "profile": number,
        "website_url": website_url,
        "instance_url": instance_url,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def _print_response(body: str) -> None:
    """Pretty-print the response, formatted as a list if it's a heartbeat JSON."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return

    LABELS = {
        "ok":          ("Status",       lambda v: "OK" if v is True else "FAIL" if v is False else str(v)),
        "url":         ("URL",          str),
        "ial":         ("IAL",          str),
        "prevIal":     ("Prev IAL",     str),
        "epoch":       ("Epoch",        str),
        "ialVerified": ("IAL Verified", lambda v: "yes" if v is True else "no" if v is False else str(v)),
    }

    known_keys = set(LABELS)
    if known_keys & set(data):
        for key, (label, fmt) in LABELS.items():
            if key in data:
                print(f"  {label:<14} {fmt(data[key])}")
        for k, v in data.items():
            if k not in known_keys:
                print(f"  {k:<14} {v}")
    else:
        print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Core fling
# ---------------------------------------------------------------------------

def fling(website_url: str, instance_url: str) -> None:
    """Fetch website_url/.well-known/ternbook.json, then POST to instance_url/api/heartbeat."""
    source_url = build_source_url(website_url)
    target_url = build_target_url(instance_url)

    print(f"  Fetching   {source_url}")
    try:
        with urllib.request.urlopen(source_url, timeout=30) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
    except urllib.error.URLError as exc:
        print(f"  error: could not fetch {source_url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    print(f"  Flinging → {target_url}")
    req = urllib.request.Request(
        target_url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            response_body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_body = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        print(f"  error: could not reach {target_url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    print(f"  ← {status}")
    if response_body.strip():
        print()
        _print_response(response_body)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_fling(args: list[str]) -> None:
    # Shorthand: tbflingr fling profile <number>
    if len(args) >= 2 and args[0].lower() == "profile":
        try:
            number = int(args[1])
        except ValueError:
            print(f"  error: profile number must be an integer, got {args[1]!r}", file=sys.stderr)
            sys.exit(1)
        data = load_profile(number)
        if data is None:
            print(f"  error: profile {number} not found", file=sys.stderr)
            sys.exit(1)
        print(f"  Loaded profile {number}: {data['website_url']} → {data['instance_url']}")
        fling(data["website_url"], data["instance_url"])
        return

    website_url, instance_url, profile_number = parse_fling_args(args)

    if profile_number is not None:
        path = save_profile(profile_number, website_url, instance_url)
        print(f"  Profile {profile_number} saved → {path}")

    fling(website_url, instance_url)


def cmd_load(args: list[str]) -> None:
    if len(args) < 2 or args[0].lower() != "profile":
        print("usage: tbflingr load profile <number>", file=sys.stderr)
        sys.exit(1)
    try:
        number = int(args[1])
    except ValueError:
        print(f"  error: profile number must be an integer, got {args[1]!r}", file=sys.stderr)
        sys.exit(1)

    data = load_profile(number)
    if data is None:
        print(f"  error: profile {number} not found", file=sys.stderr)
        sys.exit(1)

    print(f"  Loaded profile {number}: {data['website_url']} → {data['instance_url']}")
    fling(data["website_url"], data["instance_url"])


def cmd_profiles(_args: list[str]) -> None:
    if not os.path.isdir(PROFILES_DIR):
        print("  No profiles saved yet.")
        return
    files = sorted(f for f in os.listdir(PROFILES_DIR) if f.startswith("profile_") and f.endswith(".json"))
    if not files:
        print("  No profiles saved yet.")
        return
    for fname in files:
        path = os.path.join(PROFILES_DIR, fname)
        with open(path) as f:
            data = json.load(f)
        print(f"  [{data['profile']}]  {data['website_url']}  →  {data['instance_url']}")


def parse_fling_args(args: list[str]) -> tuple[str, str, int | None]:
    if len(args) < 3 or args[1].lower() != "to":
        print(
            "usage: tbflingr fling <website_url> to <instance_url> [save profile <number>]",
            file=sys.stderr,
        )
        sys.exit(1)

    website_url = args[0]
    instance_url = args[2]
    profile_number: int | None = None

    rest = args[3:]
    if rest:
        if len(rest) >= 3 and rest[0].lower() == "save" and rest[1].lower() == "profile":
            try:
                profile_number = int(rest[2])
            except ValueError:
                print(f"  error: profile number must be an integer, got {rest[2]!r}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"  error: unexpected arguments: {' '.join(rest)}", file=sys.stderr)
            sys.exit(1)

    return website_url, instance_url, profile_number


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

HELP = """tbflingr — Packaged curl for flinging URLs to Ternbook web directory instances.

Commands:
  fling <website_url> to <instance_url> [save profile <number>]
      Fetch <website_url>/.well-known/ternbook.json and POST it to
      <instance_url>/api/heartbeat.
      If 'save profile <number>' is given, the pair is saved for reuse.

  fling profile <number>
      Load a saved profile and run the fling immediately.

  load profile <number>
      Same as 'fling profile <number>'.

  profiles
      List all saved profiles.

  help
      Show this message.

Profiles are stored in ~/.tbflingr/profiles/.
"""


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0].lower() in ("help", "--help", "-h"):
        print(HELP)
        return

    cmd = args[0].lower()
    rest = args[1:]

    if cmd == "fling":
        cmd_fling(rest)
    elif cmd == "load":
        cmd_load(rest)
    elif cmd == "profiles":
        cmd_profiles(rest)
    else:
        print(f"  error: unknown command {cmd!r}. Run 'tbflingr help' for usage.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
