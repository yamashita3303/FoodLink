from django import forms
from .models import User, Store
from django.core.exceptions import ValidationError

class PhoneSplitWidget(forms.MultiWidget):
    """電話番号を3分割で入力するウィジェット"""
    def __init__(self, attrs=None):
        widgets = [
            forms.TextInput(attrs={'size': 4, 'maxlength': 4, 'placeholder': '090'}),
            forms.TextInput(attrs={'size': 4, 'maxlength': 4, 'placeholder': '1234'}),
            forms.TextInput(attrs={'size': 4, 'maxlength': 4, 'placeholder': '5678'}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split('-')
        return ['', '', '']

class PhoneSplitField(forms.MultiValueField):
    """3つの入力欄を1つの文字列にまとめる"""
    widget = PhoneSplitWidget

    def __init__(self, *args, **kwargs):
        fields = [
            forms.CharField(),
            forms.CharField(),
            forms.CharField(),
        ]
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return '-'.join(part.strip() for part in data_list)
        return ''

class UserSignupStep1Form(forms.ModelForm):
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='再確認用パスワード', widget=forms.PasswordInput)
    phone = PhoneSplitField(label='電話番号')

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("このメールアドレスは既に登録されています。")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("パスワードが一致しません。")
        return cleaned_data

class UserSignupStep2Form(forms.ModelForm):
    class Meta:
        model = User
        fields = ['postal_code', 'prefecture', 'city', 'address_line1', 'address_line2']

class StoreSignupStep1Form(forms.ModelForm):
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='再確認用パスワード', widget=forms.PasswordInput)
    phone = PhoneSplitField(label='電話番号')

    class Meta:
        model = Store
        fields = ['username', 'phone', 'password']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if Store.objects.filter(phone=phone).exists():
            raise ValidationError("この電話番号は既に登録されています。")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("パスワードが一致しません。")
        return cleaned_data

class StoreSignupStep2Form(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['postal_code', 'prefecture', 'city', 'address_line1', 'opening_time', 'closing_time']

class StoreSigninForm(forms.Form):
    phone = PhoneSplitField(label='電話番号')
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)