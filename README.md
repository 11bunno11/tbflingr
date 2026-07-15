# tbflingr

A CLI client for registering websites to the Ternbook web directory.

## Install

```bash
pip install tbflingr
```

## Usage


Fling a site to a Ternbook instance (fetches `/.well-known/ternbook.json`, POSTs to `/api/heartbeat`)<br>
```bash
tbflingr fling https://mysite.com to https://myinstance.com`
```

Fling and save the pair as profile 1<br>
```bash
tbflingr fling https://mysite.com to https://myinstance.com save profile 1
```

Re-run a saved profile<br>
```bash
tbflingr fling profile 1
```

List saved profiles<br>
```bash
tbflingr profiles
```

For more regarding Ternbook, visit https://ternbook.neocities.org

Profiles are stored in `~/.tbflingr/profiles/`.
