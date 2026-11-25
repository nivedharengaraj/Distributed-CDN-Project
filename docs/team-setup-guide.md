# Team setup guide

Start on your laptop with the latest code on `main` and make a feature branch for your work. Use the university VMs when you need to check deployment or run a shared integration test.

## 1. Prerequisites

- Access to the team's GitHub repository and a local installation of Git.
- Python 3.10 with `venv` and pip. The three university VMs have been tested with **Python 3.10.12**. You can use another Python 3.10 patch release on your laptop. Install the project's pinned packages from [requirements.txt](../requirements.txt).
- For VM access, a working SSH client, your own University of Helsinki username and password, and access to the university network through eduVPN or the university remote desktop. In eduVPN, select **Institute Access → University of Helsinki**. Follow the [university eduVPN setup instructions](https://helpdesk.it.helsinki.fi/en/instructions/logging-and-connections/networks/eduvpn-university-helsinki).

The course prototype uses three edge nodes on separate VMs and direct communication between each edge and its two peers. The demo will show shared catalog state, consensus, and node logs. The stack is Python, FastAPI and Uvicorn for HTTP, Pydantic for shared schemas, HTTPX for outbound HTTP, PySyncObj/Raft for replicated catalog metadata, and pytest for tests. Each edge has its own filesystem cache. The origin serves the original image bytes, and Nginx is planned as the browser entry point.

## 2. Set up your laptop

For a new checkout, run these commands from the parent directory where you want the project. If GitHub prompts you to sign in, use your GitHub account with access to the repository.

```shell
git clone https://github.com/nivedharengaraj/Distributed-CDN-Project.git distributed-cdn
cd distributed-cdn
```

If you already cloned the repository, open the existing checkout and run `git status --short`. Preserve any local work before switching branches. In either case, start from the latest `main`.

```shell
git switch main
git pull --ff-only origin main
```

In **Windows PowerShell**:

```powershell
py -3.10 --version
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

In **Linux or WSL**:

```bash
python3.10 --version
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

Stop at the first failed command and keep its error output. When the tests pass, create your feature branch. Replace `your-component` with a descriptive name before running the command.

```shell
git switch -c feature/your-component
```

Implement and test your component on that branch. Push the branch and open a pull request when it is ready for review.

| Member | Start here |
| --- | --- |
| Member 1 | Cluster configuration, origin, startup, and proxy in `edge/config.py`, `infra/`, and `scripts/` |
| Member 2 | Cache and image retrieval in `edge/cache.py` |
| Member 3 | Shared models and replicated catalog in `edge/models.py` and `edge/catalog.py` |
| Member 4 | API, gallery, and integration in `edge/main.py`, `frontend/`, and `tests/test_integration.py` |

Use the [implementation agreements](implementation.md) for the interfaces between components.

## 3. Connect to the university VMs when needed

The course exercise allows two ways to reach the university network. Connect eduVPN and use a local terminal, or open the university remote desktop (VDI) and use a terminal inside it. Follow the [University of Helsinki remote-access instructions](https://helpdesk.it.helsinki.fi/en/logging-and-connections/remote-access-university-services).

### Log in to a gateway

Open one PowerShell tab per VM you need and run this in each tab. Enter your university username when asked and type your university password at the SSH password prompt. If SSH asks you to trust a gateway or VM for the first time, verify its fingerprint through a trusted university source.

```powershell
$UniversityUser = Read-Host "University username"
ssh "$UniversityUser@melkinkari.cs.helsinki.fi"
```

If `melkinkari` is unreachable, the exercise lists two alternative gateways. Try one of these commands in the same PowerShell tab after the first attempt exits.

```powershell
ssh "$UniversityUser@melkki.cs.helsinki.fi"
# Or use the other gateway.
ssh "$UniversityUser@melkinpaasi.cs.helsinki.fi"
```

If you're using a Linux terminal inside the remote desktop, run the Bash equivalent. Use the same list of gateway hostnames.

```bash
read -r -p "University username: " university_user
ssh "$university_user@melkinkari.cs.helsinki.fi"
```

### Check course access and log in to a VM

Once on a gateway, run:

```bash
groups
```

Check for `grp-cs-tcpdump` in the output. The exercise identifies this as the access group for its VMs. If the group is missing, contact Tiina or the course staff to confirm your access. If the group is present and a project VM still rejects your login, tell the course staff which VM you tried. The exercise lists VM 1 and VM 2, and the project also uses VM 3.

From the gateway's Linux prompt, run **one** command from the table in the corresponding tab. You may be prompted again for your university password.

| VM | Edge ID | Command from the jump host |
| --- | --- | --- |
| VM 1 | `edge-a` | `ssh svm-11.cs.helsinki.fi` |
| VM 2 | `edge-b` | `ssh svm-11-2.cs.helsinki.fi` |
| VM 3 | `edge-c` | `ssh svm-11-3.cs.helsinki.fi` |

Use your own university account and checkout. Run project commands on the edge VM after the second SSH login.

### Set up your checkout on a VM

Run this on each VM where you will run code. If you already have a checkout, enter it and check `git status --short` instead of cloning again.

```bash
cd ~
git clone https://github.com/nivedharengaraj/Distributed-CDN-Project.git distributed-cdn
cd distributed-cdn
```

From that checkout, run:

```bash
git switch main
git pull --ff-only origin main
git rev-parse HEAD
python3.10 --version
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

For a shared run, the coordinator records the current `main` commit after updating and confirms that all three checkouts report the same hash before starting services. The [VM setup verification guide](vm-setup-verification.md) records the baseline network and origin tests. You only need to verify your own login and the environment on VMs where you will run code.

## 4. IP addresses and ports

### IP addresses

Each VM has its own network address. Everyone who logs in to the same VM uses that VM's interfaces and IPs. Each account keeps its own checkout, Python environment, and runtime files. The VMs report the same OS hostname, so distinguish them by the SSH destination in the table or run `hostname -I` on the VM. For laptop-only tests, use `127.0.0.1`.

Read endpoint settings from configuration. Commit examples in `infra/cluster.example.json` and keep machine-specific values in the ignored `infra/cluster.local.json`. Use `NODE_ID` to select `edge-a`, `edge-b`, or `edge-c` for a shared deployment.

### Ports

A VM's listening ports are shared among accounts, including listeners on loopback. Two processes that try to listen on the same IP and TCP port on that VM normally conflict. Different VMs can use the same port numbers.

| Port | Team use |
| --- | --- |
| `8000` | Edge HTTP on each of the three VMs |
| `4321` | Raft on each of the three VMs |
| `9000` | Origin on VM 1 |
| `8080` | Planned Nginx browser entry point on VM 1 |

Use those ports for the coordinated shared deployment. For individual tests on a shared VM, agree on a different free port and use your own cache and Raft directories. Use loopback when only the same VM needs to reach the service. Check for existing listeners before starting a process.

```bash
ss -ltn
```

The team has verified peer connectivity for `8000` and `4321` and origin access on `9000`. Coordinate the test window because other processes may use the ports between runs.

## 5. Member 1 · Nginx on VM 1

The VM inventory found Nginx unavailable on VM 1's `PATH`. Check again on VM 1 and confirm with the course staff or university IT which user-level setup they support if it is still unavailable.

```bash
if command -v nginx >/dev/null; then
    nginx -v
else
    echo 'nginx unavailable on PATH'
fi
```

Complete `infra/nginx.conf` using user-writable paths for the PID, logs, and temporary files. Plan for a listener on VM 1's loopback at `127.0.0.1:8080` and round-robin upstreams on the three edge HTTP addresses. Proxy the gallery page, gallery API, and public media routes. Once the config is complete, validate it with `nginx -t` using the same config path and prefix you will use to start it.

When the proxy and edge routes are ready, connect eduVPN and run this from **local PowerShell** to reach the proxy through the jump host.

```powershell
$UniversityUser = Read-Host "University username"
ssh -J "$UniversityUser@melkinkari.cs.helsinki.fi" -N -L 127.0.0.1:8080:127.0.0.1:8080 "$UniversityUser@svm-11.cs.helsinki.fi"
```

Keep that terminal open and visit `http://127.0.0.1:8080/` in your browser. The Nginx browser check can proceed independently of the three-node Raft feasibility test.
