{{- define "lms.name" -}}
{{ .Release.Name }}
{{- end -}}

{{- define "lms.fullname" -}}
{{ .Values.fullnameOverride }}
{{- end -}}

{{- define "lms.frontendPath" -}}
/services/lms/frontend
{{- end -}}

{{- define "lms.backendPath" -}}
/services/lms/backend
{{- end -}}

{{- define "lms.socketPath" -}}
/services/lms/socket.io
{{- end -}}
