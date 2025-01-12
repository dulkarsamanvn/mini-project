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
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import JsonResponse
import razorpay
from offer_management.models import Coupon
from wallet.models import Wallet
from django.utils.timezone import now  # Ensure this import exists at the top of your file
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ReturnReason
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from razorpay.errors import BadRequestError, SignatureVerificationError, ServerError
import razorpay
from orders.models import OrderItemReturn
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse

# @login_required
# def checkout(request):
#     try:
#         # Ensure wallet exists
#         try:
#             wallet = Wallet.objects.get(user=request.user)
#         except Wallet.DoesNotExist:
#             wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

#         # Retrieve default address and cart items
#         default_address = Address.objects.filter(user=request.user, is_default=True).first()
#         address = Address.objects.filter(user=request.user)
#         cart_items = CartItem.objects.filter(user=request.user)

#         # Calculate cart total
#         cart_total = sum(
#             item.quantity * (
#                 item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
#             ) for item in cart_items
#         )

#         # Retrieve active coupons
#         coupons = Coupon.objects.filter(is_active=True,is_listed=True)

#         # Retrieve discount from session
#         discount_amount = Decimal(request.session.get('discount_amount', 0.00))
#         final_total = max(cart_total - discount_amount, Decimal('0.00'))

#         context = {
#             'default_address': default_address,
#             'cart_total': cart_total,
#             'address': address,
#             'coupons': coupons,
#             'discount_amount': discount_amount,
#             'final_total': final_total,
#             'wallet_balance': wallet.balance
#         }
#         return render(request, 'checkout.html', context)

#     except Exception as e:
#         messages.error(request, f"An error occurred: {e}")
#         return redirect('cart:cart')


@login_required
def checkout(request):
    try:
        # Check if cart is empty
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart')

        # Check for unlisted products and remove them
        items_to_delete = []
        valid_items = []
        
        for item in cart_items:
            if not item.product_variant.product.is_listed:
                items_to_delete.append(item)
            else:
                valid_items.append(item)

        # If any unlisted items found, delete them and redirect to cart
        if items_to_delete:
            for item in items_to_delete:
                item.delete()
            messages.warning(request, 'Some items were removed from your cart as they are no longer available.')
            return redirect('cart:cart')

        # Ensure wallet exists
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

        # Retrieve default address and addresses
        default_address = Address.objects.filter(user=request.user, is_default=True).first()
        address = Address.objects.filter(user=request.user)

        # Calculate cart total only for valid items
        cart_total = sum(
            item.quantity * (
                item.product_variant.get_discounted_price() 
                if hasattr(item.product_variant, 'get_discounted_price') 
                else item.product_variant.price
            ) for item in valid_items
        )

        # Retrieve active coupons
        coupons = Coupon.objects.filter(is_active=True, is_listed=True)

        # Retrieve discount from session
        discount_amount = Decimal(request.session.get('discount_amount', 0.00))
        final_total = max(cart_total - discount_amount, Decimal('0.00'))

        context = {
            'default_address': default_address,
            'cart_total': cart_total,
            'address': address,
            'coupons': coupons,
            'discount_amount': discount_amount,
            'final_total': final_total,
            'wallet_balance': wallet.balance,
            'cart_items': valid_items  # Use valid items instead of all cart items
        }
        return render(request, 'checkout.html', context)

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('cart:cart')

@csrf_exempt
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code', '').strip()

            if not request.user.is_authenticated:
                return JsonResponse({'error': 'User not authenticated.'}, status=403)

            # Get the cart items for the user
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({'error': 'Your cart is empty.'}, status=400)

            # Calculate the total amount considering existing discounts
            total_amount = sum(
                item.quantity * (
                    item.product_variant.get_discounted_price() 
                    if hasattr(item.product_variant, 'get_discounted_price') 
                    else item.product_variant.price
                ) for item in cart_items
            )

            # Fetch the coupon
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code, 
                    is_active=True, 
                    valid_from__lte=now().date(), 
                    valid_until__gte=now().date()
                )
            except Coupon.DoesNotExist:
                return JsonResponse({'error': 'Invalid or expired coupon.'}, status=400)

            # Calculate discount
            discount_amount = (coupon.discount_percentage / 100) * total_amount

            # Save coupon details in the session
            request.session['coupon_code'] = coupon_code
            request.session['discount_amount'] = float(discount_amount)

            # Apply proportional discount to each item
            for item in cart_items:
                item_total = item.quantity * (
                    item.product_variant.get_discounted_price() 
                    if hasattr(item.product_variant, 'get_discounted_price') 
                    else item.product_variant.price
                )
                proportional_discount = (item_total / total_amount) * discount_amount
                item.applied_discount = proportional_discount
                item.save()

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


