# University VM setup and verification

This guide reproduces the checks completed on 25 November 2026. It starts with three PowerShell terminals and ends with a verified scaffold on all three edge VMs, direct peer connectivity, and an origin download from both peers.

## 1. Open three PowerShell terminals and connect

Connect to the university VPN, then open three PowerShell terminals. Keep one terminal for each VM throughout the checks.

Run this in **each PowerShell terminal**. Enter your own university username at the prompt and your password directly at the SSH prompt.

```powershell
$UniversityUser = Read-Host "University username"
ssh "$UniversityUser@melkinkari.cs.helsinki.fi"
```

Once each terminal is at the jump host's Linux prompt, run the corresponding command below. Enter your own password at the VM prompt. If SSH asks you to trust a host for the first time, verify the fingerprint through a trusted university source before accepting it.

| Terminal | Destination command from the jump host | Edge ID | VM address |
| --- | --- | --- | --- |
| VM 1 | `ssh svm-11.cs.helsinki.fi` | `edge-a` | `128.214.11.91` |
| VM 2 | `ssh svm-11-2.cs.helsinki.fi` | `edge-b` | `128.214.9.25` |
| VM 3 | `ssh svm-11-3.cs.helsinki.fi` | `edge-c` | `128.214.9.26` |

**Observed result.** SSH succeeded from Windows through the jump host to all three VMs. All three reported the same OS hostname, so use the SSH destination and VM address to distinguish the terminals. Run the remaining commands on the VMs.

## 2. Check Python and tools

Run this block in **all three VM terminals**.

```bash
hostname
hostname -I
python3 --version
command -v python3.10
git --version
curl --version | head -n 1
command -v tmux || echo 'tmux unavailable'
command -v ss || echo 'ss unavailable'
```

Run this check on **VM 1**, where the browser proxy is planned.

```bash
if command -v nginx >/dev/null; then
    nginx -v
else
    echo 'nginx unavailable'
fi
```

Run the following in **all three VM terminals** to check that Python can create a virtual environment with working pip. The temporary directory is removed when the check finishes.

```bash
python3.10 - <<'PY'
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory(prefix="cdn-venv-check-") as directory:
    env = Path(directory) / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
    subprocess.run([str(env / "bin" / "python"), "-m", "pip", "--version"], check=True)

print("venv and pip OK")
PY
```

**Observed result.** All three VMs ran Ubuntu 22.04.5 with Python 3.10.12 at `/usr/bin/python3.10`, Git 2.34.1, and curl 7.81.0. Both `tmux` and `ss` were available on all three. Each temporary environment reported pip 22.0.2 and printed `venv and pip OK`. Nginx was unavailable on VM 1's `PATH`.

## 3. Check out the scaffold and run its smoke test

For a fresh checkout, run this on **each VM**. If you already have a checkout, enter it instead and check `git status --short` before switching commits. Preserve any local work.

```bash
cd ~
git clone https://github.com/nivedharengaraj/Distributed-CDN-Project.git distributed-cdn
cd distributed-cdn
```

From the checkout on **each VM**, select the same scaffold commit and create an environment in your own checkout.

```bash
git fetch origin main
git switch --detach 6b1d642
git rev-parse HEAD
python3.10 -m venv .venv
.venv/bin/python --version
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

**Observed result.** All three checkouts matched commit `6b1d642efbc653f281c2fdb26a85954ecad0080e`. The pinned dependencies installed on Python 3.10.12, including PySyncObj 0.3.17. Pip reported `No broken requirements found` on every VM. PySyncObj's legacy `setup.py install` message was followed by a successful install.

| VM | Scaffold smoke test |
| --- | --- |
| VM 1 | `1 passed in 0.29s` |
| VM 2 | `1 passed in 0.57s` |
| VM 3 | `1 passed in 0.31s` |

The smoke test imports the scaffold and checks that FastAPI registers the agreed routes.

## 4. Verify direct peer connections on ports 8000 and 4321

Coordinate the test window with the team because accounts on the same VM share listening ports. Once the ports are approved for the test, check for existing listeners on **each VM**. If a port is occupied, identify the process and coordinate with its owner.

```bash
ss -ltnp '( sport = :8000 or sport = :4321 )'
```

In **VM 1**, set its local address and its two peers.

```bash
local_ip=128.214.11.91
peer1=128.214.9.25
peer2=128.214.9.26
```

In **VM 2**, set its addresses.

```bash
local_ip=128.214.9.25
peer1=128.214.11.91
peer2=128.214.9.26
```

In **VM 3**, set its addresses.

```bash
local_ip=128.214.9.26
peer1=128.214.11.91
peer2=128.214.9.25
```

### Port 8000

In **all three terminals**, start one background listener per VM. Using the background job keeps the same SSH terminal available for the outbound requests.

```bash
cd ~/distributed-cdn
port=8000
.venv/bin/python -m uvicorn edge.main:app --host "$local_ip" --port "$port" &
listener_pid=$!
```

Wait for `Uvicorn running on` and port `8000` on **all three VMs**. Then run this block in **each terminal**.

```bash
for peer in "$peer1" "$peer2"; do
    printf '%s -> %s:%s: ' "$local_ip" "$peer" "$port"
    curl --noproxy '*' --connect-timeout 3 --max-time 5 \
        --silent --show-error --output /dev/null \
        --write-out 'HTTP %{http_code}\n' \
        "http://$peer:$port/openapi.json"
