import json
from django.shortcuts import render,get_object_or_404,redirect
from .models import CartItem,ProductVariant
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
# @login_required
# def cart_view(request):
#     cart_items=CartItem.objects.filter(user=request.user)
#     total_amount=sum(item.total_amount for item in cart_items)
#     return render(request, 'cart.html', {'cart_items': cart_items, 'total_amount': total_amount})
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        discounted_price = item.product_variant.get_discounted_price()  # Assuming this method exists in ProductVariant
        final_price = discounted_price if discounted_price < item.product_variant.price else item.product_variant.price
        item.total_amount = item.quantity * final_price  # Recalculate the total amount

    context = {
        'cart_items': cart_items,
        'total_amount': sum(item.total_amount for item in cart_items),
    }
    return render(request, 'cart.html', context)




# -----------------------------------------------------------




# @login_required
# def add_to_cart(request, product_variant_id):
#     try:
#         product_variant = get_object_or_404(ProductVariant, id=product_variant_id)
#     except ValueError:
#         messages.error(request, _("Invalid product variant."))
#         return redirect(reverse('product:product_list'))

#     if product_variant.quantity <= 0:
#         messages.error(request, _("This product is out of stock and cannot be added to the cart."))
#         return redirect(reverse('product:product_detail', args=[product_variant.product.id]))

#     cart_item, created = CartItem.objects.get_or_create(
#         user=request.user,
#         product_variant=product_variant,
#         defaults={'quantity': 1, 'total_amount': product_variant.price}
#     )

#     if not created:
#         if cart_item.quantity + 1 > product_variant.quantity:
#             messages.error(
#                 request, 
#                 _("Cannot add more. Only %(stock)s left in stock.") % {'stock': product_variant.quantity}
#             )
#             return redirect(reverse('product:product_detail', args=[product_variant.product.id]))

#         cart_item.quantity += 1
#         cart_item.total_amount = cart_item.quantity * product_variant.price

#     cart_item.save()
#     messages.success(request, _("Item added to cart successfully!"))
#     return redirect(reverse('cart:cart'))
@login_required
def add_to_cart(request, product_variant_id):
    try:
        product_variant = get_object_or_404(ProductVariant, id=product_variant_id)
    except ValueError:
        messages.error(request, _("Invalid product variant."))
        return redirect(reverse('product:product_list'))

    if product_variant.quantity <= 0:
        messages.error(request, _("This product is out of stock and cannot be added to the cart."))
        return redirect(reverse('product:product_detail', args=[product_variant.product.id]))

    # Determine the price to use (discounted or original)
    discounted_price = product_variant.get_discounted_price()  # Assuming this method exists in ProductVariant
    final_price = discounted_price if discounted_price < product_variant.price else product_variant.price

    # Get or create the cart item
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product_variant=product_variant,
        defaults={'quantity': 1, 'total_amount': final_price}  # Use final_price when creating
    )

    if not created:
        # If the item already exists, check stock and update quantity and total amount
        if cart_item.quantity + 1 > product_variant.quantity:
            messages.error(
                request,
                _("Cannot add more. Only %(stock)s left in stock.") % {'stock': product_variant.quantity}
            )
            return redirect(reverse('product:product_detail', args=[product_variant.product.id]))

        cart_item.quantity += 1
        cart_item.total_amount = cart_item.quantity * final_price  # Recalculate total based on new quantity

    else:
        # Set the correct total amount for the new cart item based on final price
        cart_item.total_amount = cart_item.quantity * final_price

    cart_item.save()
    messages.success(request, _("Item added to cart successfully!"))
    return redirect(reverse('cart:cart'))



def remove_cart_item(request,cart_item_id):
    cart_item=get_object_or_404(CartItem,id=cart_item_id,user=request.user)
    cart_item.delete()
    messages.success(request,"product removed from cart")
    return redirect('cart:cart')


# @csrf_exempt
# def update_cart_item(request):
#     if request.method == 'POST':
#         body = json.loads(request.body)
#         cart_item_id = body.get('cart_item_id')
#         quantity = int(body.get('quantity'))

#         try:
           
            
#             if quantity < 1:
#                 return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
#             if quantity > 5:
#                  return JsonResponse({'error': 'Quantity must be at least 5'}, status=400)
#         except (ValueError, TypeError):
#             return JsonResponse({'error': 'Invalid quantity value'}, status=400)

#         try:
#             cart_item = CartItem.objects.get(id=cart_item_id)
#             cart_item.quantity = quantity
#             cart_item.save()

#             item_total = cart_item.quantity * cart_item.product_variant.price
#             cart_items = CartItem.objects.filter(user=request.user)
#             cart_total = sum(item.quantity * item.product_variant.price for item in cart_items)

#             return JsonResponse({'success': True, 'item_total': item_total, 'cart_total': cart_total}, status=200)
#         except CartItem.DoesNotExist:
#             return JsonResponse({'error': 'Cart item not found'}, status=404)

#     return JsonResponse({'error': 'Invalid request'}, status=400)
@csrf_exempt
def update_cart_item(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            cart_item_id = body.get('cart_item_id')
            quantity = int(body.get('quantity'))

            # Validate quantity
            if quantity < 1:
                return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
            if quantity > 5:
                return JsonResponse({'error': 'Quantity cannot exceed 5'}, status=400)

            # Fetch the cart item
            cart_item = CartItem.objects.get(id=cart_item_id)
            cart_item.quantity = quantity

            # Calculate totals
            original_price = cart_item.product_variant.price
            discounted_price = cart_item.product_variant.get_discounted_price() or original_price
            item_total = original_price * quantity
            discounted_item_total = discounted_price * quantity

            # Save the updated cart item
            cart_item.total_amount = discounted_item_total
            cart_item.save()

            # Calculate cart totals
            cart_items = CartItem.objects.filter(user=request.user)
            cart_total = sum(item.product_variant.price * item.quantity for item in cart_items)
            discounted_cart_total = sum(
                (item.product_variant.get_discounted_price() or item.product_variant.price) * item.quantity 
                for item in cart_items
            )

            # Return the response
            return JsonResponse({
                'success': True,
                'item_total': item_total,
                'discounted_item_total': discounted_item_total,
                'cart_total': cart_total,
                'discounted_cart_total': discounted_cart_total,
            }, status=200)

        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid quantity value'}, status=400)
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)


