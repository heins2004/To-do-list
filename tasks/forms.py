from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "due_date", "type", "xp_reward"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Defeat the backlog"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add context, notes, or a boss strategy"}
            ),
            "type": forms.Select(),
            "xp_reward": forms.NumberInput(attrs={"min": 10, "max": 500, "step": 10}),
        }
