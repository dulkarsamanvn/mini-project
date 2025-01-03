from django.shortcuts import render,redirect,get_object_or_404
from .models import Coupon,Offer
from datetime import datetime
from django.utils.timezone import make_aware
from category.models import Category
from product.models import Product
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core import serializers



# Create your views here.
@staff_member_required
def add_coupon(request):
    if request.method=='POST':
        code=request.POST.get('code')
        discount_percentage=request.POST.get('discount_percentage')
        valid_from=request.POST.get('valid_from')
        valid_until=request.POST.get('valid_until')
        is_active=request.POST.get('is_active') == 'on'

        if code and discount_percentage and valid_from and valid_until:
            Coupon.objects.create(
                code=code,
                discount_percentage=discount_percentage,
                valid_from=valid_from,
                valid_until=valid_until,
                is_active=is_active
            )
            messages.success(request,"coupon added successfully")
            print("Coupon successfully saved!")
            return redirect('offer_management:coupon_list')
    return render(request,'add_coupon.html')

@staff_member_required
def edit_coupon(request,pk):
    coupon=get_object_or_404(Coupon,pk=pk)
    if request.method=="POST":
        coupon.code = request.POST.get('code')
        coupon.discount_percentage = request.POST.get('discount_percentage')
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_until = request.POST.get('valid_until')
        coupon.is_active = request.POST.get('is_active') == 'on'
        coupon.save()
        messages.success(request,"coupon updated successfully")
        return redirect('offer_management:coupon_list')
    return render(request,'edit_coupon.html',{'coupon':coupon})


@staff_member_required
def remove_coupon(request,pk):
    coupon=get_object_or_404(Coupon,pk=pk)
    if request.method=='POST':
        coupon.delete()
        messages.success(request,"coupon deleted successfully")
        return redirect('offer_management:coupon_list')
    
@staff_member_required
def coupon_list(request):
    coupon=Coupon.objects.all().order_by('valid_until')
    return render(request,'coupon_list.html',{'coupon':coupon})



# -------------------------------------------------------------------------------

@staff_member_required
def offer_list(request):
    offers=Offer.objects.all()
    return render(request,'offer_list.html',{'offers':offers})



@staff_member_required
def add_offer(request):
    categories = Category.objects.all()
    products = Product.objects.all() 

    # Serialize the data
    serialized_categories = serializers.serialize('json', categories)
    serialized_products = serializers.serialize('json', products)

    if request.method == "POST":
        name = request.POST.get("name")
        discount = request.POST.get("discount")
        description = request.POST.get("description")
        offer_type = request.POST.get("offer_type")
        selected_id = request.POST.get("selected_id")
        end_date = request.POST.get("end_date")

        if not(name and discount and description and offer_type and selected_id and end_date):
            messages.error(request, 'All fields are required')
            return redirect('offer_management:add_offer')

        offer = Offer(
            name=name,
            discount=discount,
            description=description,
            offer_type=offer_type,
            end_date=end_date,
        )

        if offer_type == "category":
            offer.category_id = selected_id
        elif offer_type == "product":
            offer.product_id = selected_id 

        offer.save()
        messages.success(request, "Offer added successfully")
        return redirect('offer_management:offer_list')

    return render(request, "add_offer.html", {
        "categories": serialized_categories,
        "products": serialized_products
    })



@staff_member_required
def edit_offer(request, pk):
    # Get the offer object to edit
    offer = get_object_or_404(Offer, pk=pk)
    
    categories = Category.objects.all()
    products = Product.objects.all()  # Get all products

    # Serialize categories and products
    serialized_categories = serializers.serialize('json', categories)
    serialized_products = serializers.serialize('json', products)

    if request.method == "POST":
        name = request.POST.get("name")
        discount = request.POST.get("discount")
        description = request.POST.get("description")
        offer_type = request.POST.get("offer_type")
        selected_id = request.POST.get("selected_id")
        end_date = request.POST.get("end_date")

        if not(name and discount and description and offer_type and selected_id and end_date):
            messages.error(request, 'All fields are required')
            return redirect('offer_management:edit_offer', pk=pk)

        offer.name = name
        offer.discount = discount
        offer.description = description
        offer.offer_type = offer_type
        offer.end_date = end_date

        if offer_type == "category":
            offer.category_id = selected_id
            offer.product = None  
        elif offer_type == "product":
            offer.product_id = selected_id  
            offer.category = None  

        offer.save()
        messages.success(request, "Offer updated successfully")
        return redirect('offer_management:offer_list')

    return render(request, "edit_offer.html", {
        "offer": offer,
        "categories": serialized_categories,
        "products": serialized_products
    })



@staff_member_required
def delete_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        offer.delete()
        messages.success(request, "Offer deleted successfully.")
        return redirect('offer_management:offer_list')



