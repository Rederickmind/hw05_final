from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    '''Функция отображения кастомной страницы ошибки 404'''
    return render(
        request,
        'core/404.html',
        {'path': request.path},
        status=HTTPStatus.NOT_FOUND
    )


def csrf_failure(request, reason=''):
    '''Функция отображения кастомной страницы ошибки 403'''
    return render(request, 'core/403csrf.html')
