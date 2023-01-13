from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, User

User = get_user_model()

test_group_title = 'Тестовая группа'
test_group_slug = 'test_group'
test_group_description = 'Тестовое описание группы'
test_post_text = 'Тестовый пост'
test_comment_text = 'Тестовый коммент к тестовому посту'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title=test_group_title,
            slug=test_group_slug,
            description=test_group_description,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=test_post_text,
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text=test_comment_text,
        )

        cls.public_addresses_response = {
            '/': HTTPStatus.OK,
            '/group/test_group/': HTTPStatus.OK,
            f'/profile/{cls.user.username}/': HTTPStatus.OK,
            f'/posts/{cls.post.pk}/': HTTPStatus.OK,
        }

        cls.public_urls_templates = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{cls.group.slug}/',
            'posts/profile.html': f'/profile/{cls.user.username}/',
            'posts/post_detail.html': f'/posts/{cls.post.pk}/',
        }

        cls.logged_in_urls = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{cls.group.slug}/',
            'posts/profile.html': f'/profile/{cls.user.username}/',
            'posts/post_detail.html': f'/posts/{cls.post.pk}/',
            'posts/post_create.html': '/create/'
        }

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='Nikita_Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем клиент автора тестового поста
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.post.author)

    def test_public_pages(self):
        '''Проверка общедоступных страниц'''
        for address, status in self.public_addresses_response.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_unexisting_page_error(self):
        '''Проверка ошибки при переходе на несуществующую страницу'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unauthorized_redirect_create_page(self):
        '''Проверка редиректа неавторизованного пользователя'''
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
        )

    def test_create_page(self):
        '''Проверка страницы доступной авторизованному пользователю'''
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_by_author(self):
        '''Проверка страницы редактирования поста автором'''
        response = self.author_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_by_not_author(self):
        '''Проверка страницы редактирования поста не автором'''
        response = self.authorized_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.pk}
            ),
        )

    def test_unauthorized_templates_use(self):
        '''Проверка шаблонов неавторизованного пользователя'''
        cache.clear()
        for template, url in self.public_urls_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_authorized_templates_use(self):
        '''Проверка шаблонов авторизованного пользователя'''
        cache.clear()
        for template, url in self.logged_in_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_author_template_use(self):
        '''Проверка шаблона для автора поста'''
        response = self.author_client.get(
            f'/posts/{PostsURLTests.post.pk}/edit/'
        )
        self.assertTemplateUsed(response, 'posts/post_create.html')
