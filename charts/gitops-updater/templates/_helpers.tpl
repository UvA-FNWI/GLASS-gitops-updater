{{/*
Name of the image pull secret.
Uses .Values.imagePullSecret if set, otherwise <chart-name>-registry
when .Values.externalSecrets.registry is set. Renders empty otherwise.
*/}}
{{- define "gitops-updater.imagePullSecretName" -}}
{{- if .Values.imagePullSecret -}}
{{- .Values.imagePullSecret -}}
{{- else if (.Values.externalSecrets).registry -}}
{{- printf "%s-registry" .Chart.Name -}}
{{- end -}}
{{- end -}}

{{- define "gitops-updater.secretName" -}}
{{- if .Values.secret -}}
{{- .Values.secretName -}}
{{- else if (.Values.externalSecrets).secret -}}
{{- printf "%s-secret" .Chart.Name -}}
{{- end -}}
{{- end -}}