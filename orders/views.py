from decimal import Decimal
import json
from django.shortcuts import render,redirect,get_object_or_404
from cart.models import CartItem
from profile_management.models import Address
from django.contrib import messages
from django.db import transaction
from . models import Order,OrderItem
from django.utils.timezone import now
from product.models import ProductVariant,ProductVariantImage
from django.db.models import Prefetch
from cart.models import CartItem
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import JsonResponse
import razorpay
from offer_management.models import Coupon
from datetime import datetime

# Create your views here.
def checkout(request):
    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    address = Address.objects.filter(user=request.user)
    cart_items = CartItem.objects.filter(user=request.user)

    # Calculate the cart total using discounted prices
    cart_total = sum(item.quantity * (
        item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
    ) for item in cart_items)

    # Retrieve any active coupons
    coupons = Coupon.objects.filter(is_active=True)

    # Include discount details from the session if a coupon has been applied
    discount_amount = request.session.get('discount_amount', 0.00)
    final_total = cart_total - Decimal(discount_amount)

    context = {
        'default_address': default_address,
        'cart_total': cart_total,
        'address': address,
        'coupons': coupons,
        'discount_amount': discount_amount,
        'final_total': final_total
    }
    return render(request, 'checkout.html', context)






# def place_order(request):
#     print("POST Data:", request.POST)
#     # Retrieve the cart from the database
#     cart_items = CartItem.objects.filter(user=request.user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart:cart')

#     # Retrieve POST data
#     address_id = request.POST.get('address_id')
#     payment_method = request.POST.get('payment_method')
#     coupon_code = request.POST.get('coupon_code', '').strip()  # Get the coupon code from POST data

#     print("Address ID:", address_id)
#     print("Payment Method:", payment_method)
#     print("Coupon Code:", coupon_code)

#     if not address_id or not payment_method:
#         messages.error(request, "Please select both address and payment method.")
#         return redirect('orders:checkout')
    
#     address = get_object_or_404(Address, id=address_id, user=request.user)

#     try:
#         with transaction.atomic():
#             # Create the order
#             total_amount = Decimal(0.00)
#             order = Order.objects.create(
#                 user=request.user,
#                 address=address,
#                 payment_method=payment_method,
#                 delivery_charge=Decimal('0.00'),  # Add logic if delivery charge is dynamic
#                 tax=Decimal('0.00'),  # Example tax rate (18%)
#                 order_date=now()
#             )

#             # Process each cart item
#             for cart_item in cart_items:
#                 product_variant = cart_item.product_variant
#                 quantity = cart_item.quantity
#                 unit_price = product_variant.price
#                 total_price = unit_price * quantity

#                 if product_variant.quantity < quantity:
#                     raise ValueError(f"Insufficient stock for {product_variant.product.name}. Available: {product_variant.quantity}")

#                 # Reduce product_variant quantity
#                 product_variant.quantity -= quantity
#                 product_variant.save()

#                 # Create an OrderItem
#                 OrderItem.objects.create(
#                     order=order,
#                     product_variant=product_variant,
#                     quantity=quantity,
#                     unit_price=unit_price,
#                     total_price=total_price
#                 )

#                 # Add to the total order amount
#                 total_amount += total_price

#             # Apply coupon logic
#             discount_amount = Decimal(0.00)
#             if coupon_code:
#                 try:
#                     coupon = Coupon.objects.get(code=coupon_code, is_active=True)
#                     if coupon.is_valid():
#                         order.coupon = coupon
#                         discount_amount = (total_amount * coupon.discount_percentage / 100).quantize(Decimal('0.01'))
#                         total_amount -= discount_amount
#                     else:
#                         messages.error(request, "The coupon code is expired or invalid.")
#                 except Coupon.DoesNotExist:
#                     messages.error(request, "Invalid coupon code.")

#             # Calculate tax and update order total
#             tax_amount = (total_amount * order.tax).quantize(Decimal('0.01'))
#             order.total_amount = (total_amount + tax_amount + order.delivery_charge).quantize(Decimal('0.01'))
#             order.save()

#             # Clear the cart
#             cart_items.delete()

#             # Handle different payment methods
#             if payment_method == 'razorpay':
#                 # Create a Razorpay order for payment
#                 client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#                 razorpay_order = client.order.create({
#                     "amount": int(order.total_amount * 100),
#                     "currency": "INR",
#                     "payment_capture": 1
#                 })
#                 order.razorpay_order_id = razorpay_order['id']
#                 order.save()
#                 return redirect('orders:razorpay_payment', order_id=order.id)

#             elif payment_method == 'cod':
#                 # If Cash on Delivery, just proceed to order confirmation
#                 messages.success(request, "Order successfully placed!")
#                 return redirect('orders:order_confirmation', order_id=order.id)

#             elif payment_method == 'wallet':
#                 messages.error(request, "Wallet payments are not implemented yet.")
#                 return redirect('orders:checkout')

