import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import LIMIT_PAGES
from ..models import Follow, Group, Post

User = get_user_model()

NUMBER_OF_TEST_POSTS = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        for i in range(NUMBER_OF_TEST_POSTS):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )
        cls.post2 = Post.objects.create(
            author=cls.user,
            id=101,
            text='Тестовый пост 13',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'testname'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_image_0 = first_object.image
        group_title_0 = first_object.group.title
        group_slug_0 = first_object.group.slug
        group_description_0 = first_object.group.description
        self.assertEqual(post_text_0, 'Тестовый пост 13')
        self.assertEqual(post_author_0, 'testname')
        self.assertEqual(post_image_0, 'posts/small.gif')
        self.assertEqual(group_title_0, 'Тестовая группа')
        self.assertEqual(group_slug_0, 'test-slug')
        self.assertEqual(group_description_0, 'Тестовое описание')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = (self.authorized_client.get(reverse('posts:group_list',
                                               kwargs={'slug': 'test-slug'})))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image
        self.assertEqual(post_group_0,
                         'Тестовая группа')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = (self.authorized_client
                    .get(reverse('posts:profile',
                         kwargs={'username': 'testname'})))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_image_0 = first_object.image
        self.assertEqual(post_author_0,
                         'testname')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = (self.authorized_client
                    .get(reverse('posts:post_detail',
                         kwargs={'post_id': 101})))
        first_object = response.context['post']
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        self.assertEqual(post_id_0,
                         101)
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = (self.authorized_client
                    .get(reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = (self.authorized_client
                    .get(reverse('posts:post_edit',
                         kwargs={'post_id': 1})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_posts(self):
        """Паджинатор выводит 10 постов на первую страницу index, group list,
        profile"""
        pages_names = {
            reverse('posts:index'): LIMIT_PAGES,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): LIMIT_PAGES,
            reverse('posts:profile',
                    kwargs={'username': 'testname'}): LIMIT_PAGES,
            reverse('posts:index') + '?page=2': NUMBER_OF_TEST_POSTS + 1
            - LIMIT_PAGES,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'})
            + '?page=2': NUMBER_OF_TEST_POSTS + 1 - LIMIT_PAGES,
            reverse('posts:profile',
                    kwargs={'username': 'testname'})
            + '?page=2': NUMBER_OF_TEST_POSTS + 1 - LIMIT_PAGES
        }
        for url, number_posts in pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 number_posts)

    def test_post_displayed_correctly(self):
        """Пост корректно отображается на главной странице, на странице группы,
        в профайле пользователя """
        group = Group.objects.create(
            title='Тестовая группа для нового поста',
            slug='new-group',
            description='Тестовое описание'
        )
        user = User.objects.create_user(username='testname_test')
        post = Post.objects.create(
            author=user,
            text='Пост проверка',
            group=group
        )
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'new-group'}),
            reverse('posts:profile',
                    kwargs={'username': 'testname_test'}),
        ]
        for url in pages_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIn(post, response.context['page_obj'].object_list)

    def test_post_not_in_not_own_group(self):
        """Проверка, что пост не попадает в группу, для которой
        не был предназначен """
        group = Group.objects.create(
            title='Тестовая группа для нового поста 2',
            slug='own-group',
            description='Тестовое описание'
        )
        user = User.objects.create_user(username='testname_test')
        post = Post.objects.create(
            author=user,
            text='Пост проверка на отображение',
            group=group
        )
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={
                                                  'slug': 'test-slug'
                                              }))
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_index_cache_before_clear(self):
        """Проверка работы кэширования index до очистки"""
        group = Group.objects.create(
            title='Тестовая группа для проверки кэша',
            slug='cache-group',
            description='Тестовое описание'
        )
        user = User.objects.create_user(username='cache-test')
        response = self.authorized_client.get(reverse('posts:index'))
        content_before_create = response.content
        Post.objects.create(
            author=user,
            text='Пост проверка cache',
            group=group
        )
        response = self.authorized_client.get(reverse('posts:index'))
        content_after_create = response.content
        self.assertEqual(content_before_create, content_after_create)

    def test_index_cache_after_clear(self):
        """Проверка работы кэширования index после очистки"""
        group = Group.objects.create(
            title='Тестовая группа для проверки кэша',
            slug='cache-group',
            description='Тестовое описание'
        )
        user = User.objects.create_user(username='cache-test')
        response = self.authorized_client.get(reverse('posts:index'))
        content_before_create = response.content
        Post.objects.create(
            author=user,
            text='Пост проверка cache',
            group=group
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        content_after_cache_clear = response.content
        self.assertNotEqual(content_before_create, content_after_cache_clear)


class FollowTests(TestCase):

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для теста подписок'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Тест подписки"""
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )

    def test_unfollow(self):
        """Тест отписки"""
        self.assertEqual(Follow.objects.all().count(), 0)
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        self.assertEqual(Follow.objects.all().count(), 1)
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_record_is_displayed_by_subscribers(self):
        """запись появляется в ленте тех, кто подписан"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для теста подписок')

    def test_record_is_not_displayed_for_non_subscribers(self):
        """запись  не появляется в ленте тех, кто не подписан"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_following.get(reverse
                                                  ('posts:follow_index'))
        self.assertNotContains(response,
                               'Тестовая запись для теста подписок')

    def test_subscriptions_to_yourself(self):
        """тест подписки на самого себя"""
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client_auth_following.get(reverse('posts:profile_follow',
                                               kwargs={'username':
                                                       self.user_following.
                                                       username}))
        self.assertEqual(Follow.objects.all().count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )

    def test_repeat_subscription(self):
        """Тест повторной подписки"""
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)
