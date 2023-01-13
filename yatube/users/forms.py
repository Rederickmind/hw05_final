from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


# Класс для формы регистрации - наследник класса UserCreationForm
class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # Модель, с которой связана создаваемая форма
        model = User
        # Поля, которые должны быть видны в форме и их порядок
        fields = ('first_name', 'last_name', 'username', 'email')
