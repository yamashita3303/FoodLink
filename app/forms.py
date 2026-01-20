from django import forms
from .models import User, Product
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation

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

# ユーザネーム
class UserEditUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

# メールアドレス
class UserEditEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

# パスワード
class UserEditPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html()
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（再入力）",
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        # パスワードの一致チェックのみ行う(バリデーションは行わないvar)
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("新しいパスワードが一致しません")
        return cleaned_data
    # バリデーションを外す場合は validate_password を呼ばない(パスワードを8文字以上にする等の制約を付ける場合はコメントアウトを外す)
        # if p1 and p2 and p1 != p2:
        #     raise forms.ValidationError("新しいパスワードが一致しません")
        # if p1:
        #     password_validation.validate_password(p1, self.user)
        # return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

# 電話番号
class UserEditPhoneForm(forms.ModelForm):
    phone = PhoneSplitField(label='電話番号')
    class Meta:
        model = User
        fields = ['phone']

# 住所
class UserEditAddressForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['postal_code', 'prefecture', 'city', 'address_line1', 'address_line2']

class StoreSignupStep1Form(forms.ModelForm):
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

class StoreSignupStep2Form(forms.ModelForm):
    class Meta:
        model = User
        fields = ['postal_code', 'prefecture', 'city', 'address_line1', 'opening_time', 'closing_time']

# 店舗名（ユーザーネーム）
class StoreEditUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

# パスワード
class StoreEditPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html()
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（再入力）",
        widget=forms.PasswordInput
    )

    def __init__(self, store, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("新しいパスワードが一致しません")
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.store.set_password(password)
        if commit:
            self.store.save()
        return self.store

# 電話番号
class StoreEditPhoneForm(forms.ModelForm):
    phone = PhoneSplitField(label='電話番号')

    class Meta:
        model = User
        fields = ['phone']

# 住所
class StoreEditAddressForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['postal_code', 'prefecture', 'city', 'address_line1']

# 営業時間
class StoreEditHoursForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['opening_time', 'closing_time']
        widgets = {
            'opening_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }


class StoreSigninForm(forms.Form):
    phone = PhoneSplitField(label='電話番号')
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'price', 'expiration_date', 'quantity',
            'origin', 'image1', 'image2', 'image3', 'image4', 'image5', 'notes'
        ]
        widgets = {
            'expiration_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔥 ここ重要：POSTされた datetime-local を正しく解釈させる
        self.fields['expiration_date'].input_formats = ['%Y-%m-%dT%H:%M']

        for i in range(1, 6):
            self.fields[f'image{i}'].required = False