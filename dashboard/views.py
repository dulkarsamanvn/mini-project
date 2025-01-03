from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from orders.models import Order
from django.db.models import Sum
from django.db.models import F, ExpressionWrapper, DecimalField
from io import BytesIO
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from datetime import datetime, timedelta
import openpyxl
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate
import json

# Create your views here.
# ---------------------------------------------------------------------------------------
def get_date_range(date_range, start_date=None, end_date=None):
    today = timezone.now().date()

    if date_range == 'day':
        start_date = today
        end_date = today
    elif date_range == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif date_range == 'month':
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    elif date_range == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif date_range == 'custom':
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid custom date format. Use YYYY-MM-DD.")
        else:
            # Fallback to today if custom dates are invalid
            start_date = today
            end_date = today
    else:
        start_date = today
        end_date = today

    return start_date, end_date








# ---------------------------------------------------------------------------------------
# def sales_report(request):
#     # Get date range parameter from request
#     date_range = request.GET.get('date_range', 'day')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')

#     # Calculate the date range for filtering
#     start_date, end_date = get_date_range(date_range, start_date, end_date)
#     print("Final Start Date:", start_date)
#     print("Final End Date:", end_date)

#     # Filter orders within the calculated date range (ignore time)
#     orders = Order.objects.filter(order_date__date__range=[start_date, end_date], order_status='DELIVERED')


#     # Annotate orders with discount amount (absolute value)
#     orders = orders.annotate(
#         original_total=Sum(F('items__quantity') * F('items__unit_price')),
#         discount_amount=ExpressionWrapper(
#             F('original_total') * F('coupon__discount_percentage') / 100,
#             output_field=DecimalField(max_digits=10, decimal_places=2)
#         )
#     )

#     paginator=Paginator(orders,10)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     # Calculate sales summary
#     overall_sales_count = orders.count() or 0
#     overall_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
#     overall_discount = orders.aggregate(Sum('coupon__discount_percentage'))['coupon__discount_percentage__sum'] or 0

#     context = {
#         'page_obj': page_obj,
#         'overall_sales_count': overall_sales_count,
#         'overall_order_amount': overall_order_amount,
#         'overall_discount': overall_discount,
#         'date_range': date_range,
#         'start_date': start_date,
#         'end_date': end_date,
#     }

#     return render(request, 'sales_report.html', context)


# ---------------------------------------------------------------------
from orders.models import OrderItem

def sales_report(request):
    # Get date range parameter from request
    date_range = request.GET.get('date_range', 'day')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Calculate the date range for filtering
    start_date, end_date = get_date_range(date_range, start_date, end_date)

    # Filter orders within the calculated date range (ignore time)
    orders = Order.objects.filter(order_date__date__range=[start_date, end_date], order_status='DELIVERED')

    # Group by date and calculate total revenue per day
    daily_revenue = (
        orders.annotate(date=TruncDate('order_date'))
        .values('date')
        .annotate(total_revenue=Sum('total_amount'))
        .order_by('date')
    )

    # Prepare data for the chart
    # Prepare data for the chart
    graph_labels = [entry['date'].strftime('%Y-%m-%d') for entry in daily_revenue]
    graph_data = [float(entry['total_revenue']) for entry in daily_revenue]  # Convert Decimal to float


    # Pagination for orders
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate sales summary
    overall_sales_count = orders.count() or 0
    overall_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    overall_discount = orders.aggregate(Sum('coupon__discount_percentage'))['coupon__discount_percentage__sum'] or 0

    # Top Selling Products
    top_products = (
        OrderItem.objects.filter(order__in=orders)
        .values(product_name=F('product_variant__product__name'))
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

    # Extract names and quantities for the chart
    top_product_names = [item['product_name'] for item in top_products]
    top_product_quantities = [item['total_sold'] for item in top_products]

    # Top Selling Categories
    top_categories = (
        OrderItem.objects.filter(order__in=orders)
        .values(category_name=F('product_variant__product__category__name'))
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

    top_category_names = [item['category_name'] for item in top_categories]
    top_category_quantities = [item['total_sold'] for item in top_categories]

    # Top Selling Brands
    top_brands = (
        OrderItem.objects.filter(order__in=orders)
        .values(brand_name=F('product_variant__product__brand__name'))
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

    top_brand_names = [item['brand_name'] for item in top_brands]
    top_brand_quantities = [item['total_sold'] for item in top_brands]

    # Add top-selling data to the context
    context = {
        'page_obj': page_obj,
        'overall_sales_count': overall_sales_count,
        'overall_order_amount': overall_order_amount,
        'overall_discount': overall_discount,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'graph_labels': json.dumps(graph_labels),  # Pass JSON-encoded labels
        'graph_data': json.dumps(graph_data),      # Pass JSON-encoded data
        'top_product_names': json.dumps(top_product_names),  # Encode as JSON
        'top_product_quantities': json.dumps(top_product_quantities),  # Encode as JSON
        'top_category_names':json.dumps(top_category_names),
        'top_category_quantities':json.dumps(top_category_quantities),
        'top_brand_names': json.dumps(top_brand_names),
        'top_brand_quantities': json.dumps(top_brand_quantities),
    }

    return render(request, 'sales_report.html', context)






def export_sales_report(request, format):
    date_range = request.GET.get('date_range', 'day')
    start_date=request.GET.get('start_date')
    end_date=request.GET.get('end_date')


    start_date, end_date = get_date_range(date_range,start_date,end_date)

    # Fetch filtered orders
    orders = Order.objects.filter(order_date__date__range=[start_date, end_date], order_status='DELIVERED')
    orders = orders.annotate(
        original_total=Sum(F('items__quantity') * F('items__unit_price')),
        discount_amount=ExpressionWrapper(
            F('original_total') * F('coupon__discount_percentage') / 100,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )

    if format == 'pdf':
        return export_pdf(orders)
    elif format == 'excel':
        return export_excel(orders)
    else:
        return HttpResponse("Invalid format", status=400)


def export_pdf(orders):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, "Sales Report")

    y = 750
    for order in orders:
        text = (
            f"Order ID: {order.id}, "
            f"Total: {order.total_amount}, "
            f"Discount: {order.discount_amount}"
        )
        p.drawString(50, y, text)
        y -= 20

    p.save()
    return response


def export_excel(orders):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # Write headers
    headers = ["Order ID", "Total Amount", "Discount Amount"]
    ws.append(headers)

    # Write data
    for order in orders:
        ws.append([order.id, order.total_amount, order.discount_amount])

    wb.save(response)
    return response



