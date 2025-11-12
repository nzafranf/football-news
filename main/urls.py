from django.urls import path
from main.views import show_main, create_news, show_news, show_xml, show_json, show_xml_by_id, show_json_by_id
from main.views import edit_news
from main.views import delete_news
from main.views import add_news_entry_ajax
from main.views import proxy_image

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('create-news/', create_news, name='create_news'),
    path('news/<str:id>/', show_news, name='show_news'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('xml/<str:news_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:news_id>/', show_json_by_id, name='show_json_by_id'),
    path('news/<uuid:id>/edit', edit_news, name='edit_news'),
    path('news/<uuid:id>/delete', delete_news, name='delete_news'),
    path('create-news-ajax', add_news_entry_ajax, name='add_news_entry_ajax'),
    path('create-flutter/', add_news_entry_ajax, name='create_flutter'),  # Alias for Flutter
    path('proxy-image/', proxy_image, name='proxy_image'),  # Image proxy for Flutter
]
