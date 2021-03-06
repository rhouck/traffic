from django import forms
from django.forms import widgets
from utils import locations

class ReferralForm(forms.Form):
    ref = forms.CharField(min_length=8, max_length=8)

class SplashForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Your Email Address'}))

class LocationForm(forms.Form):
    lat = forms.FloatField(widget=forms.HiddenInput(), min_value=-90.0, max_value=90.0)
    lng = forms.FloatField(widget=forms.HiddenInput(), min_value=-180.0, max_value=180.0)

class UserLogin(forms.Form):
    username = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    #password = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Password', 'type': "password"}))

class UserSignup(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'User Name'}))
    phone = forms.CharField(required=False, min_length=7, max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))
    password = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Password', 'type': "password"}))
    password2 = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Repeat your password', 'type': "password"}))
    company = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Company'}))
    tos = forms.BooleanField(required=True, initial=False)
    
    choices = []
    for k, v in locations.iteritems():
        choices.append((k, v['name']))
    location = forms.ChoiceField(required=True, choices = choices,)
                                
class ContactForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    message = forms.CharField(min_length=1, widget=forms.Textarea(attrs={'placeholder': 'Message'}))

class CommentForm(forms.Form):
    message = forms.CharField(required=True, min_length=2, widget=forms.Textarea(attrs={'placeholder': 'Any tips on this event?', 'rows': 2}))

"""
Api forms
"""
class ApiLoginForm(forms.Form):
    email = forms.EmailField()
class ApiSignupForm(forms.Form):
    email = forms.EmailField()
    ref = forms.CharField(required=False, min_length=8, max_length=8)
class ApiRefForm(forms.Form):
    ref = forms.CharField(min_length=8, max_length=8)
class ApiCommentForm(forms.Form):
    message = forms.CharField(min_length=2)
    email = forms.EmailField()
class ApiHighriseForm(forms.Form):
    tag = forms.CharField(required=False)
    email = forms.EmailField()