# @csrf_exempt
# def apply_coupon(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             coupon_code = data.get('coupon_code', '').strip()

#             # Get the cart items for the user
#             cart_items = CartItem.objects.filter(user=request.user)
#             if not cart_items.exists():
#                 return JsonResponse({'error': 'Your cart is empty.'}, status=400)

#             # Calculate the total amount considering existing discounts
#             total_amount = sum(item.quantity * (
#                 item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
#             ) for item in cart_items)

#             # Fetch the coupon
#             try:
#                 coupon = Coupon.objects.get(code=coupon_code, is_active=True)
#             except Coupon.DoesNotExist:
#                 return JsonResponse({'error': 'Invalid or expired coupon.'}, status=400)

#             # Calculate discount
#             discount_amount = (coupon.discount_percentage / 100) * total_amount

#             # Save coupon details in the session
#             request.session['coupon_code'] = coupon_code
#             request.session['discount_amount'] = float(discount_amount)  # Convert to float for JSON serialization



#             for item in cart_items:
#                 item_total = item.quantity * (
#                     item.product_variant.get_discounted_price() 
#                     if hasattr(item.product_variant, 'get_discounted_price') 
#                     else item.product_variant.price
#                 )
#                 proportional_discount = (item_total / total_amount) * discount_amount
#                 item.applied_discount = proportional_discount
#                 item.save()

#             # Return success response
#             return JsonResponse({
#                 'success': True,
#                 'discount': discount_amount,
#                 'new_total': total_amount - discount_amount
#             })

#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
#     else:
#         return JsonResponse({'error': 'Invalid request method.'}, status=400)


# -------------------before removing unlisted products-------------------------
# @login_required
# def place_order(request):
#     # Retrieve cart items
#     cart_items = CartItem.objects.filter(user=request.user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart:cart')

#     # Retrieve POST data
#     address_id = request.POST.get('address_id')
#     payment_method = request.POST.get('payment_method')
#     if not address_id or not payment_method:
#         messages.error(request, "Please select both address and payment method.")
#         return redirect('orders:checkout')

#     # Get the user's address
#     address = get_object_or_404(Address, id=address_id, user=request.user)

#     # Calculate the original total amount
#     original_total = sum(
#         item.quantity * (
#             item.product_variant.get_discounted_price() if hasattr(item.product_variant, 'get_discounted_price') else item.product_variant.price
#         ) for item in cart_items
#     )

#     # Retrieve and validate the coupon
#     coupon_code = request.session.get('coupon_code')  # Coupon code stored in session
#     coupon = None
#     discount_amount = Decimal(0.00)

#     if coupon_code:
#         try:
#             coupon = Coupon.objects.get(code=coupon_code, is_active=True)
#             discount_amount = (original_total * coupon.discount_percentage) / 100  # Calculate discount amount
#         except Coupon.DoesNotExist:
#             messages.warning(request, "Invalid or expired coupon.")
#             coupon = None  # Reset coupon if invalid

    
#     discounted_total = original_total - discount_amount

#     try:
#         with transaction.atomic():
#             wallet = Wallet.objects.get(user=request.user)

#             if payment_method == 'wallet':
               
#                 if wallet.balance < discounted_total:
#                     messages.error(request, "Insufficient wallet balance. Please select another payment method.")
#                     return redirect('orders:checkout')

              
#                 wallet.debit(discounted_total, description="Order payment using wallet")
            
#             if payment_method=='cod' and discounted_total < 1000:
#                 messages.error(request,"Orders with COD payment must be at least ₹1000.")
#                 return redirect('orders:checkout')

          
#             order = Order.objects.create(
#                 user=request.user,
#                 address=address,
#                 payment_method=payment_method,
#                 order_date=now(),
#                 delivery_charge=Decimal('0.00'),
#                 tax=Decimal('0.00'), 
#                 coupon=coupon  
#             )

            
#             for cart_item in cart_items:
#                 product_variant = cart_item.product_variant
#                 quantity = cart_item.quantity
#                 unit_price = (
#                     product_variant.get_discounted_price() if hasattr(product_variant, 'get_discounted_price') else product_variant.price
#                 )
#                 total_price = unit_price * quantity

