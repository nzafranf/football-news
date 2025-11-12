import datetime
import json
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm
from authentication.forms import CustomUserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.models import User

@csrf_exempt
def register(request):
    # Check if this is an API request (JSON) or web request (form)
    if request.content_type == 'application/json' or 'application/json' in request.META.get('CONTENT_TYPE', ''):
        # Handle JSON API request for Flutter
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password1 = data.get('password1')
                password2 = data.get('password2')

                # Check if the passwords match
                if password1 != password2:
                    return JsonResponse({
                        "status": False,
                        "message": "Passwords do not match."
                    }, status=400)

                # Check if the username is already taken
                if User.objects.filter(username=username).exists():
                    return JsonResponse({
                        "status": False,
                        "message": "Username already exists."
                    }, status=400)

                # Create the new user
                user = User.objects.create_user(username=username, password=password1)
                user.save()

                return JsonResponse({
                    "username": user.username,
                    "status": 'success',
                    "message": "User created successfully!"
                }, status=200)

            except json.JSONDecodeError:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid JSON data."
                }, status=400)
            except KeyError as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Missing field: {str(e)}"
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Registration failed: {str(e)}"
                }, status=500)

        else:
            return JsonResponse({
                "status": False,
                "message": "Invalid request method."
            }, status=400)
    else:
        # Handle web form request
        form = CustomUserCreationForm()
        registration_success = False

        if request.method == "POST":
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                registration_success = True
                form = CustomUserCreationForm()  # Reset form
        context = {'form': form, 'registration_success': registration_success}
        return render(request, 'register.html', context)


@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            # Try to parse as JSON (for Flutter requests)
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except (json.JSONDecodeError, KeyError):
            # Fallback to form data (for web requests)
            username = request.POST.get('username')
            password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({
                "status": False,
                "message": "Username and password are required."
            }, status=400)

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return JsonResponse({
                    "username": user.username,
                    "user_id": user.id,
                    "status": True,
                    "message": "Login successful!"
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login failed, account is disabled."
                }, status=401)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login failed, please check your username or password."
            }, status=401)
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=400)

@csrf_exempt
def logout_user(request):
    logout(request)
    # Check if this is a JSON API request
    if request.content_type == 'application/json' or request.method == 'POST':
        return JsonResponse({
            "status": True,
            "message": "Logout successful!"
        }, status=200)
    else:
        # Web request - redirect
        response = HttpResponseRedirect(reverse('authentication:login'))
        response.delete_cookie('last_login')
        return response
    
