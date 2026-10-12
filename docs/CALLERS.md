# GitOps updater callers (FNWI)

This service exposes an HTTP API (`GET /gitops-updater`) used by CI and other automation to bump image versions in GitOps repositories.

FNWI runs **two gitops-updater instances** (different URLs, different Helm config). Each instance writes to a specific GitOps repo and serves the cluster(s) wired to that repo.

## Updater endpoints

| URL | Serves | GitOps repository |
|-----|--------|-------------------|
| `https://api-v2-tst.datanose.nl/gitops-updater` | DataNose Kubernetes (production and staging) | [UvA-FNWI/DataNose-v2-gitops](https://github.com/UvA-FNWI/DataNose-v2-gitops) |
| `https://k8s.datanose.nl/gitops-updater` | General-purpose cluster | [UvA-FNWI/k8s-gitops](https://github.com/UvA-FNWI/k8s-gitops) |

Required query parameters: `name` (configured handler id) and `version` (image tag or semver).

## Kubernetes clusters (three production environments)

| Cluster | GitOps source | Role |
|---------|---------------|------|
| **DataNose production** | `DataNose-v2-gitops` | Production DataNose workloads |
| **DataNose staging** | `DataNose-v2-gitops` | Staging for DataNose (same repo as production, different targets/branches or paths as configured) |
| **General / k8s** | `k8s-gitops` | Many additional apps with lower uptime expectations (no HA, no crown-jewel applications) |

The DataNose production and staging clusters both follow manifests from **one** GitOps repo; the third cluster is operated separately via **k8s-gitops** and is updated through the general-purpose updater URL.

## Authentication

| Method | Status |
|--------|--------|
| `Authorization: Bearer <secret>` | Preferred |
| `?secret=<secret>` on the query string | Deprecated; supported until **2027-01-07** |

Successful responses that used query `secret` include a `Deprecation` header and a JSON `deprecation` field.

## Release rollouts

[`.github/release-targets.yaml`](../.github/release-targets.yaml) is the list this repository publishes and rolls out. A push to `main` builds one version and pushes that image and chart to every registry in the file. It does not call an updater.

Each `rollout` entry is a separate GitHub Environment (`datanose`, `k8s`). Add a required reviewer on both environments. Approving one does not start the other. The call uses `Authorization: Bearer` and the secret named on that entry (`UPDATER_SECRET_DN`, `UPDATER_SECRET_K8S`).

| Rollout | Updater URL | Config `name` | Image registry |
|---------|-------------|---------------|----------------|
| `datanose` | `api-v2-tst.datanose.nl` | `gitops-updater` | `datanosecr.azurecr.io` |
| `k8s` | `k8s.datanose.nl` | `gitops-updater` | `fnwicr.azurecr.io` |

`k8s-gitops` still reads the Helm chart from `datanosecr.azurecr.io`. The workflow pushes the chart there as well as to `fnwicr`. Approve `k8s` only when that Application's image repository is `fnwicr.azurecr.io/gitops-updater` and `tag` is empty.

When adding a cluster, add a registry only if it pulls from a new host, and add a rollout entry with its own environment and secret.

## Local / chart defaults

The Helm chart default hostname in `values.yaml` is a placeholder (`gitops-updater.local`). Real hostnames are set per environment at deploy time.
