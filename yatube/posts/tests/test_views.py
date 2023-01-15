import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

test_group_title = 'Тестовая группа'
test_group_slug = 'test_group'
test_group_description = 'Тестовое описание группы'
test_post_text = 'Тестовый пост'
test_image_name = 'small.jpg'
test_comment_text = 'Тестовый коммент к тестовому посту'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title=test_group_title,
            slug=test_group_slug,
            description=test_group_description,
        )

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

        cls.post = Post.objects.create(
            author=cls.user,
            text=test_post_text,
            group=cls.group,
            image=cls.uploaded
        )

        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:homepage'),
            'posts/group_list.html': reverse(
                'posts:group_posts',
                kwargs={'slug': 'test_group'}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': f'{cls.user.username}'}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{cls.post.pk}'}
            ),
            'posts/post_create.html': (
                reverse('posts:post_create')
            )
        }

        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text=test_comment_text,
        )

    @classmethod
    def tearDownClass(cls):
        '''Удаляем временную директорию и всё её содержимое'''
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='Nikita_Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем клиент автора тестового поста
        self.author_client = Client()
        self.author_client.force_login(PostsViewsTests.post.author)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        cache.clear()
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_by_author_uses_correct_template(self):
        """
        Проверка шаблона редактирования поста автором posts/post_create.html
        """
        response = self.author_client.\
            get(reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'}
            )
            )
        self.assertTemplateUsed(response, 'posts/post_create.html')

    # Проверка контекстов в view функциях
    def test_homepage_show_correct_context(self):
        '''Шаблон home сформирован с правильным контекстом.'''
        cache.clear()
        response = self.authorized_client.get(reverse('posts:homepage'))
        self.assertIsInstance(response.context['page_obj'], Page)
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group
        posts_image_0 = first_object.image

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)
        self.assertEqual(posts_image_0, self.post.image)

    def test_group_page_show_correct_context(self):
        '''Шаблон group сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        )

        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertIsInstance(response.context['group'], Group)
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group
        posts_image_0 = first_object.image

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)
        self.assertEqual(posts_image_0, self.post.image)

    def test_profile_page_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author.username}
        )
        )

        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertIsInstance(response.context['username'], User)
        self.assertEqual(
            response.context['post_quantity'],
            len(list(Post.objects.filter(
                author_id=self.post.author.id
            ))))
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group
        posts_image_0 = first_object.image

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)
        self.assertEqual(posts_image_0, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.guest_client.get(reverse(
            "posts:post_detail",
            kwargs={"post_id": self.post.id}
        )
        )
        self.assertIsInstance(response.context['post'], Post)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_create_edit_show_correct_context(self):
        '''Шаблон create_edit сформирован с правильным контекстом.'''
        response = self.author_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.FileField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        self.assertEqual(len(response.context['form'].fields), 3)

    def test_create_show_correct_context(self):
        '''Шаблон create сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.FileField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(len(response.context['form'].fields), 3)

    def test_comment_works(self):
        '''Валидная форма Комментария создает запись в базе данных.'''
        comments_count = Comment.objects.count()
        form_data = {'text': test_comment_text}
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail",
                kwargs={"post_id": self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=test_comment_text
        ).exists()
        )

    def test_anauthorized_user_cant_comment(self):
        '''Комментарий неавторизированного пользователя не создается'''
        comments_count = Comment.objects.count()
        form_data = {'text': 'Неавторизированный комментарий'}
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse(
                'posts:add_comment',
                kwargs={"post_id": self.post.id}
            ),
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(Comment.objects.filter(
            text='Неавторизированный комментарий'
        ).exists()
        )

    def test_cache_index(self):
        '''Проверка хранения и очищения кэша для Главной страницы.'''
        response = self.authorized_client.get(reverse('posts:homepage'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:homepage'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:homepage'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class PostsPaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )

        cls.POSTS_AMOUNT_FIRST_PAGE = 10
        cls.POSTS_AMOUNT_SECOND_PAGE = 3
        cls.TEST_POSTS_AMOUNT = 13

        test_posts = []
        for i in range(cls.TEST_POSTS_AMOUNT):
            test_posts.append(Post(author=cls.user,
                                   text=f'Тестовый пост {i}',
                                   group=cls.group
                                   )
                              )
        Post.objects.bulk_create(test_posts)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Авторизованый клиент - автор тестовых постов
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_homepage_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Главной равно 10.'''
        cache.clear()
        response = self.guest_client.get(reverse('posts:homepage'))
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_FIRST_PAGE
        )

    def test_homepage_second_page_contains_three_records(self):
        '''Проверка: количество постов на первой странице Главной равно 3.'''
        response = self.guest_client.get(reverse('posts:homepage') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_SECOND_PAGE
        )

    def test_group_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Группы равно 10.'''
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_FIRST_PAGE
        )

    def test_group_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на первой странице Группы равно 3.'''
        response = self.guest_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_SECOND_PAGE
        )

    def test_profile_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Профиля равно 10.'''
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_FIRST_PAGE
        )

    def test_profile_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на первой странице Профиля равно 3.'''
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_AMOUNT_SECOND_PAGE
        )


class PostAdditionalCheck(TestCase):
    '''Проверка создания поста на главной, в профиле и в группе'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group2',
            description='Тестовое описание другой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='Nikita_Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем клиент автора тестового поста
        self.author_client = Client()
        self.author_client.force_login(PostAdditionalCheck.post.author)

    def test_check_post_on_homepage(self):
        '''Созданный пост отображается на Главной странице'''
        cache.clear()
        response = self.authorized_client.get(reverse('posts:homepage'))
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)

    def test_check_post_in_group(self):
        '''Созданный пост отображается на странице Тестовой группы'''
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        )

        first_object = response.context['page_obj'][0]
        posts_group_0 = first_object.group

        self.assertEqual(posts_group_0, self.post.group)

    def test_check_post_not_in_incorrect_group(self):
        '''Созданный пост не в Тестовой группе 2'''
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        )

        first_object = response.context['page_obj'][0]
        posts_group_0 = first_object.group

        self.assertNotEqual(posts_group_0, self.group2)

    def test_check_post_in_user_profile(self):
        '''Созданный пост отображается в профиле автора'''
        response = self.author_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author.username}
        )
        )
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)


