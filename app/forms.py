from django import forms
from .models import Product

# 複数ファイルアップロード用カスタムウィジェット
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # 複数選択を許可

class ProductForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('meat', '肉'),
        ('fish', '水産'),
        ('vegetable', '野菜'),
        ('fruit', '果物'),
        ('dairy', '乳製品'),
        ('main', '主食'),
        ('sozai', '惣菜'),
        ('snack', 'お菓子'),
        ('other', 'その他'),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # ここで required=False にしているので、画像が無くてもエラーにならない
    images = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={
            'multiple': True,
            'class': 'form-control'
        }),
        label="商品画像（複数可）"
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'price',
            'expiration_date',
            'quantity',
            'category',
            'origin',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '産地'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # 保存処理をオーバーライド
    def save(self, commit=True):
        product = super().save(commit=False)
        images = self.files.getlist('images')  # POSTされたファイルを取得

        # 画像は最大5枚まで
        if len(images) > 5:
            raise forms.ValidationError("アップロードは最大5枚までです。")

        if commit:
            # images を順番に image1〜image5 にセット
            for idx, img in enumerate(images):
                if idx == 0:
                    product.image1 = img
                elif idx == 1:
                    product.image2 = img
                elif idx == 2:
                    product.image3 = img
                elif idx == 3:
                    product.image4 = img
                elif idx == 4:
                    product.image5 = img
            product.save()  # DB保存

        return product
