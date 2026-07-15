# tbflingr

A CLI client for registering websites to the Ternbook web directory.

## Install

```bash
pip install tbflingr
```

## Usage

```bash
# Fling a site to an instance (fetches /.well-known/ternbook.json, POSTs to /api/heartbeat)
tbflingr fling https://mysite.com to https://myinstance.com

# Fling and save the pair as profile 1
tbflingr fling https://mysite.com to https://myinstance.com save profile 1

# Re-run a saved profile
tbflingr fling profile 1

# List saved profiles
tbflingr profiles
```

Profiles are stored in `~/.tbflingr/profiles/`.
