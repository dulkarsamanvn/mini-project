from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Product, ProductVariant,ProductVariantImage
from brand.models import Brand
from category.models import Category
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.contrib import messages
import re
from django.db.models import Q

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_list(request):
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
        if not name:
            messages.error(request, "Product name is required.")
            return redirect('product:add_product')

        if not re.match(r"^[a-zA-Z0-9&\-\s_]+$", name):
            messages.error(request, "Product name can only contain letters, numbers, spaces, '&', '-', and '_'.")
            return redirect('product:add_product')

        if Product.objects.filter(name__iexact=name).exists():
            messages.error(request, "Product with this name already exists.")
            return redirect('product:add_product')

        if len(description) > 1000:
            messages.error(request, "Description cannot exceed 1000 characters.")
            return redirect('product:add_product')
        
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

# @login_required
# @cache_control(no_cache=True, must_revalidate=True, no_store=True)
# def edit_product(request, product_id):
#     product = get_object_or_404(Product, pk=product_id)
    
#     if request.method == 'POST':
#         product.name = request.POST.get('name')
#         product.description = request.POST.get('description')
#         product.category_id = request.POST.get('category')
#         product.brand_id = request.POST.get('brand')
#         product.movement = request.POST.get('movement')
        
#         if product.name and product.category_id and product.brand_id:
#             product.save()
#             messages.success(request,'product updated successfully')
#             return redirect('product:product_list')
#         else:
#             return HttpResponse("Error: All fields are required.", status=400)
    
