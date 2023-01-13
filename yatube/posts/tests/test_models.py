from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, User

User = get_user_model()
SYMBOLS_AMOUNT = 15
test_group_title = 'Тестовая группа'
test_group_slug = 'test_group'
test_group_description = 'Тестовое описание группы'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title=test_group_title,
            slug=test_group_slug,
            description=test_group_description,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, длиннее 15 символов...',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        test_group = PostModelTest.group
        test_post = PostModelTest.post

        group_str = str(test_group)
        expected_group_str = test_group.title
        self.assertEqual(group_str, expected_group_str, ('Метод str группы'
                                                         'работает неверно'))

        post_str = str(test_post)
        expected_post_str = test_post.text[:SYMBOLS_AMOUNT]
        self.assertEqual(post_str, expected_post_str, ('Метод str поста'
                                                       'работает неверно'))

    def test_post_verbose_name(self):
        """verbose_name в полях модели POst совпадает с ожидаемым."""
        test_post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).verbose_name, expected)

    def test_group_verbose_name(self):
        """verbose_name в полях модели POst совпадает с ожидаемым."""
        test_group = PostModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Ссылка на группу',
            'description': 'Описание группы'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_group._meta.get_field(value).verbose_name, expected)

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        test_post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).help_text, expected)
