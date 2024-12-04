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
        full_name = request.POST.get("full_name")
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

# @never_cache
# def verify_otp_view(request):
#     if request.method == "POST":
#         # Check if this is a resend request
#         if request.POST.get('resend_otp') == 'true':
#             # Retrieve email from the session
#             email = request.session.get("email")
#             if not email:
#                 messages.error(request, "Session expired. Please try again.")
#                 return redirect("signup")

#             # Generate and send a new OTP
#             otp = generate_otp()
#             cache.set(email, otp, timeout=300)  # Cache OTP for 5 minutes
#             send_otp(email, otp)

#             messages.success(request, "New OTP sent to your email")
#             return redirect("verify_otp")

#         # Existing OTP verification logic remains the same
#         otp = "".join(request.POST.getlist("otp"))  # Combine all OTP inputs

#         email = request.session.get("email")
#         if not email:
#             messages.error(request, "Session expired. Please try again.")
#             return redirect("signup")


#         cached_otp = cache.get(email)
#         if cached_otp and str(cached_otp) == otp:
#             # Retrieve user data from cache
#             user_data = cache.get(f"user_data_{email}")
#             if user_data:
#                 user = CustomUser.objects.create_user(
#                     email=user_data["email"],
#                     full_name=user_data["full_name"],
#                     phone=user_data["phone"],
#                     password=user_data["password"],
#                 )
#                 user.is_active = True
#                 user.save()

#                 # Clear cache
#                 cache.delete(email)
#                 cache.delete(f"user_data_{email}")

#                 messages.success(request, "Account created successfully")
#                 return redirect("login")
#         else:
#             messages.error(request, "Invalid OTP")
#             return redirect("verify_otp")

#     return render(request, "verify_otp.html")

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




@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home_view(request):
    categories = Category.objects.filter(is_listed=True)
    brands = Brand.objects.filter(is_listed=True)
    products = Product.objects.prefetch_related('variants__images').all()
    processed_products = []

    for product in products:
        first_variant = product.variants.first()
        if first_variant:
            primary_image = first_variant.images.filter(is_primary=True).first()
            primary_image_url = primary_image.image.url if primary_image else None
            processed_products.append({
                'id': product.id,  # Include the product ID
                'name': product.name,
                'price': first_variant.price,
                'case_color': first_variant.case_color,
                'dial_color': first_variant.dial_color,
                'primary_image_url': primary_image_url,
                'other_case_colors': [
                    variant.case_color for variant in product.variants.all()
                ],
                'dial_colors': [
                    variant.dial_color for variant in product.variants.all()
                ],
            })
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




