from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from main.forms import NewsForm
from main.models import News
from django.http import HttpResponse
from django.core import serializers

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.models import User
import json
import requests
from urllib.parse import unquote

@login_required(login_url='/auth/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        news_list = News.objects.all()
    else:
        news_list = News.objects.filter(user=request.user)

    context = {
        'npm' : '2406402542',
        'name': request.user.username,
        'class': 'PBP F',
        'news_list': news_list,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }

    return render(request, "main.html", context)

def create_news(request):
    form = NewsForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        news_entry = form.save(commit = False)
        news_entry.user = request.user
        news_entry.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "create_news.html", context)

@login_required(login_url='/auth/login')
def show_news(request, id):
    news = get_object_or_404(News, pk=id)
    news.increment_views()

    context = {
        'news': news
    }

    return render(request, "news_detail.html", context)

def show_xml(request):
     news_list = News.objects.all()
     xml_data = serializers.serialize("xml", news_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    news_list = News.objects.all()
    json_data = serializers.serialize("json", news_list)
    return HttpResponse(json_data, content_type="application/json")

def show_xml_by_id(request, news_id):
   try:
       news_item = News.objects.filter(pk=news_id)
       xml_data = serializers.serialize("xml", news_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except News.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, news_id):
   try:
       news_item = News.objects.get(pk=news_id)
       json_data = serializers.serialize("json", [news_item])
       return HttpResponse(json_data, content_type="application/json")
   except News.DoesNotExist:
       return HttpResponse(status=404)
   

def edit_news(request, id):
    news = get_object_or_404(News, pk=id)
    form = NewsForm(request.POST or None, instance=news)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "edit_news.html", context)

def delete_news(request, id):
    news = get_object_or_404(News, pk=id)
    news.delete()
    return HttpResponseRedirect(reverse('main:show_main'))

def show_json(request):
    news_list = News.objects.all()
    data = [
        {
            'id': str(news.id),
            'title': news.title,
            'content': news.content,
            'category': news.category,
            'thumbnail': news.thumbnail,
            'news_views': news.news_views,
            'created_at': news.created_at.isoformat() if news.created_at else None,
            'is_featured': news.is_featured,
            'user_id': news.user_id,
        }
        for news in news_list
    ]

    return JsonResponse(data, safe=False)

def show_json_by_id(request, news_id):
    try:
        news = News.objects.select_related('user').get(pk=news_id)
        data = {
            'id': str(news.id),
            'title': news.title,
            'content': news.content,
            'category': news.category,
            'thumbnail': news.thumbnail,
            'news_views': news.news_views,
            'created_at': news.created_at.isoformat() if news.created_at else None,
            'is_featured': news.is_featured,
            'user_id': news.user_id,
            'user_username': news.user.username if news.user_id else None,
        }
        return JsonResponse(data)
    except News.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

@csrf_exempt
@require_POST
def add_news_entry_ajax(request):
    try:
        # Try to parse JSON first (for Flutter API requests)
        data = json.loads(request.body)
        title = strip_tags(data.get("title", ""))
        content = strip_tags(data.get("content", ""))
        category = data.get("category", "")
        thumbnail = data.get("thumbnail", "")
        is_featured = data.get("is_featured", False)
        user_id = data.get("user_id")  # Accept user_id from Flutter
    except json.JSONDecodeError:
        # Fallback to form data (for web requests)
        title = strip_tags(request.POST.get("title", ""))
        content = strip_tags(request.POST.get("content", ""))
        category = request.POST.get("category", "")
        thumbnail = request.POST.get("thumbnail", "")
        is_featured = request.POST.get("is_featured") == 'on'
        user_id = None

    # Get user - prefer authenticated user, fallback to user_id from payload
    if request.user.is_authenticated:
        user = request.user
    elif user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Invalid user ID."
            }, status=400)
    else:
        return JsonResponse({
            "status": False,
            "message": "Authentication required."
        }, status=401)

    new_news = News(
        title=title,
        content=content,
        category=category,
        thumbnail=thumbnail,
        is_featured=is_featured,
        user=user
    )
    new_news.save()

    return JsonResponse({
        "status": True,
        "message": "News created successfully!",
        "news_id": str(new_news.id)
    }, status=201)

@csrf_exempt
def proxy_image(request):
    """Proxy external images to avoid CORS issues"""
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)

    try:
        # URL decode the image URL
        decoded_url = unquote(image_url)
        print(f"Proxying image: {decoded_url}")

        # Fetch image from external source
        response = requests.get(decoded_url, timeout=10, stream=True)
        response.raise_for_status()

        # Return the image with proper content type and CORS headers
        django_response = HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )

        # Add CORS headers
        django_response['Access-Control-Allow-Origin'] = '*'
        django_response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        django_response['Access-Control-Allow-Headers'] = '*'

        return django_response

    except requests.RequestException as e:
        print(f"Error fetching image {decoded_url}: {e}")
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)
    except Exception as e:
        print(f"Unexpected error proxying image: {e}")
        return HttpResponse(f'Unexpected error: {str(e)}', status=500)