#     # Pass data for category, brand, and product details
#     categories = Category.objects.all()
#     brands = Brand.objects.all()
#     return render(request, 'edit_product.html', {'product': product, 'categories': categories, 'brands': brands})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        # Trim whitespace from name and description
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        movement = request.POST.get('movement', '')
        
        # Validate non-empty fields
        if not name or not description or not category_id or not brand_id:
            messages.error(request,"all fields are required")
            return redirect('product:edit_product',product_id=product.id)
        
        if '_' in name:
            messages.error(request,"no underscore allowed in name")
            return redirect('product:edit_product', product_id=product.id)
        
        # Check for case-insensitive name uniqueness
        existing_product = Product.objects.filter(Q(name__iexact=name) & ~Q(id=product_id)).first()
        if existing_product:
            messages.error(request,f"the name {name} is already used by another product")
            return redirect('product:product_list')
        
        # Update product attributes if validations pass
        product.name = name
        product.description = description
        product.category_id = category_id
        product.brand_id = brand_id
        product.movement = movement
        
        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('product:product_list')
    
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
        variant_id = request.POST.get('variant_id')
        case_color = request.POST.get('case_color')
        dial_color = request.POST.get('dial_color')
        strap_material = request.POST.get('strap_material')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        status = request.POST.get('status')

        if variant_id:  # Edit existing variant
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                variant.case_color = case_color
                variant.dial_color = dial_color
                variant.strap_material = strap_material
                variant.price = price
                variant.quantity = quantity
                variant.status = status
                variant.save()

                # Handle image updates
                # Delete images marked for deletion
                images_to_delete = request.POST.getlist('delete_images')
                if images_to_delete:
                    ProductVariantImage.objects.filter(id__in=images_to_delete).delete()

                # Add new images
                primary_image_exists = variant.images.filter(is_primary=True).exists()
                for i in range(5):
                    image_file = request.FILES.get(f'image_{i}')
                    if image_file:
                        # If no primary image exists or this is marked as primary
                        is_primary = not primary_image_exists and i == 0
                        if is_primary:
                            primary_image_exists = True
                        ProductVariantImage.objects.create(
                            variant=variant,
                            image=image_file,
                            is_primary=is_primary
                        )

                messages.success(request, 'Variant updated successfully')
            except ProductVariant.DoesNotExist:
                messages.error(request, 'Variant not found')

        else:  # Add new variant
            variant = ProductVariant.objects.create(
                product=product,
                case_color=case_color,
                dial_color=dial_color,
                strap_material=strap_material,
                price=price,
                quantity=quantity,
                status=status,
            )

            # Handle multiple image uploads for new variant
            primary_image_set = False
            for i in range(5):
                image_file = request.FILES.get(f'image_{i}')
                if image_file:
                    # If this is the first image uploaded, set it as primary
                    is_primary = not primary_image_set
                    if is_primary:
                        primary_image_set = True
                    ProductVariantImage.objects.create(
                        variant=variant,
                        image=image_file,
                        is_primary=is_primary
                    )
            
            messages.success(request, 'Variant added successfully')

        return redirect('product:manage_variants', product_id=product.id)

    return render(request, 'manage_variants.html', {
        'product': product,
        'variants': variants
    })

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_variant(request, variant_id):
    """Delete a specific variant"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id  # Save product ID for redirect
    variant.delete()
    messages.success(request,'variant deleted successfully')
    return redirect('product:manage_variants', product_id=product_id)

# @login_required
# def product_detail(request, product_id):
#     """View to display product details with variants."""
#     product = get_object_or_404(Product, pk=product_id)
#     variants = ProductVariant.objects.filter(product=product).select_related('product')
#     # Get the primary variant and its images
#     primary_variant = variants.first()
#     primary_variant_images = ProductVariantImage.objects.filter(variant=primary_variant)

#     # Collect unique colors for variant selection
#     dial_colors = variants.values('id' ,'dial_color').distinct()
#     case_colors = variants.values('id','case_color').distinct()

#     # Handle AJAX request for variant change
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         selected_color = request.GET.get('dial_color')
#         selected_variant = variants.filter(dial_color=selected_color).first()
#         print(selected_variant.id)
#         if selected_variant:
#             data = {
#                 'id': selected_variant.id,
#                 'price': selected_variant.price,
#                 'status': selected_variant.get_status_display(),
#                 'quantity': selected_variant.quantity,
#                 'images': [img.image.url for img in ProductVariantImage.objects.filter(variant=selected_variant)],
#                 'dial_color': selected_variant.dial_color,
#                 'case_color': selected_variant.case_color,
#                 'strap_material': selected_variant.strap_material,
#             }
#             return JsonResponse(data)

#     # Prepare data for the Specification tab
#     specifications = {
#         'Brand': product.brand.name if product.brand else "Unknown",
#         'Category': product.category.name if product.category else "Uncategorized",
#         'Movement': product.get_movement_display(),
#         # 'Dial Color': primary_variant.dial_color,
#         'Case Color': primary_variant.case_color,
#         'Strap Material': primary_variant.strap_material,
#         # 'Status': primary_variant.get_status_display(),
#         # 'Quantity': primary_variant.quantity,
#     }

#     context = {
#     'product': product,
#     'primary_variant': primary_variant,
#     'primary_variant_id': primary_variant.id if primary_variant else None,  # Pass the correct ID conditionally
#     'primary_variant_images': primary_variant_images,
#     'variants': variants,
#     'dial_colors': dial_colors,
#     'case_colors': case_colors,
#     'status': primary_variant.get_status_display() if primary_variant else "",
#     'quantity': primary_variant.quantity if primary_variant else 0,
#     'specifications': specifications,
#     'description': product.description,
#     'price': primary_variant.get_discounted_price() if primary_variant else None,
#     }

#     print('Primary Variant:', primary_variant)
#     print('Primary Variant ID:', primary_variant.id if primary_variant else "No Variant Found")


#     return render(request, 'product_detail.html', context)



@login_required
def product_detail(request, product_id):
    """View to display product details with variants."""
    product = get_object_or_404(Product, pk=product_id)
    variants = ProductVariant.objects.filter(product=product).select_related('product')
    
    # Get the primary variant and its images
    primary_variant = variants.first()
    primary_variant_images = ProductVariantImage.objects.filter(variant=primary_variant)

    # Collect unique colors for variant selection
    dial_colors = variants.values('id', 'dial_color').distinct()
    case_colors = variants.values('id', 'case_color').distinct()

    # Handle AJAX request for variant change
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        selected_color = request.GET.get('dial_color')
        selected_variant = variants.filter(dial_color=selected_color).first()

        if selected_variant:
            # Calculate the discounted price if any offer applies
            discounted_price = selected_variant.get_discounted_price() if selected_variant.get_discounted_price else selected_variant.price

            data = {
                'id': selected_variant.id,
                'price': str(selected_variant.price),  # Original price
                'discounted_price': str(discounted_price),  # Discounted price
                'status': selected_variant.get_status_display(),
                'quantity': selected_variant.quantity,
                'images': [img.image.url for img in ProductVariantImage.objects.filter(variant=selected_variant)],
                'dial_color': selected_variant.dial_color,
                'case_color': selected_variant.case_color,
                'strap_material': selected_variant.strap_material,
            }
            return JsonResponse(data)

    # Get the primary variant price, and calculate its discounted price
    if primary_variant:
        discounted_price = primary_variant.get_discounted_price() if primary_variant.get_discounted_price else primary_variant.price
    else:
        discounted_price = None

    # Prepare data for the Specification tab
    specifications = {
        'Brand': product.brand.name if product.brand else "Unknown",
        'Category': product.category.name if product.category else "Uncategorized",
        'Movement': product.get_movement_display(),
        'Case Color': primary_variant.case_color if primary_variant else "Unknown",
        'Strap Material': primary_variant.strap_material if primary_variant else "Unknown",
    }

    context = {
        'product': product,
        'primary_variant': primary_variant,
        'primary_variant_id': primary_variant.id if primary_variant else None,  # Pass the correct ID conditionally
        'primary_variant_images': primary_variant_images,
        'variants': variants,
        'dial_colors': dial_colors,
        'case_colors': case_colors,
        'status': primary_variant.get_status_display() if primary_variant else "",
        'quantity': primary_variant.quantity if primary_variant else 0,
        'specifications': specifications,
        'description': product.description,
        'price': discounted_price,  # Update price to reflect the discounted price
    }

    return render(request, 'product_detail.html', context)




