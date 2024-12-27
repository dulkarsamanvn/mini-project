from django import forms
from accounts.models import CustomUser 
import re
from .models import Address

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone', 'gender', 'birthday', 'alternate_number']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Current Password'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not old_password:
            raise forms.ValidationError("Please enter your current password.")
        return old_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')

        # Password validation regex
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

        if not re.match(password_regex, new_password):
            raise forms.ValidationError(
                "Password must contain at least 8 characters, "
                "including one uppercase letter, one lowercase letter, one number, and one special symbol."
            )

        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        old_password = cleaned_data.get('old_password')

        # Check if new password and confirm password match
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New password and confirm password do not match.")
        
        # Prevent using the same password
        if old_password and new_password and old_password == new_password:
            raise forms.ValidationError("New password cannot be the same as the current password.")

        return cleaned_data
    




class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "name",
            "address_type",
            "phone",
            "alternate_phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default",
        ]
        widgets = {
            "is_default": forms.CheckboxInput(),
        }