#                 if product_variant.quantity < quantity:
#                     raise ValueError(f"Insufficient stock for {product_variant.product.name}.")

               
#                 product_variant.quantity -= quantity
#                 product_variant.save()

                
#                 OrderItem.objects.create(
#                     order=order,
#                     product_variant=product_variant,
#                     quantity=quantity,
#                     unit_price=unit_price,
#                     total_price=total_price
#                 )

#             # Calculate the final total
#             tax_amount = discounted_total * order.tax
#             final_total = discounted_total + tax_amount + order.delivery_charge
#             order.total_amount = final_total.quantize(Decimal('0.01'))
#             order.save()

            
#             cart_items.delete()

            
#             request.session.pop('coupon_code', None)
#             request.session.pop('discount_amount', None)

#             # Handle payment methods
#             if payment_method == 'razorpay':
#                 # Razorpay integration
#                 client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#                 razorpay_order = client.order.create({
#                     "amount": int(order.total_amount * 100),  # Razorpay requires amount in paise
#                     "currency": "INR",
#                     "payment_capture": 1
#                 })
#                 order.razorpay_order_id = razorpay_order['id']
#                 order.save()
#                 return redirect('orders:razorpay_payment', order_id=order.id)

#             elif payment_method == 'cod':
                
#                 messages.success(request, "Order placed successfully!")
#                 return redirect('orders:order_confirmation', order_id=order.id)

#             elif payment_method == 'wallet':
#                 order.order_status='CONFIRMED'
#                 order.save()
#                 messages.success(request, "Order placed successfully using wallet balance!")
#                 return redirect('orders:order_confirmation', order_id=order.id)

#             else:
#                 messages.error(request, "Invalid payment method.")
#                 return redirect('orders:checkout')

#     except ValueError as e:
#         messages.error(request, f"An error occurred: {str(e)}")
#         return redirect('orders:checkout')
#     except Exception as e:
#         messages.error(request, f"An unexpected error occurred: {str(e)}")
#         return redirect('orders:checkout')

# -------------------before removing unlisted products-------------------------

