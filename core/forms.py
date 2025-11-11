from django import forms
from allauth.socialaccount.forms import SignupForm

class CustomSocialSignupForm(SignupForm):
    """ソーシャルログイン用のサインアップフォーム"""
    language = forms.CharField(max_length=20, label='言語', required=True)
    phone_number = forms.CharField(max_length=20, label='電話番号', required=True)
    address = forms.CharField( max_length=255, label='住所', required=True )
    suburb = forms.CharField( max_length=100, label='市区町村', required=True)
    state = forms.CharField( max_length=100, label='都道府県', required=True)
    post_code = forms.CharField(max_length=20, label='郵便番号',required=True)
    
    def save(self, request):
      pass