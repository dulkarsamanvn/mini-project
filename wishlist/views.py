from django.contrib import messages
from django.shortcuts import render, get_object_or_404,redirect
from product.models import Product
from . models import Wishlist
from django.http import JsonResponse
# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Wishlist
from product.models import Product, ProductVariant
from cart.models import CartItem
from cart.views import add_to_cart
from django.contrib.auth.decorators import login_required




@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the product already exists in the wishlist
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        message = "Product is already in your wishlist!"
        success = False
    else:
        message = "Product added to wishlist"
        success = True

    return JsonResponse({'success': success, 'message': message})

# ----------------------before removing unlisted products------------------------------
# @login_required(login_url= 'login')
# def view_wishlist(request):
#     wishlist_items = Wishlist.objects.filter(user=request.user)
    
#     # Check if variants exist for each product and pass them to the template
#     for item in wishlist_items:
#         product = item.product
#         # Use the 'variants' related name instead of 'productvariant_set'
#         if not product.variants.exists():
#             print(f"Product '{product.name}' has no variants.")
#         else:
#             print(f"Product '{product.name}' has variants.")

#     return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

# ----------------------before removing unlisted products------------------------------


@login_required(login_url='login')
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    items_to_delete = []
    valid_items = []

    # Check for unlisted products and validate variants
    for item in wishlist_items:
        product = item.product
        
        # Check if product is listed
        if not product.is_listed:
            items_to_delete.append(item)
            continue
        
        # Check variants only for listed products
        if not product.variants.exists():
            print(f"Product '{product.name}' has no variants.")
        else:
            print(f"Product '{product.name}' has variants.")
            
        valid_items.append(item)

    # Delete unlisted items
    if items_to_delete:
        for item in items_to_delete:
            item.delete()
        messages.warning(request, 'Some items were removed from your wishlist as they are no longer available.')

    context = {
        'wishlist_items': valid_items
    }
    return render(request, 'wishlist.html', context)

@login_required
def remove_from_wishlist(request, product_id):
    try:
        # Ensure the item exists in the user's wishlist
        item = Wishlist.objects.get(user=request.user, product__id=product_id)
        item.delete()
        messages.success(request, 'Item removed from wishlist successfully.')
    except Wishlist.DoesNotExist:
        messages.error(request, 'Item not found in your wishlist.')
    
    return redirect('wishlist:view_wishlist') 


def add_variant_to_cart_from_wishlist(request, variant_id):
    # You can call the Cart app's add_to_cart function here
    # or directly use the logic of that function if needed.
    return add_to_cart(request, variant_id)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from product.models import ProductVariant

def fetch_variant_details(request):
    variant_id = request.GET.get('variant_id')
    if not variant_id:
        return JsonResponse({'error': 'Variant ID is required'}, status=400)

    try:
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # Get the primary image or fallback to the first image
        primary_image = variant.images.filter(is_primary=True).first()
        image_url = primary_image.image.url if primary_image else variant.images.first().image.url

        return JsonResponse({
            'id': variant.id,
            'product_id': variant.product.id,  # Include product_id for frontend targeting
            'price': variant.price,
            'quantity': variant.quantity,
            'status': 'In Stock' if variant.quantity > 0 else 'Out of Stock',
            'image_url': image_url,  # Include the image URL in the response
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
