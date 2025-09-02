from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.urls import reverse
from datetime import datetime

from .models import JournalEntry, JournalPages
from .sentiment_utils import get_mood_trend

# helper function (not a Django view, just a utility)
def login_user(request, username, password):
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # code to insert a record in JournalPages
        user_pages = JournalPages.objects.filter(user=user)

        if not user_pages.exists():
            JournalPages.objects.create(user=user)

        session = request.session
        session['username'] = username
        return {"status": "success", "message": "Login successful"}
    else:
        return {"status": "error", "message": "Invalid username or password."}

# API login endpoint
# @api_view(["GET", "POST"])
def api_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            response = login_user(request, username, password)
            # return Response(response, status=status.HTTP_200_OK if response["status"] == "success" else status.HTTP_401_UNAUTHORIZED)
            if response["status"] == "success":
                return redirect("home")
            else:
                return render(request, "loginpage.html", {"error": response.get("message", "Invalid credentials")})
        else:
            # return Response({"status": "error", "message": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)
            return render(request, "loginpage.html", {"error": "Username and password required"})
        
    else:
        return render(request, "loginpage.html")

@api_view(["POST"])
def api_register(request):
    if request.method == "POST":

        User = get_user_model()

        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if username and email and password:
            if User.objects.filter(username=username).exists():
                return Response({"status": "error", "message": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email).exists():
                return Response({"status": "error", "message": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Create user properly
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password  # Django automatically hashes it
            )

            return redirect("api_login")
        else:
            return Response({"status": "error", "message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
# @login_required
def api_pageAdd(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # <-- Parse JSON
            addPages = int(data.get("addPages", 1))
            addPages *= 2
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({"status": "error", "message": "Invalid input"}, status=400)

        user_pages = JournalPages.objects.filter(user=request.user).first()
        if not user_pages:
            return JsonResponse({"status": "error", "message": "User pages not found"}, status=404)

        current_pages = user_pages.pages
        user_pages.pages = current_pages + addPages
        user_pages.save()

        # Reload to confirm update
        user_pages.refresh_from_db()

        print("User pages:", user_pages.pages)
        print("Current pages:", current_pages)
        print("Add pages:", addPages)

        return JsonResponse({"status": "success", "message": "Page added successfully", "pages": user_pages.pages})
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@login_required
def api_save(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("Parsed data:", data, type(data))  # Debug

            # If data is a list, take the first item
            if isinstance(data, list):
                data = data[0]

            content = data.get("content", "") if isinstance(data, dict) else ""

            if not content:
                return JsonResponse({"status": "error", "message": "Content is empty"}, status=400)

            todays_journals = JournalEntry.objects.filter(user=request.user, created_at__date=datetime.now().date()).first()

            if todays_journals:
                todays_data = todays_journals.content
                print("Today's journal data:", todays_data)
                print("New content:", content)
                # Compare with new content
                if todays_data != content:
                    print("Content has changed.")
                    todays_data = content
                    todays_journals.content = todays_data
                    todays_journals.save()

                    todays_journals.refresh_from_db()
                    print("Updated journal entry:", todays_journals.content)
                else:
                    print("Content is the same.")
            else:
                # Save the journal entry
                JournalEntry.objects.create(
                    user=request.user,
                    content=content
                )

            return JsonResponse({"status": "success", "message": "Journal entry saved successfully"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_journals(request):
    if request.method == "GET":
        # Fetch and return the user's journal entries
        journals = JournalEntry.objects.filter(user=request.user)
        journal_data = [{"id": journal.id, "title": journal.created_at, "content": journal.content, "sentiment": journal.sentiment, "confidence": journal.confidence} for journal in journals]
        return Response({"status": status.HTTP_200_OK, "journals": journal_data})
    else:
        return Response({"status": status.HTTP_400_BAD_REQUEST, "message": "Invalid request method"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mood_trend_view(request, period):
    try:
        if period not in ["weekly", "monthly", "annual"]:
            return Response({"error": "Invalid period"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        data = get_mood_trend(user, period=period)
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def home(request):
    user_pages = JournalPages.objects.filter(user=request.user).first()
    pages_count = user_pages.pages if user_pages else 10
    context = {
        "pages_range": range(pages_count),
        "username": request.user.username if request.user.is_authenticated else "",
        "email": request.user.email if request.user.is_authenticated else ""
    }
    return render(request, "index.html", context)


@login_required
def api_logout(request):
    if request.method in ["POST", "GET"]:
        logout(request)
        return JsonResponse({"status": "success", "redirect_url": reverse("login")})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return redirect("login")
