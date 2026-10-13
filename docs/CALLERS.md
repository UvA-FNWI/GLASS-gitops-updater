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

Publish settings live in GitHub, not in this repository. See [Releases](../README.md#releases). A push to `main` builds one version and pushes that image and chart to every host in the `RELEASE_HOSTS` repository variable. It does not call an updater until an environment is approved.

`ROLLOUT_ENVIRONMENTS` lists the GitHub Environments. Each one has `UPDATER_URL`, `UPDATER_CONFIG`, and `UPDATER_SECRET_NAME`. Approving one does not start the other. This branch still sends the secret as a query parameter, because the pod that is serving does not accept Bearer yet. The follow-up branch switches both calls to `Authorization: Bearer` after that image is live.

| Environment | Updater URL | Config `name` | `UPDATER_SECRET_NAME` | Image registry |
|-------------|-------------|---------------|-----------------------|----------------|
| `datanose` | `https://api-v2-tst.datanose.nl/gitops-updater` | `gitops-updater` | `UPDATER_SECRET_DN` | `datanosecr.azurecr.io` |
| `k8s` | `https://k8s.datanose.nl/gitops-updater` | `gitops-updater` | `UPDATER_SECRET_K8S` | `datanosecr.azurecr.io` |

Both current clusters use `datanosecr`. Add another line to `RELEASE_HOSTS` only when a new cluster pulls its image and chart from a different host. Add a cluster by creating its environment and appending that name to `ROLLOUT_ENVIRONMENTS`.

## Local / chart defaults

The Helm chart default hostname in `values.yaml` is a placeholder (`gitops-updater.local`). Real hostnames are set per environment at deploy time.
