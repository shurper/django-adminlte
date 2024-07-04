from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from wildberries.models import Store, AutoBidderSettings, WeeklySchedule, IntraDaySchedule, PositionRange
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


class PositionRangeForm(forms.Form):
    start_position = forms.IntegerField(min_value=1)
    end_position = forms.IntegerField(min_value=1)
    bid = forms.DecimalField(max_digits=10, decimal_places=2)


class IntraDayScheduleForm(forms.Form):
    start_time = forms.TimeField()
    end_time = forms.TimeField()


class WeeklyScheduleForm(forms.Form):
    day_of_week = forms.ChoiceField(choices=[
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')
    ])


class CreateAutoBidderSettingsForm(forms.ModelForm):
    class Meta:
        model = AutoBidderSettings
        fields = ['product_id', 'keyword', 'destination', 'max_bid', 'is_enabled', 'depth']
        widgets = {
            'product_id': forms.NumberInput(attrs={'required': True}),
            'keyword': forms.TextInput(attrs={'required': True}),
            'max_bid': forms.NumberInput(attrs={'required': True, 'step': '0.01'}),
            'depth': forms.NumberInput(attrs={'required': True, 'step': '1'}),
            'destination': forms.Select(choices=[(0, 'Не выбрано'),(123585791, "Электросталь"), (-5650614, "Сочи")]),
            'is_enabled': forms.Select(choices=[(True, "Включен"), (False, "Выключен")]),
        }


class PositionRangeForm(forms.ModelForm):
    class Meta:
        model = PositionRange
        fields = ['start_position', 'end_position', 'bid']


class IntraDayScheduleForm(forms.ModelForm):
    class Meta:
        model = IntraDaySchedule
        fields = ['start_time', 'end_time']


class WeeklyScheduleForm(forms.ModelForm):
    class Meta:
        model = WeeklySchedule
        fields = ['day_of_week']