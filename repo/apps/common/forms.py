from django import forms


class WorkspaceSessionForm(forms.Form):
    session_key = forms.CharField(required=False, max_length=64)