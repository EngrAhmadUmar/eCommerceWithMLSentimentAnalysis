from core.models import Product, Vendor, Category, ProductImages, CartOrder, CartOrderItems, ProductReview, Wishlist, Address
from django.db.models import Count, Min, Max
from django.contrib import messages

def default(request):
    categories = Category.objects.all()
    vendors = Vendor.objects.all()

    #filter price of products
    min_max_price = Product.objects.aggregate(Min('price'),Max(
        'price'))

    try:
        wishlist = Wishlist.objects.filter(user=request.user)
    except:
        messages.warning(request, 'You need to login to access your wishlist')
        wishlist = 0



    try:
        address = Address.objects.get(user=request.user)
    except:
        address = None
        
    return {
        'categories': categories,
        'min_max_price': min_max_price,
        'vendors': vendors,
        'address': address,
        'wishlist': wishlist,
    }