from core.models import Product, Vendor, Category, ProductImages, CartOrder, CartOrderItems, ProductReview, Wishlist, Address
from django.db.models import Count, Min, Max

def default(request):
    categories = Category.objects.all()
    vendors = Vendor.objects.all()

    #filter price of products
    min_max_price = Product.objects.aggregate(Min('price'),Max(
        'price'))

    try:
        address = Address.objects.get(user=request.user)
    except:
        address = None
        
    return {
        'categories': categories,
        'min_max_price': min_max_price,
        'vendors': vendors,
        'address': address,
    }