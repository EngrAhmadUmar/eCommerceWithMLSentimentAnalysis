from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from core.models import Product, Vendor, Category, ProductImages, CartOrder, CartOrderItems, ProductReview, Wishlist, Address
from taggit.models import Tag
from django.db.models import Avg
from core.forms import ProductReviewForm
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required


def index(request):
    # product = Product.objects.all().order_by('-id')
    products = Product.objects.filter(product_status="published", featured=True)
    context = {
        "products": products
    }
    return render(request, 'core/index.html', context)

def product_list_view(request):
    products = Product.objects.filter(product_status="published")
    context = {
        "products": products
    }
    return render(request, 'core/product-list.html', context)

def category_list_view(request):
    categories = Category.objects.all()

    context = {
        "categories": categories
    }

    return render(request, 'core/category.html', context)

def category_product_list_view(request, cid):
    category = Category.objects.get(cid=cid)
    products = Product.objects.filter(product_status='published', category=category)

    context = {
        'category': category,
        'products': products
    }

    return render(request, 'core/category-product-list.html', context)


def vendor_list_view(request):
    vendors = Vendor.objects.all()

    context = {
        'vendor': vendors,
    }
    return render(request, 'core/vendor-list.html', context)

def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid=vid)
    products = Product.objects.filter(vendor=vendor, product_status='published')


    context = {
        'vendor': vendor,
        'products': products,
    }
    return render(request, 'core/vendor-detail.html', context)


def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)
    
    #Get all reviews for a product
    reviews = ProductReview.objects.filter(product=product).order_by('-date')

    #Getting average reviews
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))


    #Help us get images
    p_images = product.p_images.all()

    #Product Review Form
    review_form = ProductReviewForm()

    make_review = True

    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False

    context = {
        'product': product,
        'p_images': p_images,
        'make_review': make_review,
        'review_form': review_form,
        'average_rating': average_rating,
        'reviews': reviews,
        'products': products
    }

    return render(request, 'core/product-detail.html', context)

def tag_list(request, tag_slug=None):
    products = Product.objects.filter(product_status='published').order_by('-id')

    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)

        products = products.filter(tags__in=[tag])

    context = {
        'tag': tag,
        'products': products,
    }

    return render(request, 'core/tag.html', context)


def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user

    review = ProductReview.objects.create(
        user = user,
        product = product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))

    return JsonResponse(
        {
            'bool': True,
            'context': context,
            'average_reviews': average_reviews
        }
    )


def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by('-date')

    context = {
        'products': products,
        'query': query,
    }

    return render(request, 'core/search.html', context)


def filter_product(request):
    categories = request.GET.getlist('category[]')
    vendors = request.GET.getlist('vendor[]')

    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status='published').order_by('-date').distinct()
    
    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)

    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct()

    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct()

    context = {
        'products': products
    }

    data = render_to_string('core/asnyc/product-list.html', context)

    return JsonResponse({'data': data})


def add_to_cart(request):
    cart_products = {}
    cart_products[str(request.GET["id"])] = {
        'title': request.GET["title"],
        'price': request.GET["price"],
        'qty': request.GET["qty"],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_products[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_products)
            request.session['cart_data_obj'] = cart_data
    else:
        request.session['cart_data_obj'] = cart_products

    return JsonResponse({'data': request.session['cart_data_obj'], 'totalcartitems':
    len(request.session['cart_data_obj'])})


def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for product_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
            return render(request, "core/cart.html", {'cart_data': request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})
    else:
        messages.warning(request, 'Your cart is empty')
        return redirect('core:index')


def delete_from_cart_view(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for product_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/asnyc/cart-list.html", {'cart_data': request.session['cart_data_obj'], 'totalcartitems':
    len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})

    return JsonResponse({'data': context, 'totalcartitems': len(request.session['cart_data_obj'])})


def update_from_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for product_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/asnyc/cart-list.html", {'cart_data': request.session['cart_data_obj'], 'totalcartitems':
    len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})

    return JsonResponse({'data': context, 'totalcartitems': len(request.session['cart_data_obj'])})


@login_required
def checkout_view(request):

    cart_total_amount = 0
    total_amount = 0
    if 'cart_data_obj' in request.session:
        for product_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])
        
        order = CartOrder.objects.create(
            user=request.user,
            price=total_amount,
        )

        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
            ############ Create Order Items ################
            items = CartOrderItems.objects.create(
                order=order,
                invoice_no='INV-'+str(order.id),
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        




    host = request.get_host()
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': cart_total_amount,
        'item_name': "order-item-number-" + str(order.id),
        'invoice': 'invoice-number-' + str(order.id),
        'currency_code': 'USD',
        'notify_url': 'http://{}{}'.format(host, reverse('core:paypal-ipn')),
        'return_url': 'http://{}{}'.format(host, reverse('core:payment-completed')),
        'cancel_url': 'http://{}{}'.format(host, reverse('core:payment-failed')),
    }

    paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
    return render(request, 'core/checkout.html', {'cart_data':request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount, 'paypal_payment_button': paypal_payment_button},)


csrf_exempt
@login_required
def payment_completed_view(request):
        cart_total_amount = 0
        if 'cart_data_obj' in request.session:
            for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, 'core/payment-completed.html', {'cart_data':request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount})


@csrf_exempt
@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')
