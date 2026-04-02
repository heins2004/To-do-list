from django import forms

from .models import Habit


class HabitForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Habit
        fields = ["title", "description", "start_date", "xp_reward"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Morning training"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Describe the daily ritual"}
            ),
            "xp_reward": forms.NumberInput(attrs={"min": 10, "max": 250, "step": 5}),
        }
