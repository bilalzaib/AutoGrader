from django.contrib.auth.forms import AuthenticationForm

class CustomAuthentication(AuthenticationForm):
    def confirm_login_allowed(self, user):
        # Inactive users are allowed
        """
        if not user.is_active:
            raise forms.ValidationError(
                _("This account is inactive."),
                code='inactive',
            )
        """
        pass