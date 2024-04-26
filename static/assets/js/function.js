const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];


//Add reviews
$("#commentForm").submit(function(e){
    e.preventDefault();

    let dt = new Date();
    let time = dt.getDay() + " " + monthNames[dt.getUTCMonth()] + ", " + dt.getFullYear()


    $.ajax({
        data: $(this).serialize(),
        method: $(this).attr('method'),
        url: $(this).attr('action'),
        dataType: 'json',

        success: function(res){
            console.log("saved la");

            if(res.bool == true ){
                $("#review-resp").html('Review Added Successfully.')
                $(".hide-comment-form").hide()
                $(".add-review").hide()

                let _html = '<div class="single-comment justify-content-between d-flex mb-30">'
                    _html += '<div class="user justify-content-between d-flex">'
                    _html += '<div class="thumb text-center">'
                    _html += '<img src="https://static-00.iconduck.com/assets.00/profile-default-icon-2048x2045-u3j7s5nj.png" alt="" />'
                    _html += '<a href="#" class="font-heading text-brand">'+ res.context.user +'</a>'
                    _html += '</div>'

                    _html += '<div class="desc">'
                    _html += '<div class="d-flex justify-content-between mb-10">'
                    _html += '<div class="d-flex align-items-center">'
                    _html += '<span class="font-xs text-muted">' + time + '</span>'
                    _html += '</div>'
                    
                    for (let i = 1; i <= res.context.rating; i++){
                        _html += '<i class="fas fa-star text-warning"> </i>'
                    }

                    _html += '</div>'
                    _html += '<p class="mb-10">'+ res.context.review +'<a href="#" class="reply">Reply</a></p>'

                    _html += '</div>'
                    _html += '</div>'
                    _html += '</div>'
                    $('.comment-list').prepend(_html)
            }
           
        }
    })
})


// Filter Products by Vendor or Category
$(document).ready(function (){
    $(".filter-checkbox, #priceFilterBtn").on("click", function(){
        // console.log('click click click');

        let filter_object = {}

        let min_price = $("#max_price").attr("min")
        let max_price = $("#max_price").val()
        
        filter_object.min_price = min_price;
        filter_object.max_price = max_price;

            
        $('.filter-checkbox').each(function(){
            let filter_value = $(this).val();
            let filter_key = $(this).data('filter');

            // console.log(filter_key);
            // console.log(filter_value);

            filter_object[filter_key] = Array.from(document.querySelectorAll('input[data-filter=' + filter_key + ']:checked')).map(function(element){
                return element.value
            })
        })
        // console.log(filter_object)

        $.ajax({
            url: '/filter-product',
            data: filter_object,
            dataType: 'json',
            beforeSend: function(){
                console.log('trying to filter - try hard');
            },
            success: function(response){
                console.log(response);
                console.log("tryhard lost, it worked");
                $('#filtered-product').html(response.data)
            }
        })
        
    })
    console.log("error2");
    $("#max_price").on("blur", function(){
        let min_price = $(this).attr("min")
        let max_price = $(this).attr("max")
        let current_price = $(this).val()

        console.log(min_price);
        
        console.log(max_price);
        console.log("error1");
        
        console.log(current_price);

        if(current_price < parseInt(min_price) || current_price > parseInt(max_price)){
            min_Price = Math.round(min_price * 100)/100
            max_Price = Math.round(max_price * 100)/100

            alert("Price must be between $" + min_Price + ' and $' + max_Price);
            $(this).val(min_price);
            $('#range').val(min_price)

            $(this).focus()
            return false
            
        }
    })
})


// Add to cart functionality
$(".add-to-cart-btn").on("click", function(){
    let this_val = $(this)
    let index = this_val.attr("data-index")
    let quantity = $(".product-quantity-" +index).val()
    let product_title = $(".product-title-" +index).val()
    let product_id = $(".product-id-" +index).val()
    let product_price = $(".current-product-price-" +index).text()
    let product_pid = $(".product-pid-" +index).val()
    let product_image = $('.product-image-' +index).val()
 
    console.log("quantity", quantity);
    console.log("product title", product_title);
    console.log("product_id", product_id);
    console.log("product price", product_price);
    console.log("this val", this_val);
    console.log("product pid", product_pid);
    console.log("image ", product_image);
    console.log("index", index);

    $.ajax({
        url: '/add-to-cart',
        data: {
            'id': product_id,
            'pid': product_pid,
            'image': product_image,
            'qty': quantity,
            'title': product_title,
            'price': product_price
        },
        dataType: 'json',
        beforeSend: function(){
            console.log("adding product");
        },
        success: function(res){
            this_val.html('✅');
            console.log("added product");

            $(".cart-items-count").text(response.totalcartitems)
        }
    })
})


// Delete Product from cart
$(document).on("click", '.delete-product', function(){
    let product_id = $(this).attr("data-product")
    let this_val = $(this)

    $.ajax({
        url: '/delete-from-cart',
        data:{
            'id': product_id
        },
        dataType: 'json',
        beforeSend: function(){
            this_val.hide()
        },
        success: function(response){
            this_val.show()
            $('.cart-items-count').text(response.totalcartitems)
            $('#cart-list').html(response.data)
        },
    })

})



// Delete Product from cart
$(document).on("click", '.update-product', function(){
    let product_id = $(this).attr("data-product")
    let product_quantity = $('.product-qty-'+product_id).val()
    let this_val = $(this)

    console.log(product_id);

    $.ajax({
        url: '/update-cart',
        data:{
            'id': product_id,
            'qty': product_quantity,
        },
        dataType: 'json',
        beforeSend: function(){
            this_val.hide()
        },
        success: function(response){
            this_val.show()
            $('.cart-items-count').text(response.totalcartitems)
            $('#cart-list').html(response.data)
        },
    })

})


// $("#add-to-cart-btn").on("click", function(){
//     let quantity = $("#product-quantity").val()
//     let product_title = $(".product-title").val()
//     let product_id = $(".product-id").val()
//     let product_price = $("#current-product-price").text()
//     let this_val = $(this)

//     console.log(quantity);
//     console.log(product_title);
//     console.log(product_id);
//     console.log(product_price);
//     console.log(this_val);

//     $.ajax({
//         url: '/add-to-cart',
//         data: {
//             'id': product_id,
//             'qty': quantity,
//             'title': product_title,
//             'price': product_price
//         },
//         dataType: 'json',
//         beforeSend: function(){
//             console.log("adding product");
//         },
//         success: function(res){
//             this_val.html('Item added to cart');
//             console.log("added product");

//             $(".cart-items-count").text(response.totalcartitems)
//         }
//     })
// })