#             else:
#                 messages.error(request, "Invalid payment method.")
#                 return redirect('orders:checkout')

#     except ValueError as e:
#         messages.error(request, f"An error occurred: {str(e)}")
#         return redirect('orders:checkout')
#     except Exception as e:
#         messages.error(request, f"An unexpected error occurred: {str(e)}")
#         return redirect('orders:checkout')




# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# import json
# def apply_coupon(request):
#     if request.method == 'POST':
#         if not request.headers.get('X-CSRFToken'):
#             return JsonResponse({'error': 'CSRF token missing or incorrect'}, status=400)

#         try:
#             data = json.loads(request.body)
#             coupon_code = data.get('coupon_code')  # Make sure the key matches the frontend

#             # Get the cart items for the user
#             cart_items = CartItem.objects.filter(user=request.user)

#             # Get the coupon
#             coupon = Coupon.objects.get(code=coupon_code, is_active=True)

#             # Calculate discount for all cart items
#             total_discount = 0
#             total_amount = sum(item.total_amount for item in cart_items)

#             for item in cart_items:
#                 item_discount = (coupon.discount_percentage / 100) * item.total_amount
#                 item.total_amount -= item_discount
#                 total_discount += item_discount
#                 item.save()  # Save the updated cart item

#             # Calculate new total for the cart after the discount
#             new_total = total_amount - total_discount
#             request.session['discounted_total'] = str(new_total)

#             return JsonResponse({'success': True, 'discount': total_discount, 'new_total': new_total})

#         except Coupon.DoesNotExist:
#             return JsonResponse({'error': 'Invalid or expired coupon'}, status=400)
#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON format'}, status=400)


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
@csrf_exempt
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code', '').strip()

            # Get the cart items for the user
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({'error': 'Your cart is empty.'}, status=400)

            # Calculate the total amount considering existing discounts
            total_amount = sum(item.quantity * (
                item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
            ) for item in cart_items)

            # Fetch the coupon
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            except Coupon.DoesNotExist:
                return JsonResponse({'error': 'Invalid or expired coupon.'}, status=400)

            # Calculate discount
            discount_amount = (coupon.discount_percentage / 100) * total_amount

            # Save coupon details in the session
            request.session['coupon_code'] = coupon_code
            request.session['discount_amount'] = float(discount_amount)  # Convert to float for JSON serialization

            # Return success response
            return JsonResponse({
                'success': True,
                'discount': discount_amount,
                'new_total': total_amount - discount_amount
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)



def place_order(request):
    # Retrieve cart items
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart')

    # Retrieve POST data
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method')
    if not address_id or not payment_method:
        messages.error(request, "Please select both address and payment method.")
        return redirect('orders:checkout')

    # Get the user's address
    address = get_object_or_404(Address, id=address_id, user=request.user)

    # Calculate total amount using discounted prices
    total_amount = sum(item.quantity * (
        item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
    ) for item in cart_items)

    # Apply coupon discount
    discount_amount = Decimal(request.session.get('discount_amount', 0.00))  # Default to 0 if no discount applied

    try:
        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                user=request.user,
                address=address,
                payment_method=payment_method,
                order_date=now(),
                delivery_charge=Decimal('0.00'),  # Update if necessary
                tax=Decimal('0.00'),  # Example tax rate (18%)
            )

            # Process each cart item
            for cart_item in cart_items:
                product_variant = cart_item.product_variant
                quantity = cart_item.quantity
                unit_price = (
                    product_variant.get_discounted_price() if hasattr(product_variant, 'get_discounted_price') else product_variant.price
                )
                total_price = unit_price * quantity

                if product_variant.quantity < quantity:
                    raise ValueError(f"Insufficient stock for {product_variant.product.name}.")

                # Reduce stock
                product_variant.quantity -= quantity
                product_variant.save()

                # Create an order item
                OrderItem.objects.create(
                    order=order,
                    product_variant=product_variant,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )

            # Apply the discount and calculate the final total
            total_amount -= discount_amount
            tax_amount = total_amount * order.tax
            final_total = total_amount + tax_amount + order.delivery_charge
            order.total_amount = final_total.quantize(Decimal('0.01'))
            order.save()

            # Clear the user's cart
            cart_items.delete()

            # Clear session data for the coupon
            request.session.pop('coupon_code', None)
            request.session.pop('discount_amount', None)

            # Handle payment methods
            if payment_method == 'razorpay':
                # Razorpay integration
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    "amount": int(order.total_amount * 100),  # Razorpay requires amount in paise
                    "currency": "INR",
                    "payment_capture": 1
                })
                order.razorpay_order_id = razorpay_order['id']
                order.save()
                return redirect('orders:razorpay_payment', order_id=order.id)

            elif payment_method == 'cod':
                # Cash on Delivery
                messages.success(request, "Order placed successfully!")
                return redirect('orders:order_confirmation', order_id=order.id)

            else:
                messages.error(request, "Invalid payment method.")
                return redirect('orders:checkout')

    except ValueError as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('orders:checkout')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('orders:checkout')