done
```

After recording the results, stop the listener you started in **each terminal**.

```bash
kill "$listener_pid"
wait "$listener_pid" || true
```

### Port 4321

Keep the address variables from above. In **all three terminals**, start one temporary listener on `4321`.

```bash
port=4321
.venv/bin/python -m uvicorn edge.main:app --host "$local_ip" --port "$port" &
listener_pid=$!
```

Wait until all three show `Uvicorn running on` with port `4321`. Rerun the same `curl` loop from the port 8000 check in **each terminal**. It now uses `4321`. A successful HTTP response from this temporary listener verifies the TCP path to that port. Raft behavior is covered by a separate test.

Stop the temporary listener on **each VM** and confirm that both ports are free.

```bash
kill "$listener_pid"
wait "$listener_pid" || true
ss -ltnp '( sport = :8000 or sport = :4321 )'
```

If you accidentally started a duplicate listener, use `jobs -l` and `ss -ltnp` to identify your running test process before stopping it. The most recent `$!` can refer to the failed duplicate.

**Observed result.** All six directed paths returned `HTTP 200` on both ports. Receiver logs also showed requests from both peers. During the first attempts, passing `LOCAL_IP` literally caused name resolution to fail, a failed paste kept one check on port `8000` after its peers had shut down, and restarting an already running listener caused an address-in-use error. The subsequent checks passed in every direction, and both ports were confirmed clear on all three VMs after cleanup.

| Source | Destinations | Port 8000 | Port 4321 |
| --- | --- | --- | --- |
| VM 1 | VM 2 and VM 3 | 2 of 2 returned `200` | 2 of 2 returned `200` |
| VM 2 | VM 1 and VM 3 | 2 of 2 returned `200` | 2 of 2 returned `200` |
| VM 3 | VM 1 and VM 2 | 2 of 2 returned `200` | 2 of 2 returned `200` |

## 5. Verify the origin on port 9000

On **VM 1**, confirm that port `9000` is available for the test. Create a single test object, print its SHA-256 digest, and serve the temporary directory. Keep the server running while the other two VMs fetch the object.

```bash
ss -ltnp '( sport = :9000 )'
origin_probe_dir=$(mktemp -d)
mkdir "$origin_probe_dir/objects"
printf 'CDN origin connectivity test\n' > "$origin_probe_dir/objects/probe.txt"
sha256sum "$origin_probe_dir/objects/probe.txt"
python3.10 -m http.server 9000 --bind 128.214.11.91 --directory "$origin_probe_dir"
```

Run this block on **VM 2 and VM 3**.

```bash
(
    set -o pipefail
    curl --noproxy '*' --fail --silent --show-error --max-time 5 \
        http://128.214.11.91:9000/objects/probe.txt | sha256sum
)
```

Compare each result with VM 1's digest, then press **Ctrl+C** on VM 1 to stop the temporary origin.

**Observed result.** VM 1 logged `HTTP 200` for both requests. The original file and both downloads had the same SHA-256 digest.

```text
ba894736d54fac6f85f0d91e8f9f79b40d91c6cb7e6ecf3d5dde4112f8951d37
```

The VM 1 log confirmed that the temporary server exited when interrupted.

## Summary

All VM setup checks in this guide passed. SSH worked on all three VMs, the same scaffold and dependencies ran on Python 3.10.12, and every edge reached both peers on ports `8000` and `4321`. Both peers downloaded the origin object on port `9000` and matched its checksum. The temporary listeners were stopped. The VMs are ready for the separate three-node Raft feasibility test. The Nginx browser check remains a follow-up.
