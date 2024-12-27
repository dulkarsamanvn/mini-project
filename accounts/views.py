from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import CustomUser
from category.models import Category
from brand.models import Brand
from product.models import Product,ProductVariant, ProductVariantImage
from .utils import generate_otp, send_otp
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control,never_cache
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import cache_control


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        full_name = request.POST.get("full_name","").strip()
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")
        
        if len(password)<8:
            messages.error(request,'Password must be atleast 8 characters long')
            return redirect('signup')
        
        if ' ' in email:
            messages.error(request,'email cannot contain spaces')
            return redirect('signup')


        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered")
            return redirect("signup")
        
        if not full_name or not all(c.isalnum() or c in "_." for c in full_name):
            messages.error(request,"full name can only contain letters,numbers,underscores and periods")
            return redirect("signup")
        
        if not any(p.isupper() for p in password):
            messages.error(request,"password must contain one uppercase letter")
            return redirect("signup")

        if not any(p.islower() for p in password):
            messages.error(request,"password must contain one lowercase letter")
            return redirect("signup")
        
        if not any(p.isdigit() for p in password):
            messages.error(request,"password must contain one digit")
            return redirect("signup")
        
        if not any(p in "!@#$%^&*(),.?\":{}|<>" for p in password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("signup")

        # Generate and send OTP
        otp = generate_otp()
        cache.set(email, otp, timeout=300)  # Cache OTP for 5 minutes
        send_otp(email, otp)

        # Temporarily store user data in cache
        cache.set(f"user_data_{email}", {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password,
        }, timeout=300)

        # Store email in session
        request.session["email"] = email

        messages.success(request, "OTP sent to your email")
        return redirect("verify_otp")

    return render(request, "signup.html")

@never_cache 
def verify_otp_view(request): 
    if request.method == "POST": 
        # Check if this is a resend request 
        if request.POST.get('resend_otp') == 'true': 
            # Retrieve email from the session 
            email = request.session.get("email") 
            if not email: 
                messages.error(request, "Session expired. Please try again.") 
                return redirect("signup") 
 
            # Generate and send a new OTP 
            otp = generate_otp() 
            cache.set(email, otp, timeout=300)  # Cache OTP for 5 minutes 
            send_otp(email, otp) 
 
            messages.success(request, "New OTP sent to your email") 
            return redirect("verify_otp") 
 
        # Existing OTP verification logic 
        otp = "".join(request.POST.getlist("otp"))  # Combine all OTP inputs 
 
        email = request.session.get("email") 
        if not email: 
            messages.error(request, "Session expired. Please try again.") 
            return redirect("signup") 
 
        cached_otp = cache.get(email) 
        if not cached_otp:
            messages.error(request, "OTP has expired. Please request a new OTP.") 
            return redirect("verify_otp")

        if str(cached_otp) == otp: 
            # Retrieve user data from cache 
            user_data = cache.get(f"user_data_{email}") 
            if user_data: 
                user = CustomUser.objects.create_user( 
                    email=user_data["email"], 
                    full_name=user_data["full_name"], 
                    phone=user_data["phone"], 
                    password=user_data["password"], 
                ) 
                user.is_active = True 
                user.save() 
 
                # Clear cache 
                cache.delete(email) 
                cache.delete(f"user_data_{email}") 
 
                messages.success(request, "Account created successfully") 
                return redirect("login") 
        else: 
            messages.error(request, "Invalid OTP") 
            return redirect("verify_otp") 
 
    return render(request, "verify_otp.html")



@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(email=email, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is blocked. Please contact the admin.")
                return redirect("login")
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html', {'google_login_url': '/auth/login/google-oauth2/'})





@user_passes_test(lambda u: u.is_staff)  # Ensure only staff users can access
@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_dashboard_view(request):
    if not request.user.is_authenticated or not request.user.is_admin:
        return redirect('adminlogin')
    # Get the search query from GET request (if any)
    search_query = request.GET.get("search", "").strip()

    # Filter users based on the search query
    if search_query:
        users = CustomUser.objects.filter(
            is_admin=False,  # Exclude admin users
        ).filter(
            full_name__icontains=search_query  # Search by full name (case-insensitive)
        )
    else:
        users = CustomUser.objects.filter(is_admin=False)  # Default: all non-admin users

    # Handle blocking/unblocking users
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")
        try:
            user = CustomUser.objects.get(id=user_id)
            if action == "block":
                user.is_active = False
                user.save()
            elif action == "unblock":
                user.is_active = True
                user.save()
        except CustomUser.DoesNotExist:
            pass

    return render(request, "admin_dashboard.html", {"users": users, "search_query": search_query})





from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


from wishlist.models import Wishlist


# @login_required
# def home_view(request):
#     # Fetch categories and brands that are listed
#     categories = Category.objects.filter(is_listed=True)
#     brands = Brand.objects.filter(is_listed=True)

#     # Get the sort_by query parameter
#     sort_by = request.GET.get('sort_by')
#     logger.debug(f"Sorting by: {sort_by}")  # Log the sort_by value

#     # Start with all products
#     products = Product.objects.prefetch_related('variants__images')

#     # Initialize a list to hold processed products
#     processed_products = []

#     for product in products:
#         # Get the first (primary) variant for sorting and display
#         primary_variant = product.variants.first()
#         if not primary_variant:
#             continue

#         primary_image = primary_variant.images.filter(is_primary=True).first()
#         primary_image_url = primary_image.image.url if primary_image else None

#         # Add product data to processed_products
#         processed_products.append({
#             'id': product.id,
#             'name': product.name,
#             'price': primary_variant.price,
#             'case_color': primary_variant.case_color,
#             'dial_color': primary_variant.dial_color,
#             'primary_image_url': primary_image_url,
#             'dial_colors': [variant.dial_color for variant in product.variants.all()],
#             'created_at': product.created_at,  # Include for sorting by 'newest_first'
            
#         })

#     # Sort the processed products based on the `sort_by` parameter
#     if sort_by == 'price_low_to_high':
#         processed_products.sort(key=lambda x: x['price'])
#     elif sort_by == 'price_high_to_low':
#         processed_products.sort(key=lambda x: x['price'], reverse=True)
#     elif sort_by == 'newest_first':
#         processed_products.sort(key=lambda x: x['created_at'], reverse=True)
#     elif sort_by == 'a_to_z':  # Sort by name A-Z
#         processed_products.sort(key=lambda x: x['name'].lower())
#     elif sort_by == 'z_to_a':  # Sort by name Z-A
#         processed_products.sort(key=lambda x: x['name'].lower(), reverse=True)

#     # Return JSON response for AJAX requests
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse({'products': processed_products})

#     # Render the template with products and filters for non-AJAX requests
#     context = {
#         'brands': brands,
#         'categories': categories,
#         'products': processed_products,
#     }
#     return render(request, "home.html", context)

from django.db.models import Q
from datetime import date
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from category.models import Category
from product.models import Product, ProductVariant
from offer_management.models import Offer
from decimal import Decimal

@login_required
def home_view(request):
    # Fetch categories and brands that are listed
    categories = Category.objects.filter(is_listed=True)
    brands = Brand.objects.filter(is_listed=True)

    # Get the sort_by query parameter
    sort_by = request.GET.get('sort_by')

    # Start with all products
    products = Product.objects.prefetch_related('variants__images')

    # Initialize a list to hold processed products
    processed_products = []

    for product in products:
        # Get the first (primary) variant for sorting and display
        primary_variant = product.variants.first()
        if not primary_variant:
            continue

        # Get the primary image
        primary_image = primary_variant.images.filter(is_primary=True).first()
        primary_image_url = primary_image.image.url if primary_image else None

        # Calculate the discounted price for the primary variant
        today = date.today()
        category_offers = Offer.objects.filter(
            offer_type='category',
            category=product.category,
            end_date__gte=today
        ).order_by('-discount')

        product_offers = Offer.objects.filter(
            offer_type='product',
            product=product,
            end_date__gte=today
        ).order_by('-discount')

        category_discount = category_offers.first().discount if category_offers.exists() else Decimal('0')
        product_discount = product_offers.first().discount if product_offers.exists() else Decimal('0')

        highest_discount = max(category_discount, product_discount)
        discounted_price = primary_variant.price * (1 - (highest_discount / Decimal('100')))

        # Add product data to processed_products
        processed_products.append({
            'id': product.id,
            'name': product.name,
            'price': primary_variant.price,
            'discounted_price': round(discounted_price, 2),  # Round to 2 decimal places
            'offer_discount':highest_discount,
            'case_color': primary_variant.case_color,
            'dial_color': primary_variant.dial_color,
            'primary_image_url': primary_image_url,
            'dial_colors': [variant.dial_color for variant in product.variants.all()],
            'created_at': product.created_at,  # Include for sorting by 'newest_first'
        })

    # Sort the processed products based on the `sort_by` parameter
    if sort_by == 'price_low_to_high':
        processed_products.sort(key=lambda x: x['discounted_price'])
    elif sort_by == 'price_high_to_low':
        processed_products.sort(key=lambda x: x['discounted_price'], reverse=True)
    elif sort_by == 'newest_first':
        processed_products.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'a_to_z':  # Sort by name A-Z
        processed_products.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'z_to_a':  # Sort by name Z-A
        processed_products.sort(key=lambda x: x['name'].lower(), reverse=True)

    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'products': processed_products})

    # Render the template with products and filters for non-AJAX requests
    context = {
        'brands': brands,
        'categories': categories,
        'products': processed_products,
    }
    return render(request, "home.html", context)


@never_cache
def logout_view(request):
    logout(request)
    request.session.flush()  # Remove all session data
    request.session.clear_expired()
    messages.success(request, "You have been logged out.")
    return redirect('login')

@user_passes_test(lambda u: u.is_staff)
def block_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request,'blocked successfully')
    return redirect("admin_dashboard")

@user_passes_test(lambda u: u.is_staff)
def unblock_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request,'unblocked successfully')
    return redirect("admin_dashboard")




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminlogin(request):
    if request.user.is_authenticated and request.user.is_admin:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)

        if user is not None:
            if user.is_admin: 
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You are not authorized as an admin.')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'adminlogin.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)  
def adminlogout(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('adminlogin')




