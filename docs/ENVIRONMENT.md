# Phase 0: Lab baseline

Author: `2025ae05142`

Recorded: 2026-10-15

## VM

| Check | Result |
|---|---|
| `whoami` | `s2025ae05142` |
| `hostname` | `ip-10-3-16-150.ap-south-1.compute.internal` |
| `pwd` | `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction` |
| `python3 --version` | `Python 3.12.9` |
| `git --version` | `git version 2.43.5` |
| `docker --version` | `Docker version 28.0.1, build 068a01e` |
| `kubectl version --client` | Failed: `/bin/bash: line 1: kubectl: command not found` (exit 127) |
| `minikube version` | `minikube version: v1.35.0` |

`docker info` confirmed that the Docker Engine server is reachable.

## Resources

`free -h`:

```text
               total        used        free      shared  buff/cache   available
Mem:            15Gi       3.9Gi       8.6Gi        71Mi       3.1Gi        11Gi
Swap:           2.0Gi          0B       2.0Gi
```

`df -h`:

```text
Filesystem                                                                                    Size  Used Avail Use% Mounted on
devtmpfs                                                                                      4.0M     0  4.0M   0% /dev
tmpfs                                                                                         7.7G   22M  7.6G   1% /dev/shm
tmpfs                                                                                         3.1G   17M  3.1G   1% /run
/dev/mapper/rl_localhost--live-root                                                            37G   11G   27G  30% /
tmpfs                                                                                         7.7G   20K  7.7G   1% /tmp
/dev/nvme0n1p1                                                                                960M  418M  543M  44% /boot
fs-09f73274fd140785b.efs.ap-south-1.amazonaws.com:/fsap-09be3efae53870d7c/12386/s2025ae05142  8.0E   91G  8.0E   1% /home/s2025ae05142/workspace
tmpfs                                                                                         1.6G   56K  1.6G   1% /run/user/1000
```

## Container, Kubernetes, and CI readiness

- Docker CLI and daemon are available.
- Minikube v1.35.0 is installed. No `minikube` profile/cluster exists yet; cluster startup is a later deployment-phase gate.
- The standalone `kubectl` command is not installed. The Kubernetes deployment phase must resolve this before it can meet its gate.
- The GitHub repository API and its Actions workflows endpoint responded with HTTP 200. This confirms endpoint access only, not permission or capacity to execute workflows. No local `gh` CLI is installed; workflow execution remains unverified until Phase 5.
- Total memory is 15 GiB; 11 GiB was available at capture time. Revisit resource use before monitoring services are started.
