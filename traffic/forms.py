from django import forms
from django.forms import widgets
from utils import locations


class UserLogin(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'User Name'}))
    password = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Password', 'type': "password"}))
    
class UserSignup(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'User Name'}))
    password = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Password', 'type': "password"}))
    password2 = forms.CharField(min_length=4, widget=forms.TextInput(attrs={'placeholder': 'Repeat your password', 'type': "password"}))
    company = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Company'}))
    tos = forms.BooleanField(required=True, initial=False)
    
    choices = []
    for k, v in locations.iteritems():
        choices.append((k, v['name']))
    location = forms.ChoiceField(required=True, choices = choices,)
                                
class ContactForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    message = forms.CharField(min_length=1, widget=forms.Textarea(attrs={'placeholder': 'Message'}))

class CommentForm(forms.Form):
    message = forms.CharField(required=True, min_length=2, widget=forms.Textarea(attrs={'placeholder': 'Any tips on this event?', 'rows': 2}))

    

