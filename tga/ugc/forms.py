from django import forms

from .models import Profile, Video


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('external_id', 'name')
        widgets = {
            'name': forms.TextInput,
        }


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('yt_id', 'title', 'uploader', 'upload_date', 'view_count',
                  'tg_id')
        widgets = {
            'yt_id': forms.TextInput,
            'title': forms.TextInput,
            'uploader': forms.TextInput,
            'upload_date': forms.DateInput,
            'view_count': forms.NumberInput,
            'tg_id': forms.TextInput,
        }