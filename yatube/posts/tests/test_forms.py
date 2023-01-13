import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

User = get_user_model()
test_group_title = 'Тестовая группа'
test_group_slug = 'test_group'
test_group_description = 'Тестовое описание группы'
test_image_name = 'small.jpg'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title=test_group_title,
            slug=test_group_slug,
            description=test_group_description,
        )

        cls.form = PostForm()

        cls.small_jpg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name=test_image_name,
            content=cls.small_jpg,
            content_type='image/jpg'
        )

    @classmethod
    def tearDownClass(cls):
        '''Удаляем временную директорию и всё её содержимое'''
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='Nikita_Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        '''
        При отправке валидной формы создаётся пост
        и происходит редирект на Профиль
        '''
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост',
            'image': self.uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                image=f'posts/{test_image_name}'
            ).exists()
        )

    def test_post_edit(self):
        '''
        Проверка что валидная форма изменяет пост отобранный по id
        и происходит редирект на post_detail
        '''
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост для изменения'
        )

        posts_count = Post.objects.count()
        post_id = self.post.id

        form_data = {
            'text': 'Изменённый тестовый пост'
        }

        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=({post_id})
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                args=({self.post.id})
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый пост для изменения'
            ).exists())
        self.assertTrue(
            Post.objects.filter(
                text='Изменённый тестовый пост'
            ).exists())
