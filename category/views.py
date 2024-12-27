from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Category
from django.contrib import messages
from django.db.models import Q

@user_passes_test(lambda u: u.is_staff)  # Ensure only staff users can access
def admin_category_list(request):
    categories = Category.objects.all()
    return render(request, "admin_categories.html", {"categories": categories})

@user_passes_test(lambda u: u.is_staff)
def admin_add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        if not name:
            messages.error(request,"Category name required")
            return redirect("admin_add_category")
        
        if description and len(description)>500:
            messages.error(request,"Description cannot exceed 500 characters")
            return redirect("admin_add_category")

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category with this name already exists.")
        else:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category added successfully.")
        return redirect("admin_category_list")
    return render(request, "admin_add_category.html")

@user_passes_test(lambda u: u.is_staff)
def admin_edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.name = request.POST.get("name").strip()
        category.description = request.POST.get("description").strip()
        if not category.name and category.description:
            messages.error(request,"all fields are required")
            return redirect('admin_edit_category',category_id=category.id)
    
        if Category.objects.filter(Q(name__iexact=category.name) & ~Q(id=category.id)).exists():
            messages.error(request, f"The name is already used by another brand.")
            return redirect('admin_edit_category',category_id=category.id)
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect("admin_category_list")
    return render(request, "admin_edit_category.html", {"category": category})

@user_passes_test(lambda u: u.is_staff)
def admin_toggle_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_listed = not category.is_listed
    category.save()
    if category.is_listed:
        messages.success(request, "Category listed successfully.")
    else:
        messages.success(request, "Category unlisted successfully.")
    return redirect("admin_category_list")


