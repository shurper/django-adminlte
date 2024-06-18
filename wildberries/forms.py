from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from wildberries.models import Store
from wildberries.utils import get_campaign_list


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)


class StoreForm(forms.ModelForm):

    def clean_wildberries_api_key(self):
        store = Store
        store.wildberries_api_key = self.cleaned_data['wildberries_api_key']
        if not get_campaign_list(store):
            raise forms.ValidationError("Недействительный API ключ Wildberries.")
        return store.wildberries_api_key

    class Meta:
        model = Store

        fields = ['name', 'wildberries_name', 'wildberries_api_key', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'wildberries_name': forms.TextInput(attrs={'class': 'form-control'}),
            'wildberries_api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
