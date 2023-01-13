from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Group, Post, User

POSTS_AMOUNT = 10


def get_page_obj(queryset, request):
    """Создание Paginator с нужным queryset"""
    paginator = Paginator(queryset, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20 * 15)
def index(request):
    """Главная страница"""
    context = {
        'page_obj': get_page_obj(Post.objects.all(), request)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Получение постов нужной группы по запросу"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_page_obj(posts, request)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Отображение профиля пользователя"""
    # Код запроса к модели User
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    post_quantity = user.posts.count()
    context = {
        'username': user,
        'post_quantity': post_quantity,
        'page_obj': get_page_obj(post_list, request)
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Функция для просмотра поста и комментариев"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция создания нового поста"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    user = request.user
    context = {
        'form': form
    }
    if not form.is_valid():
        return render(request, 'posts/post_create.html', context)
    new_post = form.save(commit=False)
    new_post.author = user
    new_post.save()
    return redirect('posts:profile', user.username)


@login_required
def post_edit(request, post_id):
    """Функция для редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': PostForm(instance=post),
        'post': post,
        'is_edit': True
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    '''Добавление комментария'''
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
