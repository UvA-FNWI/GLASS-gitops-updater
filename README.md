gitops-updater
=

The **gitops-updater** provides an HTTP API for updating YAML files stored in a git repository.
Deployments keep their own hostnames and Git repositories outside this tree. See [Releases](#releases).
You can use this when you're using gitops software on your Kubernetes cluster like Argo CD or Flux.
It's compatible with both GitHub and GitLab and can also do some tricks when you want to deploy review apps.
Besides that, the provider Helm chart also helps you out when you want to store the needed tokens within an
Azure Key Vault.

Overview
-
Idea is simple: you provide configuration when you deploy the `gitops-updater`, probably using the Helm values.
You can provide multiple configuration lines which are identified by a unique name.
Next to a name, every configuration line has a handler, a provider and some additional config (like a secret and path).
The chosen handler will determine the behaviour of your call.

Setup
-
Basically you need to install the provided Helm chart to a Kubernetes server to make the application available.
In the near future we will make the required Docker container and Helm chart publicly available. For now you need
to build it yourselves. You can do it, you're a great engineer!

For now, we will assume the updater is available somewhere on: `https://your-domain.com/gitops-updater`

GitHub provider
-
When configuring a GitHub provider, the configuration will look similar to the example below. You will need to create
a GitHub Personal Access Token (PAT) on the relevant settings page: https://github.com/settings/tokens

Make sure you grant sufficient permissions (`repo`) and make sure the PAT is available to the Docker container running
the gitops-updater as a mounted file. You can achieve this by mounting a secret,
possibly using the Azure Key Vault.
```yaml
providers:
  - name: my-github-repo
    repository: example/repo
    branch: main
    type: GitHub
    tokenPath: /mnt/secrets/gitops-updater-github-token
```

Argo CD handler
-
When you configure a configuration line like below, you will be able to update an Argo CD YAML file.
```yaml
config:
  - name: example-name
    path: directory/manifest.yaml
    secretPath: /mnt/secrets/gitops-updater-secret
    handler: argocd
    provider: my-github-repo
```
Given this configuration, the GET-call that should be executed looks like this:
```sh
curl -fsS \
  -H "Authorization: Bearer <updater-secret>" \
  "https://your-domain.com/gitops-updater?name=example-name&version=1.0.1"
```
The query parameter `secret` is deprecated (response includes `Deprecation` and `Sunset` headers until removal on **2027-01-07**); use the `Authorization: Bearer` header instead.

HTTP status codes: **401** for missing or invalid authentication; **409** when a downgrade is blocked; **422** for other client or processing errors. Successful updates use **200**.

To allow lowering `targetRevision`, set `allowDowngrade: true` on a config entry (Helm `config[].allowDowngrade`) or pass `allowDowngrade=true` on the request query string.
The repository deploy workflow (`.github/workflows/build.yml`) will switch to Bearer after an image that accepts it is serving.
The `argocd`-handler will validate if the secret matches the secret provided in the configuration. After that
it will retrieve the file `directory/manifest.yaml` and expect a file that looks a bit like this:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-name
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: default

  source:
    repoURL: my-repository.com
    chart: my/chart
    targetRevision: 1.0.0

    helm:
      values: |
        some: value

  destination:
    server: https://kubernetes.default.svc
    namespace: some-namespace

  syncPolicy:
    automated:
      prune: true
    syncOptions:
    - CreateNamespace=true
```
Please note that the value of `metadata.name` should match the name of the configuration line. When the secret
matches, the file exists and the name matches, it will retrieve the current version (`1.0.0`) and to a semver-comparison.
Only when the requested version (`1.0.1`) is higher than the current one, it will perform a commit where it updates the version.

Releases
-
Published versions are **`1.0.*`**. `Chart.yaml` and `pyproject.toml` use **`1.0.0`** as the development baseline. A push to `main` publishes the image as **`1.0.YYYYMMDDHHMMSS`** and a Helm chart with the same version and `appVersion`. Registries and rollouts are GitHub settings, not files in this repository. A fork sets its own values and does not inherit these.

Repository variables, under Settings → Secrets and variables → Actions → Variables:

| Variable | Value |
|----------|--------|
| `RELEASE_HOSTS` | Registry hosts, one per line. The image and chart are pushed to every host before any rollout. |
| `ROLLOUT_ENVIRONMENTS` | GitHub Environment names, separated by spaces, commas, or new lines. |

Each name in `ROLLOUT_ENVIRONMENTS` is an environment with a required reviewer and deployment limited to `main`. Approving one does not roll out the others. On each environment set:

| Kind | Name | Value |
|------|------|--------|
| Variable | `UPDATER_URL` | Updater URL, including the `/gitops-updater` path. |
| Variable | `UPDATER_CONFIG` | Config `name` to pass to that updater. |
| Variable | `UPDATER_SECRET_NAME` | Name of the organization secret that holds the updater secret. |
| Secret | the name in `UPDATER_SECRET_NAME` | Organization secret, shared with this repository and limited to that environment. |

This branch still passes the updater secret as a query parameter. The Deployment image tag is that `appVersion` unless `tag` is set, so a new release changes the pod spec and Kubernetes recreates the pod. Older **`0.5.*`** chart versions stay on that line until a deploy moves `targetRevision` to a **`1.0.*`** version that is semver-greater.

Development
-
Install [uv](https://docs.astral.sh/uv/), then from the repository root:

```sh
uv sync
uv run python -c "import gitops_updater.main"
```

To refresh the lockfile after changing dependencies in `pyproject.toml`:

```sh
uv lock
```

Build the container image:

```sh
docker build -t gitops-updater:local .
```

The image uses a multi-stage build: compile dependencies in a builder stage, then copy only the virtualenv into a slim runtime image (no compiler toolchain in production).

Run the same checks as PR CI (no cluster or remote GitOps repo required):

```sh
uv sync --frozen --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest -v
```

Optional: run the app locally (handlers still need a real config file and Git credentials to update repos):

```sh
export CONFIG_PATH=/path/to/config.yaml
uv run flask --app gitops_updater.main run --port 8080
```