def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # messages.success(request, "Order successfully placed!")
    return render(request, 'order_confirmation.html', {'order': order})
















# -------------------------------------------------------------------------------------

from razorpay.errors import BadRequestError, SignatureVerificationError, ServerError
import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Order
from cart.models import CartItem

def razorpay_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_method != 'razorpay':
        messages.error(request, "Invalid payment method.")
        return redirect('orders:checkout')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        razorpay_order = client.order.fetch(order.razorpay_order_id)
        print("Razorpay order fetched:", razorpay_order)  # Debug log
    except razorpay.errors.BadRequestError as e:
        print(f"Error fetching Razorpay order: {e}")  # Debug log
        messages.error(request, "Failed to fetch Razorpay order.")
        return redirect('orders:checkout')

    # Check if payment is being submitted via POST or simply rendering the page
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')
        print("Razorpay Signature:", request.POST.get('razorpay_signature'))
        
        # Verify the payment signature
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
            
            # Payment verified successfully, update the order status
            order.razorpay_payment_status = 'PAID'
            # order.order_status = 'PENDING'
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.save()

            # Empty the cart after payment success
            CartItem.objects.filter(user=request.user).delete()

            # Return a success message
            messages.success(request, "Payment successful! Order confirmed.")
            return redirect('orders:order_confirmation', order_id=order.id)

        except razorpay.errors.SignatureVerificationError:
            order.razorpay_payment_status='PENDING'
            order.save()
            messages.error(request, "Payment verification failed.")
            return redirect('orders:razorpay_payment',order_id=order.id)
            # return redirect('orders:checkout')

    # If not POST request, render the Razorpay payment page
    return render(request, 'razorpay_payment.html', {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_amount': razorpay_order['amount'],
        'razorpay_currency': razorpay_order['currency'],
    })

# def razorpay_payment(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
    
#     if order.payment_method != 'razorpay':
#         messages.error(request, "Invalid payment method.")
#         return redirect('orders:checkout')

#     client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
#     try:
#         razorpay_order = client.order.fetch(order.razorpay_order_id)
#     except razorpay.errors.BadRequestError:
#         messages.error(request, "Failed to fetch Razorpay order.")
#         return redirect('orders:checkout')

#     if request.method == 'POST':
#         payment_id = request.POST.get('razorpay_payment_id')
#         signature = request.POST.get('razorpay_signature')
        
#         # Verify the payment signature
#         try:
#             client.utility.verify_payment_signature({
#                 'razorpay_order_id': razorpay_order['id'],
#                 'razorpay_payment_id': payment_id,
#                 'razorpay_signature': signature
#             })

#             # Mark order as paid and proceed to confirmation
#             order.payment_status = 'paid'
#             order.save()
#             messages.success(request, "Payment successful. Your order is confirmed.")
#             return redirect('orders:order_confirmation', order_id=order.id)

#         except razorpay.errors.SignatureVerificationError:
#             messages.error(request, "Payment verification failed.")
#             return redirect('orders:checkout')

#     return render(request, 'razorpay_payment.html', {'order': order, 'razorpay_order': razorpay_order})


# -------------------------------------------------------------


@login_required
def orders_list(request):
    orders=Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request,'orders_list.html',{'orders':orders})

def order_items(request,order_id):
    order=get_object_or_404(Order,id=order_id,user=request.user)
    order_items = OrderItem.objects.filter(order=order).select_related('product_variant__product').prefetch_related(
        Prefetch('product_variant__images', queryset=ProductVariantImage.objects.filter(is_primary=True), to_attr='primary_images'))
    return render(request,'order_items.html',{'order':order,'order_items':order_items})


def cancel_order(request, order_id):
    order=get_object_or_404(Order,id=order_id,user=request.user)

    if order.order_status in ['SHIPPED','DELIVERED']:
        messages.error(request,"This order cannot be canceled as it has already been processed.")
        return redirect('orders:orders_list')
    
    order.order_status='CANCELED'
    order.save()

    messages.success(request,"order cancelled successfully")
    return redirect('orders:orders_list')


@staff_member_required
def admin_order_list(request):
    orders=Order.objects.all().order_by('-order_date')

    if request.method=='POST':
        order_id=request.POST.get('order_id')
        new_status=request.POST.get('order_status')
        if order_id and new_status and new_status in dict(Order.ORDER_STATUS_CHOICES):
            order=get_object_or_404(Order,id=order_id)
            if order.order_status=='CANCELED' and new_status != 'CANCELED':
                messages.error(request,f"{order_id} is already cancelled and cannot be updated")
            order.order_status=new_status
            order.save()

            messages.success(request,f"order {order_id} status updated to {new_status}")
        else:
            messages.error(request,"Invalid order Id")
    return render(request,'admin_order_list.html',{'orders':orders})

