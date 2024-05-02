from django.urls import path, include
from core.views import index, product_list_view, WishlistPage, save_checkout_info, add_to_wishlist, checkout, customer_dashboard, category_list_view, category_product_list_view, vendor_list_view, vendor_detail_view, product_detail_view, tag_list, ajax_add_review, search_view, filter_product, add_to_cart, cart_view, delete_from_cart_view, update_from_cart, payment_completed_view, payment_failed_view, order_detail, make_address_default, remove_wishlist, contact, ajax_contact

app_name = 'core'

urlpatterns = [
    #Homepage
    path("", index, name='index'),
    path('products/', product_list_view, name='product-list'),
    path('product/<pid>/', product_detail_view, name='product-detail'),


    #Category
    path('category/', category_list_view, name='category-list'),
    path('category/<cid>/', category_product_list_view, name='category-product-list'), 

    #Vendor
    path('vendors/', vendor_list_view, name='vendor-list'),
    path('vendor/<vid>', vendor_detail_view, name='vendor-detail'),

    #tags
    path('products/tag/<slug:tag_slug>', tag_list, name='tags'),

    #add review
    path('ajax-add-review/<int:pid>/', ajax_add_review, name="ajax-add-review"),

    #search 
    path('search/', search_view, name="search"),

    #filter 
    path('filter-product/', filter_product, name="filter-product/"),

    #add to cart 
    path('add-to-cart/', add_to_cart, name="add-to-cart/"),


    #Cart page url
    path('cart', cart_view, name="cart"),

    #Delete from cart
    path('delete-from-cart', delete_from_cart_view, name="delete-from-cart"),

    #update from cart
    path('update-cart', update_from_cart, name="update-cart"),


    #Checkout URL
    path('checkout/<oid>/', checkout, name="checkout"),

    #paypal url
    path("paypal/", include('paypal.standard.ipn.urls')),


    #payment successfull and failed screens
    path("payment-completed/", payment_completed_view, name="payment-completed"),
    path("payment-failed/", payment_failed_view, name="payment-failed"),


    #Dashboard URL
    path('dashboard/', customer_dashboard, name="dashboard"),

    #Order_Details URL
    path('dashboard/order/<int:id>', order_detail, name="order-detail"),

    #Make address default
    path('make-default-address', make_address_default, name="make-default-address"),

    #Adding to wishlist
    path('add-to-wishlist', add_to_wishlist, name="add-to-wishlist"),
    path('wishlist/', WishlistPage, name='wishlist'),

    #Removing from wishlist
    path('remove-from-wishlist/', remove_wishlist, name='remove-from-wishlist'),

    #Removing from wishlist
    path('contact/', contact, name='contact'),

    #Sending to contact form
    path('ajax-contact-form/', ajax_contact, name='ajax-contact-form'),

    #New Routes
    path('save_checkout_info', save_checkout_info, name='save_checkout_info')
]
