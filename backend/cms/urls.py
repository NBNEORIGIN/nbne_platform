from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Admin CMS pages
    path('pages/', views.page_list, name='page_list'),
    path('pages/create/', views.page_create, name='page_create'),
    path('pages/<int:page_id>/', views.page_detail, name='page_detail'),
    path('pages/<int:page_id>/hero/', views.page_upload_hero, name='page_upload_hero'),
    path('pages/<int:page_id>/images/', views.page_upload_image, name='page_upload_image'),
    path('pages/<int:page_id>/images/<int:image_id>/', views.page_delete_image, name='page_delete_image'),
    # Public CMS pages
    path('public/pages/', views.public_pages, name='public_pages'),
    path('public/pages/<slug:slug>/', views.public_page_detail, name='public_page_detail'),
    # Admin blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
    path('blog/<int:post_id>/image/', views.blog_upload_image, name='blog_upload_image'),
    # Public blog
    path('public/blog/', views.public_blog_list, name='public_blog_list'),
    path('public/blog/<slug:slug>/', views.public_blog_detail, name='public_blog_detail'),
]
