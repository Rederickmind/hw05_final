from django.contrib import admin

from .models import Group, Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    # Интерфейс для поиска по тексту постов
    search_fields = ('text',)
    # Возможность менять поле group в любом посте
    list_editable = ('group',)
    # Возможность фильтрации по дате
    list_filter = ('pub_date',)
    # Свойство для пустых полей по-умолчанию
    empty_value_display = '-пусто-'


admin.site.register(Group)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'author',
        'text',
        'created'
    )

    search_fields = ('text',)
    list_filter = ('created', 'author', 'post',)
