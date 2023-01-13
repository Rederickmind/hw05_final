from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
            'image': ('Картинка')
        }
        help_texts = {
            'text': ('Текст поста не может быть пустым')
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError(
                'Вы обязательно должны что-нибудь написать!'
            )
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': ('Текст комментария')
        }
        help_text = {
            'text': ('Текст комментария не может быть пустым')
        }

    def clean_comment_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError(
                'Вы обязательно должны что-нибудь написать!'
            )
        return data