@login_required
def place_order(request):
    # Retrieve cart items
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart')

    # Check for unlisted products before proceeding
    unlisted_items = []
    for item in cart_items:
        if not item.product_variant.product.is_listed:
            unlisted_items.append(item)
    
    # If unlisted items found, delete them and redirect to cart
    if unlisted_items:
        for item in unlisted_items:
            item.delete()
        messages.error(request, "Some items in your cart are no longer available. Please review your cart.")
        return redirect('cart:cart')

    # Retrieve POST data
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method')
    if not address_id or not payment_method:
        messages.error(request, "Please select both address and payment method.")
        return redirect('orders:checkout')

    # Get the user's address
    address = get_object_or_404(Address, id=address_id, user=request.user)

    # Calculate the original total amount (only for listed products)
    original_total = sum(
        item.quantity * (
            item.product_variant.get_discounted_price() 
            if hasattr(item.product_variant, 'get_discounted_price') 
            else item.product_variant.price
        ) for item in cart_items
    )

    # Retrieve and validate the coupon
    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount_amount = Decimal(0.00)

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True, is_listed=True)
            discount_amount = (original_total * coupon.discount_percentage) / 100
        except Coupon.DoesNotExist:
            messages.warning(request, "Invalid or expired coupon.")
            coupon = None

    discounted_total = original_total - discount_amount

    try:
        with transaction.atomic():
            wallet = Wallet.objects.get(user=request.user)

            if payment_method == 'wallet':
                if wallet.balance < discounted_total:
                    messages.error(request, "Insufficient wallet balance. Please select another payment method.")
                    return redirect('orders:checkout')
                wallet.debit(discounted_total, description="Order payment using wallet")
            
            if payment_method == 'cod' and discounted_total < 1000:
                messages.error(request, "Orders with COD payment must be at least ₹1000.")
                return redirect('orders:checkout')

            # Create order
            order = Order.objects.create(
                user=request.user,
                address=address,
                payment_method=payment_method,
                order_date=now(),
                delivery_charge=Decimal('0.00'),
                tax=Decimal('0.00'),
                coupon=coupon
            )

            # Process each cart item
            for cart_item in cart_items:
                product_variant = cart_item.product_variant
                
                # Double-check if product is still listed
                if not product_variant.product.is_listed:
                    raise ValueError(f"{product_variant.product.name} is no longer available.")
                
                quantity = cart_item.quantity
                unit_price = (
                    product_variant.get_discounted_price() 
                    if hasattr(product_variant, 'get_discounted_price') 
                    else product_variant.price
                )
                total_price = unit_price * quantity

                if product_variant.quantity < quantity:
                    raise ValueError(f"Insufficient stock for {product_variant.product.name}.")

                # Update stock
                product_variant.quantity -= quantity
                product_variant.save()

                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product_variant=product_variant,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )

            # Calculate final total
            tax_amount = discounted_total * order.tax
            final_total = discounted_total + tax_amount + order.delivery_charge
            order.total_amount = final_total.quantize(Decimal('0.01'))
            order.save()

            # Clear cart and session data
            cart_items.delete()
            request.session.pop('coupon_code', None)
            request.session.pop('discount_amount', None)

            # Handle payment methods
            if payment_method == 'razorpay':
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    "amount": int(order.total_amount * 100),
                    "currency": "INR",
                    "payment_capture": 1
                })
                order.razorpay_order_id = razorpay_order['id']
                order.save()
                return redirect('orders:razorpay_payment', order_id=order.id)

            elif payment_method == 'cod':
                messages.success(request, "Order placed successfully!")
                return redirect('orders:order_confirmation', order_id=order.id)

            elif payment_method == 'wallet':
                order.order_status = 'CONFIRMED'
                order.save()
                messages.success(request, "Order placed successfully using wallet balance!")
                return redirect('orders:order_confirmation', order_id=order.id)

            else:
                messages.error(request, "Invalid payment method.")
                return redirect('orders:checkout')

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('orders:checkout')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('orders:checkout')







def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # messages.success(request, "Order successfully placed!")
    return render(request, 'order_confirmation.html', {'order': order})





# -------------------------------------------------------------------------------------

def razorpay_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_method != 'razorpay':
        messages.error(request, "Invalid payment method.")
        return redirect('orders:checkout')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        razorpay_order = client.order.fetch(order.razorpay_order_id)
    except razorpay.errors.BadRequestError as e:
        messages.error(request, "Failed to fetch Razorpay order.")
        return redirect('orders:checkout')

    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')

        try:
            # Verify the payment signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })

            # If verification succeeds, update payment and order status
            order.razorpay_payment_status = 'PAID'
            order.order_status = 'CONFIRMED'  # Mark the order as confirmed after payment
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.save()

            # Empty the cart
            CartItem.objects.filter(user=request.user).delete()

            messages.success(request, "Payment successful! Order confirmed.")
            return redirect('orders:order_confirmation', order_id=order.id)
        except razorpay.errors.SignatureVerificationError:
            # Handle failed verification
            order.razorpay_payment_status = 'FAILED'
            order.order_status = 'PAYMENT_PENDING'  # Set the order status to payment pending
            order.save()

            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('orders:razorpay_payment', order_id=order.id)

    # Update order status if payment status is not "PAID"
    if order.razorpay_payment_status != 'PAID':
        order.order_status = 'PAYMENT_PENDING'
        order.save()

    # Render the payment page for GET requests
    return render(request, 'razorpay_payment.html', {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_amount': razorpay_order['amount'],
        'razorpay_currency': razorpay_order['currency'],
    })


# -------------------------------------------------------------


@login_required(login_url= 'login')
def orders_list(request):
    orders=Order.objects.filter(user=request.user).order_by('-order_date')
    reasons = ReturnReason.objects.all()
    return render(request,'orders_list.html',{'orders':orders,'reasons':reasons})


@login_required
def order_items(request,order_id):
    order=get_object_or_404(Order,id=order_id,user=request.user)
    order_items = OrderItem.objects.filter(order=order).select_related('product_variant__product').prefetch_related(
        Prefetch('product_variant__images', queryset=ProductVariantImage.objects.filter(is_primary=True), to_attr='primary_images'))
    return render(request,'order_items.html',{'order':order,'order_items':order_items})





