from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Product, ProductVariant,ProductVariantImage
from brand.models import Brand
from category.models import Category
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.contrib import messages

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_list(request):
    """View to list all products"""
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        movement = request.POST.get('movement')
        
        if name and category_id and brand_id:
            Product.objects.create(
                name=name,
                description=description,
                category_id=category_id,
                brand_id=brand_id,
                movement=movement,
            )
            messages.success(request,'product added successfully')
            return redirect('product:product_list')
        else:
            return HttpResponse("Error: All fields are required.", status=400)
    
    # Pass data for category and brand to populate dropdowns
    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'add_product.html', {'categories': categories, 'brands': brands})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.category_id = request.POST.get('category')
        product.brand_id = request.POST.get('brand')
        product.movement = request.POST.get('movement')
        
        if product.name and product.category_id and product.brand_id:
            product.save()
            messages.success(request,'product updated successfully')
            return redirect('product:product_list')
        else:
            return HttpResponse("Error: All fields are required.", status=400)
    
    # Pass data for category, brand, and product details
    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'edit_product.html', {'product': product, 'categories': categories, 'brands': brands})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_product(request, product_id):
    """Delete a specific product"""
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request,'product deleted successfully')
    return redirect('product:product_list')  # Redirect to the product list after deletion

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def manage_variants(request, product_id):
    """View to manage variants of a product, including adding multiple cropped images."""
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()

    if request.method == "POST":
        # Add new variant
        case_color = request.POST.get('case_color')
        dial_color = request.POST.get('dial_color')
        strap_material = request.POST.get('strap_material')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        status = request.POST.get('status')

        variant = ProductVariant.objects.create(
            product=product,
            case_color=case_color,
            dial_color=dial_color,
            strap_material=strap_material,
            price=price,
            quantity=quantity,
            status=status,
        )

        # Handle multiple image uploads
        primary_image_set = False
        for i in range(5):
            image_file = request.FILES.get(f'image_{i}')
            if image_file:
                    # If this is the first image uploaded, set it as the primary image
                    is_primary = not primary_image_set
                    if is_primary:
                        primary_image_set = True
                    # Create the ProductVariantImage and set its primary status
                    ProductVariantImage.objects.create(variant=variant, image=image_file, is_primary=is_primary)
        
        messages.success(request,'variant added successfully')
        return redirect('product:manage_variants', product_id=product.id)

    return render(request, 'manage_variants.html', {'product': product, 'variants': variants})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_variant(request, variant_id):
    """Delete a specific variant"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id  # Save product ID for redirect
    variant.delete()
    messages.success(request,'variant deleted successfully')
    return redirect('product:manage_variants', product_id=product_id)



# def product_detail(request, product_id):
#     """View to display product details with variants."""
#     product = get_object_or_404(Product, pk=product_id)
#     variants = ProductVariant.objects.filter(product=product).select_related('product')

#     # Get the primary variant and its images
#     primary_variant = variants.first()
#     primary_variant_images = ProductVariantImage.objects.filter(variant=primary_variant)

#     # Collect unique colors for variant selection
#     dial_colors = variants.values('dial_color').distinct()
#     case_colors = variants.values('case_color').distinct()

#     # Handle AJAX request for variant change
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         selected_color = request.GET.get('dial_color')
#         selected_variant = variants.filter(dial_color=selected_color).first()
#         if selected_variant:
#             data = {
#                 'price': selected_variant.price,
#                 'status': selected_variant.get_status_display(),
#                 'quantity': selected_variant.quantity,
#                 'images': [img.image.url for img in ProductVariantImage.objects.filter(variant=selected_variant)],
#             }
#             return JsonResponse(data)

#     context = {
#         'product': product,
#         'primary_variant': primary_variant,
#         'primary_variant_images': primary_variant_images,
#         'variants': variants,
#         'dial_colors': dial_colors,
#         'case_colors': case_colors,
#         'status': primary_variant.get_status_display(),
#         'quantity': primary_variant.quantity,
#     }
#     return render(request, 'product_detail.html', context)



def product_detail(request, product_id):
    """View to display product details with variants."""
    product = get_object_or_404(Product, pk=product_id)
    variants = ProductVariant.objects.filter(product=product).select_related('product')

    # Get the primary variant and its images
    primary_variant = variants.first()
    primary_variant_images = ProductVariantImage.objects.filter(variant=primary_variant)

    # Collect unique colors for variant selection
    dial_colors = variants.values('dial_color').distinct()
    case_colors = variants.values('case_color').distinct()

    # Handle AJAX request for variant change
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        selected_color = request.GET.get('dial_color')
        selected_variant = variants.filter(dial_color=selected_color).first()
        if selected_variant:
            data = {
                'price': selected_variant.price,
                'status': selected_variant.get_status_display(),
                'quantity': selected_variant.quantity,
                'images': [img.image.url for img in ProductVariantImage.objects.filter(variant=selected_variant)],
                'dial_color': selected_variant.dial_color,
                'case_color': selected_variant.case_color,
                'strap_material': selected_variant.strap_material,
            }
            return JsonResponse(data)

    # Prepare data for the Specification tab
    specifications = {
        'Brand': product.brand.name if product.brand else "Unknown",
        'Category': product.category.name if product.category else "Uncategorized",
        'Movement': product.get_movement_display(),
        # 'Dial Color': primary_variant.dial_color,
        'Case Color': primary_variant.case_color,
        'Strap Material': primary_variant.strap_material,
        # 'Status': primary_variant.get_status_display(),
        # 'Quantity': primary_variant.quantity,
    }

    context = {
        'product': product,
        'primary_variant': primary_variant,
        'primary_variant_images': primary_variant_images,
        'variants': variants,
        'dial_colors': dial_colors,
        'case_colors': case_colors,
        'status': primary_variant.get_status_display(),
        'quantity': primary_variant.quantity,
        'specifications': specifications,
        'description': product.description,
    }
    return render(request, 'product_detail.html', context)



