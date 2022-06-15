from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exist_at_desired_location(self):
        """Страницы /, /group/<slug>/, /profile/<username>/,
        /posts/<post_id>/, доступны любому пользователю."""
        urls = [
            '/',
            '/group/test-slug/',
            '/profile/testname/',
            '/posts/1/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_unexisting_page_and_create_url_redirect_anonymous(self):
        """Проверка ошибки 404 при запросе несуществующей страницы и
        cтраница /create/ перенаправляет анонимного пользователя """
        url_names_status = {
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.FOUND
        }
        for address, status in url_names_status.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_create_and_edit_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю и
        страница /posts/<post_id>/edit/ доступна автору поста"""
        url_names_status = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
        }
        for address, status in url_names_status.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/testname/': 'posts/profile.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_add_comment_available_authorized(self):
        """Комментировать посты может только авторизованный пользователь"""
        response = self.authorized_client.get('/posts/1/comment/')
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))
        response = self.guest_client.get('/posts/1/comment/')
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')

    def test_url_404_uses_correct_template(self):
        """Страница 404 использует кастомный шаблон"""
        response = self.authorized_client.get('/unexcpected_page/')
        self.assertTemplateUsed(response, 'core/404.html')
