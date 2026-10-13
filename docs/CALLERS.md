# Callers

This repository does not list the clusters, hostnames, or Git repositories that call the updater. Each deployment sets those in its own Helm values: the hostname, the config entries, and the Git provider.

Release hosts and rollout environments are GitHub variables for the repository that publishes the image. See [Releases](../README.md#releases). A fork sets its own values.
