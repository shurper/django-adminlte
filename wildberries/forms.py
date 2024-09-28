from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from wildberries.models import Store, AutoBidderSettings, WeeklySchedule, IntraDaySchedule, PositionRange, KeywordData
from wildberries.utils import get_campaign_list


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)


class StoreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_wildberries_api_key(self):
        store = Store
        store.wildberries_api_key = self.cleaned_data['wildberries_api_key']
        if not get_campaign_list(store):
            raise forms.ValidationError("Недействительный API ключ Wildberries.")
        return store.wildberries_api_key

    def save(self, commit=True):
        store = super().save(commit=False)
        if self.user:
            store.user = self.user
        if commit:
            store.save()
        return store

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
    keywords_monitoring = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Мониторинг ключевых слов'
    )
    destinations_monitoring = forms.MultipleChoiceField(
        choices=[
            (0, 'Не выбрано'),
            (123585791, "Электросталь"),
            (-5650614, "Сочи")
        ],
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Мониторинг местоположений'
    )

    class Meta:
        model = AutoBidderSettings
        fields = ['product_id', 'keyword', 'destination', 'max_bid', 'is_enabled', 'depth', 'keywords_monitoring', 'destinations_monitoring']
        widgets = {
            'product_id': forms.NumberInput(attrs={'required': True}),
            'keyword': forms.TextInput(attrs={'required': True}),
            'max_bid': forms.NumberInput(attrs={'required': True, 'step': '0.01'}),
            'depth': forms.NumberInput(attrs={'required': True, 'step': '1'}),
            'destination': forms.Select(choices=[(0, 'Не выбрано'), (123585791, "Электросталь"), (-5650614, "Сочи")]),
            'is_enabled': forms.Select(choices=[(True, "Включен"), (False, "Выключен")]),
        }
        labels = {
            'product_id': 'ID продукта',
            'keyword': 'Ключевое слово',
            'destination': 'Местоположение',
            'max_bid': 'Максимальная ставка',
            'is_enabled': 'Включено',
            'depth': 'Глубина мониторинга',
            'keywords_monitoring': 'Мониторинг ключевых слов',
            'destinations_monitoring': 'Мониторинг местоположений',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Retrieve keyword data for the campaign and populate the keywords_monitoring choices
        campaign_id = self.initial.get('campaign_id') or self.instance.campaign_id
        if campaign_id:
            self.fields['keywords_monitoring'].choices = KeywordData.get_fixed_keywords_choices(campaign_id)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CreateMonitoringSettingsForm(forms.ModelForm):
    keywords_monitoring = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Мониторинг ключевых слов'
    )
    keywords_monitoring_add = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Мониторинг дополнительных ключевых слов'
    )
    destinations_monitoring = forms.MultipleChoiceField(
        choices=[
            (0, 'Не выбрано'),
            (123585791, "Электросталь"),
            (-5650614, "Сочи")
        ],
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Мониторинг местоположений'
    )

    class Meta:
        model = AutoBidderSettings
        fields = [
            'product_id',
            'keyword',
            'destination',
            'max_bid',
            'is_enabled',
            'depth',
            'keywords_monitoring',
            'keywords_monitoring_add',
            'destinations_monitoring'
        ]
        widgets = {
            'product_id': forms.NumberInput(attrs={'required': True}),
            'keyword': forms.TextInput(attrs={'required': True}),
            'max_bid': forms.NumberInput(attrs={'required': True, 'step': '0.01'}),
            'depth': forms.NumberInput(attrs={'required': True, 'step': '1'}),
            'destination': forms.Select(choices=[(0, 'Не выбрано'), (123585791, "Электросталь"), (-5650614, "Сочи")]),
            'is_enabled': forms.Select(choices=[(True, "Включен"), (False, "Выключен")]),
        }
        labels = {
            'product_id': 'ID продукта',
            'keyword': 'Ключевое слово',
            'destination': 'Местоположение',
            'max_bid': 'Максимальная ставка',
            'is_enabled': 'Включено',
            'depth': 'Глубина мониторинга',
            'keywords_monitoring': 'Мониторинг ключевых слов',
            'keywords_monitoring_add': 'Мониторинг дополнительных ключевых слов',
            'destinations_monitoring': 'Мониторинг местоположений',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Retrieve keyword data for the campaign and populate the keywords_monitoring choices
        campaign_id = self.initial.get('campaign_id') or self.instance.campaign_id
        if campaign_id:
            self.fields['keywords_monitoring'].choices = [('', 'не выбрано')] + KeywordData.get_fixed_keywords_choices(campaign_id)
            self.fields['keywords_monitoring_add'].choices = [('', 'не выбрано')] + KeywordData.get_additional_keywords_choices(campaign_id)



        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'



class AddKeywordsMonitoringForm(forms.ModelForm):
    keywords_monitoring_add = forms.MultipleChoiceField(
        choices=[],  # Здесь позже подставим существующие данные
        widget=forms.SelectMultiple(attrs={'required': False}),
        label='Удалить ключевые фразы',
        required=False
    )
    new_keywords = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Введите новые ключевые фразы через запятую'}),
        label='Добавить ключевые фразы',
        required=False
    )

    class Meta:
        model = KeywordData
        fields = ['keywords_monitoring_add', 'new_keywords']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проверяем, существует ли instance и имеет ли он данные
        if self.instance and self.instance.pk:
            # Добавляем ключевые фразы в выбор
            choices = [(kw, kw) for kw in self.instance.additional]
            # Добавляем пункт "Не удалять ничего" в начало списка
            choices.insert(0, ('', 'Не удалять ничего'))
            # Устанавливаем существующие ключевые фразы в качестве вариантов выбора
            self.fields['keywords_monitoring_add'].choices = choices
            self.initial['keywords_monitoring_add'] = self.instance.additional

        # Устанавливаем по умолчанию значение для keywords_monitoring_add
        self.initial['keywords_monitoring_add'] = ['']

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_empty_values(self, input_list):
        """Удаляет пустые значения из списка."""
        return [value for value in input_list if value]

    def clean_new_keywords(self):
        """Очистка и обработка новых ключевых фраз."""
        data = self.cleaned_data.get('new_keywords', '')
        if data:
            keywords_list = [kw.strip() for kw in data.split(',') if kw.strip()]
            return keywords_list
        return []

    def save(self, commit=True):
        """Сохранение формы с добавлением новых и удалением выбранных ключевых фраз."""
        instance = super().save(commit=False)
        # Получаем текущие ключевые фразы
        current_keywords = self.clean_empty_values(instance.additional or [])

        # Обработка новых ключевых фраз
        new_keywords = self.clean_empty_values(self.cleaned_data.get('new_keywords', []))
        if new_keywords:
            # Добавляем только новые ключевые слова, которых ещё нет
            updated_keywords = list(set(current_keywords + new_keywords))
        else:
            updated_keywords = current_keywords

        updated_keywords = self.clean_empty_values(updated_keywords)
        # Обработка удаляемых ключевых фраз
        keywords_to_remove = self.clean_empty_values(self.cleaned_data.get('keywords_monitoring_add', []))

        if keywords_to_remove:
            # Исключаем выбранные фразы из текущих
            updated_keywords = [kw for kw in updated_keywords if kw not in keywords_to_remove]

        # Обновляем поле в модели
        instance.additional = updated_keywords

        if commit:
            instance.save()

        return instance


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