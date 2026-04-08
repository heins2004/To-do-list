from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username or handle", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter your password"})
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "What should we call you?"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "name@example.com"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Choose a username"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Display name"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "name@example.com"}),
    )
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Current password"}),
    )
    new_password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "New password"}),
    )
    new_password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm new password"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        wants_password_change = any([current_password, new_password1, new_password2])
        if not wants_password_change:
            return cleaned_data

        if not current_password:
            self.add_error("current_password", "Enter your current password.")
        elif not self.instance.check_password(current_password):
            self.add_error("current_password", "Current password is incorrect.")

        if not new_password1:
            self.add_error("new_password1", "Enter a new password.")
        if not new_password2:
            self.add_error("new_password2", "Confirm the new password.")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "The new passwords do not match.")

        if new_password1 and not self.errors.get("new_password1") and not self.errors.get("new_password2"):
            try:
                password_validation.validate_password(new_password1, self.instance)
            except ValidationError as error:
                self.add_error("new_password1", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user
