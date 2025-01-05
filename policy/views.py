from django.http import JsonResponse
from django.shortcuts import render
from category.models import Category
from product.models import Product,ProductVariant,ProductVariantImage
from brand.models import Brand
from django.db.models import OuterRef, Subquery, Q ,DecimalField
from datetime import date
from offer_management.models import Offer
from django.core.paginator import Paginator
from decimal import Decimal
from wishlist.models import Wishlist
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def repair_and_service(request):
    return render(request,'repair_and_service.html')


@login_required
def stores(request):
    return render(request,'stores.html')


@login_required
def available_brands(request):
    return render(request,'available_brands.html')

@login_required
def mens_page(request):

    categories = Category.objects.filter(is_listed=True)
    brands = Brand.objects.filter(is_listed=True)

    primary_variant_subquery = ProductVariant.objects.filter(
        product=OuterRef('pk'),
        images__is_primary=True
    ).values('id')[:1]

    primary_variant_price_subquery = ProductVariant.objects.filter(
        product=OuterRef('pk'),
        images__is_primary=True
    ).values('price')[:1]

    sort_by = request.GET.get('sort_by')
    query = request.GET.get('q')

   
    products = Product.objects.annotate(
        primary_variant_id=Subquery(primary_variant_subquery),
        primary_variant_price=Subquery(primary_variant_price_subquery, output_field=DecimalField(max_digits=10, decimal_places=2))
    ).filter(primary_variant_id__isnull=False)

 
    men_category = Category.objects.filter(name__iexact='men').first()
    if men_category:
        products = products.filter(category=men_category)


    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    wishlist_items = []
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    
    if sort_by == 'price_low_to_high':
        products = products.order_by('primary_variant_price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-primary_variant_price')
    elif sort_by == 'newest_first':
        products = products.order_by('-created_at')
    elif sort_by == 'a_to_z':
        products = products.order_by('name')
    elif sort_by == 'z_to_a':
        products = products.order_by('-name')

    processed_products = []
    today = date.today()

   
    for product in products:
        primary_variant = ProductVariant.objects.filter(
            id=product.primary_variant_id
        ).select_related('product').prefetch_related('images').first()

        if not primary_variant:
            continue

        
        primary_image = primary_variant.images.filter(is_primary=True).first()
        primary_image_url = primary_image.image.url if primary_image else None

        
        category_discount = Decimal('0')
        product_discount = Decimal('0')

        category_offer = Offer.objects.filter(
            offer_type='category',
            category=product.category,
            end_date__gte=today
        ).order_by('-discount').first()

        product_offer = Offer.objects.filter(
            offer_type='product',
            product=product,
            end_date__gte=today
        ).order_by('-discount').first()

        if category_offer:
            category_discount = category_offer.discount
        if product_offer:
            product_discount = product_offer.discount

        highest_discount = max(category_discount, product_discount)

        
        discounted_price = primary_variant.price * (1 - (highest_discount / Decimal('100')))

        processed_products.append({
            'id': product.id,
            'name': product.name,
            'price': primary_variant.price,
            'discounted_price': round(discounted_price, 2),
            'offer_discount': highest_discount,
            'case_color': primary_variant.case_color,
            'dial_color': primary_variant.dial_color,
            'primary_image_url': primary_image_url,
            'dial_colors': [variant.dial_color for variant in product.variants.all()],
            'created_at': product.created_at,
            'in_wishlist': product.id in wishlist_items
        })

        if sort_by == 'price_low_to_high':
            processed_products.sort(key=lambda x: x['discounted_price'])
        elif sort_by == 'price_high_to_low':
            processed_products.sort(key=lambda x: x['discounted_price'], reverse=True)

    
    paginator = Paginator(processed_products, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Handle AJAX requests for pagination
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'products': list(page_obj),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

   
    context = {
        'products': page_obj,
        'brands': brands,
        'categories': categories,
    }

    return render(request, 'mens_page.html', context)


@login_required
def womens_page(request):
    categories=Category.objects.filter(is_listed=True)
    brands=Brand.objects.filter(is_listed=True)

    primary_variant_subquery=ProductVariant.objects.filter(
        product=OuterRef('pk'),images__is_primary=True
    ).values('id')[:1]

    primary_variant_price_subquery=ProductVariant.objects.filter(product=OuterRef('pk'),images__is_primary=True).values('price')[:1]

    sort_by=request.GET.get('sort_by')
    query=request.GET.get('q')

    products=Product.objects.annotate(
        primary_variant_id=Subquery(primary_variant_subquery),
        primary_variant_price=Subquery(primary_variant_price_subquery,output_field=DecimalField(max_digits=10,decimal_places=2))
    ).filter(primary_variant_id__isnull=False)

    women_category=Category.objects.filter(name__iexact='Women').first()
    if women_category:
        products=products.filter(category=women_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    wishlist_items = []
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    
    if sort_by == 'price_low_to_high':
        products = products.order_by('primary_variant_price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-primary_variant_price')
    elif sort_by == 'newest_first':
        products = products.order_by('-created_at')
    elif sort_by == 'a_to_z':
        products = products.order_by('name')
    elif sort_by == 'z_to_a':
        products = products.order_by('-name')

    processed_products=[]
    today=date.today()

    for product in products:
        primary_variant=ProductVariant.objects.filter(
            id=product.primary_variant_id
        ).select_related('product').prefetch_related('images').first()

        if not primary_variant:
            continue


        primary_image = ProductVariantImage.objects.filter(variant__product=product, is_primary=True).first()
        primary_image_url = primary_image.image.url if primary_image else None


        category_discount=Decimal('0')
        product_discount=Decimal('0')

        category_offer=Offer.objects.filter(
            offer_type='category',
            category=product.category,
            end_date__gte=today
        ).order_by('-discount').first()

        product_offer=Offer.objects.filter(
            offer_type='product',
            product=product,
            end_date__gte=today
        ).order_by('-discount').first()

        if category_offer:
            category_discount=category_offer.discount
        if product_offer:
            product_discount=product_offer.discount

        highest_discount=max(category_discount,product_discount)

        discounted_price = primary_variant.price * (1 - (highest_discount / Decimal('100')))

        processed_products.append(
            {
                'id': product.id,
                'name': product.name,
                'price': primary_variant.price,
                'discounted_price': round(discounted_price, 2),
                'offer_discount': highest_discount,
                'case_color': primary_variant.case_color,
                'dial_color': primary_variant.dial_color,
                'primary_image_url': primary_image_url,
                'dial_colors': [variant.dial_color for variant in product.variants.all()],
                'created_at': product.created_at,
                'in_wishlist': product.id in wishlist_items
            }
        )

        if sort_by == 'price_low_to_high':
            processed_products.sort(key=lambda x: x['discounted_price'])
        elif sort_by == 'price_high_to_low':
            processed_products.sort(key=lambda x: x['discounted_price'], reverse=True)
    

    paginator = Paginator(processed_products, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Handle AJAX requests for pagination
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'products': list(page_obj),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

   
    context = {
        'products': page_obj,
        'brands': brands,
        'categories': categories,
    }

    return render(request, 'womens_page.html', context)




@login_required
def offer_page(request):
    return render(request,'offer_page.html')