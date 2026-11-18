# Cloud probe: Claude Code cloud session for Gemini simulator jobs

Run 2026-11-18 02:23 UTC in a Claude Code cloud session. No code changed. No credentials used.

## 1. Machine

- `nproc`: 4
- `free -g`: 15 GB total, 15 GB available, no swap
- `df -h .`: /dev/vda 252G size, 15G used, 25G avail (25G is the session's writable allowance)
- `python3 --version`: Python 3.13.18 (not 3.12)
- `uname -a`: Linux vm 6.18.44-fc-v595 #1 SMP PREEMPT_DYNAMIC x86_64
- Relevant env vars set: HTTPS_PROXY / https_proxy / NO_PROXY (agent proxy), CLOUDSDK_PROXY_*, CLOUDSDK_AUTH_ACCESS_TOKEN, MCP_TOOL_TIMEOUT, CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_REMOTE_SESSION_ID, CLAUDE_CODE_SESSION_ATTENDED. No limit or timeout var for processes.

## 2. pip install

`pip install -q google-genai google-auth httpx numpy pyyaml pytest`: real 10.7s, user 1.9s, sys 0.2s. No errors.

## 3. Network

| URL | HTTP code | Time |
|---|---|---|
| https://aiplatform.googleapis.com | 404 | 0.53s |
| https://generativelanguage.googleapis.com | 404 | 0.34s |
| https://oauth2.googleapis.com | 404 | 0.16s |
| https://pypi.org | 200 | 0.11s |
| https://github.com | 400 | 0.12s |

All reachable. Google traffic goes through the HTTPS proxy (`CONNECT` returns 200). An unauthenticated `GET /v1beta/models` returns Google's own 403 (`vary: X-Origin`), so responses come from Google, not the proxy.

## 4. Data and tests

- `gunzip -kf data/*-x.jsonl.gz data/v1.jsonl.gz`: real 1.6s. `data/` is 460M afterward.
- `python3 -m pytest -q tests`: 30 passed, 3 skipped in 17.05s (real 17.7s).

## 5. Background process

`nohup` date loop started 02:23:11. After 3 minutes, `wc -l /tmp/alive.txt` = 4 (02:23:11, 02:24:11, 02:25:11, 02:26:11). Process still running. 3 minutes does not prove survival over 1-6 hours: the container is reclaimed after inactivity or when the session ends.
