from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Brand
from django.contrib import messages

@user_passes_test(lambda u: u.is_staff)  # Ensure only staff users can access
def admin_brand_list(request):
    brand = Brand.objects.all()
    return render(request, "admin_brand.html", {"brand": brand})

@user_passes_test(lambda u: u.is_staff)
def admin_add_brand(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        if Brand.objects.filter(name=name).exists():
            messages.error(request, "Brand with this name already exists.")
        else:
            brand = Brand.objects.create(name=name, description=description)
            messages.success(request,'Brand added successfully')
            print(f"Brand created: {brand}")  # Debug to ensure it's created
        return redirect("admin_brand_list")
    return render(request, "admin_add_brand.html")

@user_passes_test(lambda u: u.is_staff)
def admin_edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    if request.method == "POST":
        brand.name = request.POST.get("name")
        brand.description = request.POST.get("description")
        brand.save()
        messages.success(request, "Brand updated successfully.")
        return redirect("admin_brand_list")
    return render(request, "admin_edit_brand.html", {"brand": brand})

@user_passes_test(lambda u: u.is_staff)
def admin_toggle_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_listed = not brand.is_listed
    brand.save()
    if brand.is_listed:
        messages.success(request, "Brand listed successfully.")
    else:
        messages.success(request, "Brand unlisted successfully.")
    return redirect("admin_brand_list")