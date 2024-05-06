from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from core.models import Product, Vendor, Coupon, Category, ProductImages, CartOrder, CartOrderItems, ProductReview, Wishlist, Address
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
from django.core import serializers
import calendar
from django.db.models.functions import ExtractMonth
from django.db.models import Count
from userauths.models import ContactUs, Profile
import stripe

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
            return render(request, "core/cart.html", {'cart_data': request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount': cart_total_amount})
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


def save_checkout_info(request):
    cart_total_amount = 0
    total_amount = 0

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')

        request.session['full_name'] = full_name
        request.session['email'] = email
        request.session['mobile'] = mobile
        request.session['address'] = address
        request.session['city'] = city
        request.session['state'] = state
        request.session['country'] = country

        if 'cart_data_obj' in request.session:
            for product_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])
            
            order = CartOrder.objects.create(
                user=request.user,
                price=total_amount,
                full_name=full_name,
                email=email,
                phone=mobile,
                address=address,
                city=city,
                state=state,
                country=country
            )

            del request.session['full_name']
            del request.session['email']
            del request.session['mobile']
            del request.session['address']
            del request.session['city']
            del request.session['state']
            del request.session['country']

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
        return redirect('core:checkout', order.oid)
    return redirect('core:checkout', order.oid)





@login_required
def checkout(request, oid):
    order = CartOrder.objects.get(oid=oid)
    order_items = CartOrderItems.objects.filter(order=order)

    if request.method == 'POST':
        code = request.POST.get('code')
        coupon = Coupon.objects.filter(code=code, active=True).first()

        if coupon:
            if coupon in order.coupon.all():
                messages.warning(request, "Coupon used already")
                return redirect('core:checkout', order.oid)
            else:
                discount = order.price * coupon.discount / 100
                order.coupon.add(coupon)
                order.price -= discount
                order.saved += discount
                order.save()
                
                messages.success(request, 'Coupon Activated, Proceed with Checkout')
                return redirect('core:checkout', order.oid)
        else:
            messages.warning(request, 'Incorrect Coupon Code, try again lad')
            return redirect('core:checkout', order.oid)


    context = {
        'order': order,
        'order_items': order_items,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
    }

    return render(request, 'core/checkout.html', context)
    
@csrf_exempt
def create_checkout_session(request, oid):
    order = CartOrder.objects.get(oid=oid)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    checkout_session = stripe.checkout.Session.create(
        customer_email = order.email,
        payment_method_types = ['card'],
        line_items = [
            {
                'price_data':{
                    'currency': 'USD',
                    'product_data': {
                        'name': order.full_name,
                    },
                    'unit_amount': int(order.price * 1000)
                },
                'quantity':1
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse('core:payment-completed', args=[order.oid])) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse('core:payment-failed'))
    )

    order.paid_status = False
    order.stripe_payment_intent = checkout_session['id']
    order.save()

    return JsonResponse({'sessionId': checkout_session.id})

csrf_exempt
@login_required
def payment_completed_view(request, oid):
    order = CartOrder.objects.get(oid=oid)
    if order.paid_status == False:
        order.paid_status = True
        order.save()


    context = {
        'order': order,
    }
    return render(request, 'core/payment-completed.html', context)


@csrf_exempt
@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')


login_required
def customer_dashboard(request):
    address = Address.objects.filter(user=request.user)
    order_list = CartOrder.objects.filter(user=request.user).order_by('id')

    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    profile = Profile.objects.get(user=request.user)

    for d in orders:
        month.append( calendar.month_name[d['month']] )
        total_orders.append(d['count'])

    if request.method == "POST":
        address = request.POST['address']
        mobile = request.POST['mobile']

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
        )

        messages.success(request, 'Address updated successfully')
        return redirect('core:dashboard')

    context = {
        'order_list': order_list,
        'address': address,
        'orders': orders,
        'month': month,
        'total_orders': total_orders,
        'profile': profile,
    }
    return render(request, 'core/dashboard.html', context)



def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItems.objects.filter(order=order)

    context = {
        'order_items': order_items,
    }

    return render(request, 'core/order-detail.html', context)


def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({'boolean': True})

@login_required
def WishlistPage(request):
    try:
        wishlist = Wishlist.objects.filter(user=request.user)
    except:
        wishlist = None
    context = {
    "w": wishlist
    }
    return render(request, 'core/wishlist.html', context)

def add_to_wishlist(request):
    product_id = request.GET['product_id']
    product = Product.objects.get(id=product_id)
    context = {}
    wishlist_count = Wishlist.objects.filter(product=product, user=request.user).count()
    if wishlist_count > 0:
        context = {
        'bool':True
        }
    else:
        new_wishlist = Wishlist.objects.create(
        product=product,
        user=request.user
        )
        context = {
        'bool':True
        }
    return JsonResponse(context)


def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist.objects.filter(user=request.user)

    product = Wishlist.objects.get(id=pid)
    product.delete()

    context = {
        'bool': True,
        'wishlist': wishlist
    }

    wishlist_json = serializers.serialize('json', wishlist)

    data = render_to_string('core/asnyc/wishlist-list.html', context)

    return JsonResponse({'data': data, 'w': wishlist_json})


def contact(request):
    return render(request, 'core/contact.html')

def ajax_contact(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    message = request.GET['message']
    subject = request.GET['subject']

    conct = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        message=message,
        subject=subject,
    )

    context = {
        'bool': True,
        'message': 'Message Sent Successfully'
    }

    return JsonResponse({'data': context})