logger = logging.getLogger(__name__)

@login_required
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Check if the order can be canceled
        if order.order_status in ['SHIPPED', 'DELIVERED']:
            messages.error(request, "This order cannot be canceled as it has already been processed.")
            return redirect('orders:orders_list')
        
        refund_processed=False

        # Refund logic
        if order.payment_method in ['razorpay', 'wallet']:
            wallet = Wallet.objects.get(user=request.user)
            
            # Refund for Razorpay payments
            if order.payment_method == 'razorpay':
                if order.razorpay_payment_id:
                    # Assuming you have a Razorpay client setup
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    try:
                        client.payment.refund(order.razorpay_payment_id, {
                            "amount": int(order.total_amount * 100)  # Refund amount in paise
                        })
                        logger.info(f"Refund initiated for Razorpay payment ID {order.razorpay_payment_id}")
                        refund_processed=True
                    except Exception as e:
                        logger.error(f"Razorpay refund failed: {str(e)}")
                        messages.error(request, "Razorpay refund failed. Please contact support.")
                        return redirect('orders:orders_list')

            # Refund to wallet
            wallet.credit(order.total_amount, description=f"Refund for canceled order #{order.id}")
            logger.info(f"Wallet credited for canceled order #{order.id}")
            refund_processed=True

        for item in order.items.all(): 
            product_variant = item.product_variant  
            product_variant.quantity += item.quantity
            product_variant.status = 'in_stock' if product_variant.quantity > 0 else 'out_of_stock'
            product_variant.save()

        # Update order status to 'CANCELED'
        order.order_status = 'CANCELED'
        order.save()


        if refund_processed:
            messages.success(request, "Order canceled successfully and refund processed")
        elif order.payment_method=='cod':
            messages.success(request, "Order canceled successfully")

        return redirect('orders:orders_list')

    except Wallet.DoesNotExist:
        logger.error(f"Wallet does not exist for user {request.user.email}")
        messages.error(request, "Wallet not found. Please contact support.")
        return redirect('orders:orders_list')

    except Exception as e:
        logger.error(f"Unexpected error occurred during order cancellation: {str(e)}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('orders:orders_list')





@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-order_date')

    # Pagination
    paginator = Paginator(orders, 7)  
    page = request.GET.get('page')

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:

        orders_page = paginator.page(1)
    except EmptyPage:

        orders_page = paginator.page(paginator.num_pages)

    # Handling the POST request for updating order status
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('order_status')

        try:
            if order_id and new_status and new_status in dict(Order.ORDER_STATUS_CHOICES):
                order = get_object_or_404(Order, id=order_id)

                # Check if the status is being updated to 'CANCELED'
                if new_status == 'CANCELED' and order.order_status != 'CANCELED':
                    with transaction.atomic():
                        # Process refund for Razorpay or Wallet payments
                        if order.payment_method in ['razorpay', 'wallet']:
                            wallet = Wallet.objects.get(user=order.user)

                            # Refund for Razorpay payments
                            if order.payment_method == 'razorpay':
                                if order.razorpay_payment_id:
                                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                                    client.payment.refund(order.razorpay_payment_id, {
                                        "amount": int(order.total_amount * 100)  # Refund amount in paise
                                    })

                            # Refund to Wallet
                            wallet.credit(order.total_amount, description=f"Refund for canceled order #{order.id}")

                        # Update the order status
                        order.order_status = 'CANCELED'
                        order.save()

                elif order.order_status == 'CANCELED' and new_status != 'CANCELED':
                    messages.error(request, f"Order {order_id} is already canceled and cannot be updated.")

                elif order.order_status == 'RETURNED' and new_status != 'RETURNED':
                    messages.error(request, f"Order {order_id} is already Returned and cannot be updated.")
                else:
                    # For other status updates
                    order.order_status = new_status
                    order.save()

                messages.success(request, f"Order {order_id} status updated to {new_status}.")
            else:
                messages.error(request, "Invalid order ID or status.")

        except Wallet.DoesNotExist:
            messages.error(request, "Wallet not found for this user. Please contact support.")
        except Exception as e:
            messages.error(request, f"An error occurred while updating the order: {str(e)}")

    return render(request, 'admin_order_list.html', {'orders': orders_page})




# --------------------------------------group return------------------------------------------------------------


# def return_order(request, order_id):
#     order = get_object_or_404(Order, id=order_id)

#     if order.order_status == 'DELIVERED':  # Only allow return initiation if delivered
#         if request.method == "POST":
#             # Create return reason
#             ReturnReason.objects.create(
#                 order=order,
#                 sizing_issues=bool(request.POST.get('sizing_issues')),
#                 damaged_item=bool(request.POST.get('damaged_item')),
#                 incorrect_order=bool(request.POST.get('incorrect_order')),
#                 delivery_delays=bool(request.POST.get('delivery_delays')),
#                 other_reason=request.POST.get('other_reason', '').strip(),
#                 approved=False,  # Default value on creation
#             )

#             # Update order status to 'RETURN_PENDING'
#             order.order_status = 'RETURN_PENDING'
#             print(order.order_status)
#             order.save()  # Ensure status is saved


#             print(f"Order {order_id} status updated to {order.order_status}")

#             messages.success(request, "Return initiated successfully.")
#             return redirect('orders:orders_list')
#         else:
#             messages.error(request, "Invalid request.")
#             return redirect('orders:orders_list')
#     else:
#         messages.error(request, f"Cannot initiate return for order {order.id}. Status is {order.get_order_status_display()}.")
#         return redirect('orders:orders_list')






# @staff_member_required
# def manage_returns(request):
#     # Fetch the pending and approved return requests
#     pending_returns = ReturnReason.objects.filter(
#         order__order_status__in=['RETURN_PENDING', 'RETURNED'],
#         approved=False
#     ).order_by('-created_at')

#     approved_returns = ReturnReason.objects.filter(
#         order__order_status__in=['RETURN_PENDING', 'RETURNED'],
#         approved=True
#     ).order_by('-created_at')

#     paginator = Paginator(approved_returns, 5)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     return render(request, 'manage_returns.html', {
#         'pending_returns': pending_returns,
#         'page_obj': page_obj,
#     })




# @staff_member_required
# def approve_return(request, return_id):
#     # Fetch the return request
#     return_request = get_object_or_404(ReturnReason, id=return_id)
#     order = return_request.order

#     # Credit the amount back to the user's wallet
#     try:
#         wallet = Wallet.objects.get(user=order.user)
#         wallet.credit(order.total_amount, description=f"Refund for returned order #{order.id}")
#     except Wallet.DoesNotExist:
#         messages.error(request, f"No wallet found for user associated with order #{order.id}.")
#         return redirect('orders:manage_returns')

#     # Restock the quantities of ordered items
#     for item in order.items.all(): 
#         product_variant = item.product_variant  
#         product_variant.quantity += item.quantity
#         product_variant.status = 'in_stock' if product_variant.quantity > 0 else 'out_of_stock'
#         product_variant.save()

#     # Update the return request to approved
#     return_request.approved = True
#     return_request.save()

#     # Update the order status to "RETURNED"
#     order.order_status = "RETURNED"
#     order.save()

#     messages.success(request, "Return request approved successfully.")
#     return redirect('orders:manage_returns')

# --------------------------------------------------------------------------------------



@csrf_exempt
@login_required
def return_order_item(request, order_item_id):
    if request.method == "POST":
        
        order_item = get_object_or_404(OrderItem, id=order_item_id)

       
        if hasattr(order_item, 'order_item_return'):
            messages.error(request, "A return request already exists for this item.")
            return redirect('orders:order_items', order_id=order_item.order.id)  # Redirect back to the order items page

        
        sizing_issues = request.POST.get('sizing_issues', 'off') == 'on'
        damaged_item = request.POST.get('damaged_item', 'off') == 'on'
        incorrect_order = request.POST.get('incorrect_order', 'off') == 'on'
        delivery_delays = request.POST.get('delivery_delays', 'off') == 'on'
        other_reason = request.POST.get('other_reason', '')

       
        OrderItemReturn.objects.create(
            order_item=order_item,
            sizing_issues=sizing_issues,
            damaged_item=damaged_item,
            incorrect_order=incorrect_order,
            delivery_delays=delivery_delays,
            other_reason=other_reason,
        )

        
        order_item.status = "RETURN_PENDING"
        order_item.save()

        messages.success(request, "Return initiated successfully.")
        return redirect('orders:order_items', order_id=order_item.order.id)  # Redirect back to the order items page

    messages.error(request, "Invalid request method.")
    return redirect('orders:order_items', order_id=order_item.order.id)



@staff_member_required
def manage_item_returns(request):
    
    pending_returns = OrderItemReturn.objects.filter(approved=False).order_by('-created_at')
    approved_returns = OrderItemReturn.objects.filter(approved=True).order_by('-created_at')

    
    pending_paginator = Paginator(pending_returns, 5)  
    pending_page_number = request.GET.get('pending_page')
    pending_page_obj = pending_paginator.get_page(pending_page_number)

    
    approved_paginator = Paginator(approved_returns, 5)
    approved_page_number = request.GET.get('approved_page')
    approved_page_obj = approved_paginator.get_page(approved_page_number)

    return render(request, 'manage_returns.html', {
        'pending_returns': pending_page_obj,
        'approved_returns': approved_page_obj,
    })


@staff_member_required
def approve_return_item(request, return_id):
    
    order_item_return = get_object_or_404(OrderItemReturn, id=return_id)
    order_item = order_item_return.order_item
    order = order_item.order

  
    total_order_price_before_discount = sum(item.total_price for item in order.items.all())
    discount_factor = order.total_amount / total_order_price_before_discount if total_order_price_before_discount > 0 else 1
    refund_amount = order_item.total_price * discount_factor

    try:
        
        wallet = Wallet.objects.get(user=order.user)
        wallet.credit(refund_amount, description=f"Refund for returned item #{order_item.id}")
    except Wallet.DoesNotExist:
        messages.error(request, f"Wallet not found for user associated with order #{order.id}.")
        return redirect('orders:manage_returns')

    
    product_variant = order_item.product_variant
    product_variant.quantity += order_item.quantity
    product_variant.status = 'in_stock' if product_variant.quantity > 0 else 'out_of_stock'
    product_variant.save()

   
    order_item_return.approved = True
    order_item_return.refunded_amount = refund_amount
    order_item_return.save()

    order_item.status = "RETURNED"
    order_item.save()

    messages.success(request, f"Return approved for item {order_item.product_variant.product.name}.")
    return redirect('orders:manage_returns')




# ------invoice download-------------------------------


def generate_invoice(request,order_id):
    order=Order.objects.get(id=order_id)
    
    
    buffer=BytesIO()
    p=canvas.Canvas(buffer)

    p.drawString(100, 800, f"Invoice for Order #{order.id}")
    p.drawString(100, 780, f"Customer: {order.address.name}")
    p.drawString(100, 760, f"Address: {order.address.address_line1},{order.address.city},{order.address.state}-{order.address.postal_code}")
    p.drawString(100, 740, f"phone:{order.address.phone}")
    p.drawString(100, 720, f"Date: {order.order_date}")
    p.drawString(100, 700, "Items:")

    y = 680
    for item in order.items.all():
        p.drawString(100, y, f"{item.product_variant} - {item.quantity} x {item.unit_price}")
        y -= 20

    p.drawString(100, y - 20, f"Total: {order.total_amount}")

    # Finalize and close the PDF
    p.showPage()
    p.save()

    # Return the PDF as a response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response






# ------------------------------------
@csrf_exempt
def remove_coupon(request):
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'User not authenticated.'}, status=403)

            # Get the cart items for the user
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({'error': 'Your cart is empty.'}, status=400)

            # Calculate the total amount without any coupon discount
            total_amount = sum(
                item.quantity * (
                    item.product_variant.get_discounted_price() 
                    if hasattr(item.product_variant, 'get_discounted_price') 
                    else item.product_variant.price
                ) for item in cart_items
            )

            # Remove coupon from session
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            if 'discount_amount' in request.session:
                del request.session['discount_amount']

            # Remove applied discounts from cart items
            for item in cart_items:
                item.applied_discount = 0
                item.save()

            # Return success response with new total
            return JsonResponse({
                'success': True,
                'new_total': total_amount
            })

        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)
    else:
        return JsonResponse({
            'error': 'Invalid request method.'
        }, status=400)
# ------------------------------------