class FollowViewsTests(TestCase):
    '''Проверка работы подписок'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='test_author')
        cls.user2 = User.objects.create_user(username='test_user_2')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group2',
            description='Тестовое описание другой группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

        cls.POSTS_BY_AUTHOR = 1
        cls.ZERO_POSTS = 0

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент (будет подписан на author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованный клиент автора
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)
        # Создаем авторизованный клиент без подписок
        self.authorized_client_not_following = Client()
        self.authorized_client_not_following.force_login(self.user2)

    # Авторизованный пользователь может подписываться
    # на других пользователей и удалять их из подписок.
    def test_follow(self):
        '''Проверка подписки на автора через увеличение подписок'''
        count_follow = Follow.objects.filter(
            user=FollowViewsTests.user).count()
        data_follow = {
            'user': FollowViewsTests.user,
            'author': FollowViewsTests.author
        }
        follow_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTests.author.username}
        )
        response = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTests.author.username}
            ),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTests.user
        ).count()
        self.assertTrue(
            Follow.objects.filter(
                user=FollowViewsTests.user,
                author=FollowViewsTests.author
            ).exists()
        )
        self.assertRedirects(response, follow_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_unfollow(self):
        '''Проверка отписки от автора через уменьшение подписок'''
        count_follow = Follow.objects.filter(
            user=FollowViewsTests.user
        ).count()
        data_follow = {
            'user': FollowViewsTests.user,
            'author': FollowViewsTests.author
        }
        # Подписываемся на автора
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTests.author.username}
            ),
            data=data_follow, follow=True)
        # Отписываемся от автора
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTests.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTests.user
        ).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTests.user,
            author=FollowViewsTests.author).exists())
        self.assertEqual(count_follow, new_count_follow)

    # Новая запись пользователя появляется в ленте тех, кто на него подписан
    # и не появляется в ленте тех, кто не подписан.
    def test_followers_get_posts(self):
        '''Подписчик видит посты от автора на странице follow_index'''
        data_follow = {
            'user': FollowViewsTests.user,
            'author': FollowViewsTests.author
        }
        # Подписываемся на автора
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowViewsTests.author.username}
            ),
            data=data_follow, follow=True)
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group

        self.assertEqual(
            len(response.context['page_obj']),
            self.POSTS_BY_AUTHOR
        )

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)

    def test_not_followers_dont_get_posts(self):
        '''Не подписчик не видит посты от автора на странице follow_index'''
        cache.clear()
        response = self.authorized_client_not_following.get(
            reverse('posts:homepage')
        )
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author
        posts_group_0 = first_object.group

        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, self.post.pub_date)
        self.assertEqual(posts_author_0, self.post.author)
        self.assertEqual(posts_group_0, self.post.group)

        cache.clear()
        response = self.authorized_client_not_following.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.ZERO_POSTS
        )
