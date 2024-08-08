function updateProducts(response){
  console.log("called product grid update");
  console.log(response.data);
  var $container = $('.product-grid');

  for (var i = 0; i < response.data.results.length; i++) {
    var productTag = '<div class="grid-product">';
    var imageUrl = response.data.results[i].svg;
    if (imageUrl === "" || imageUrl === null || imageUrl === undefined || imageUrl === "null") {
      imageUrl = "https://imgur.com/SC1jz9L.jpg";
    }
    else {
      imageUrl = imageUrl.replace("%", "%25");
      imageUrl = imageUrl.replace("#", "%23");
      imageUrl = imageUrl.replace("<", "%3C");
      imageUrl = imageUrl.replace(">", "%3E");
      
      imageUrl = "data:image/svg+xml," + imageUrl;
    }
    var category = '<div class="cat-name"><h5>'+ response.data.results[i].category +'</h5></div>';
    var image = '<div class="img-name" style="background-image: url(' + imageUrl + ')">' + '<h4>' + response.data.results[i].name + '</h4></div>';
    var details = '<p class="price">' + response.data.results[i].price + '<button name='+ response.data.results[i].name +' id='+ response.data.results[i].id +' class="like-product">Like <i class="fa fa-lg fa-heart"></i></button> <button class="add-to-cart js-add-to-cart btn">Add</button></p>';
    var tags = '<p class="tags">';
    for (var j = 0; j < response.data.results[i].tags.length; j++) {
      tags += response.data.results[i].tags[j];
      if(j < response.data.results[i].tags.length - 1) {
        tags += ", ";
      }
    }
    tags += '</p></div>';
    
    $container.append(productTag + category + image + details + tags);
    
  }

  $("#copilot-chat").text(response.data.message);
}

(function($){
  
  $(document).ready(function() {

    $(document).on('click', '.like-product', function(event){
        event.stopPropagation();
        event.stopImmediatePropagation();
        console.log("Like Product triggered");
        console.log(event); 
        $("#likedProducts").append(new Option(event.currentTarget.name, event.currentTarget.id));
    });

    $("#your-likes").on('click', function(event){
        console.log(event);
        productIds = [];

        $("#likedProducts > option").each(function() {
            productIds.push(this.value);
        });
        console.log("asking for recommendation for the following products:");
        console.log(productIds);

        axios.post("/recommend", {
          ids: productIds
        })
        .then((response) => {
            console.log(response);   
            updateProducts(response);
        })
        .then((error) => console.log(error));
      
    });



    $("#search").bind("enterKey",function(e){
      console.log("Enter key pressed"); 
      $(".product-grid").empty();
      if($("#search").val() === "") {
        return;
      }
        axios.post("/query", {
          query: $("#search").val(),
          history: "Fix my bugs"
        })
        .then((response) => {
            console.log(response.data);                                 
            
            updateProducts(response);

          })
        .then((error) => console.log(error));
        });
      $('#search').keyup(function(e){
      if(e.keyCode == 13)
      {
        $(this).trigger("enterKey");
        console.log("Enter key pressed");
      }
    });   

    $("#search").trigger("enterKey");

    // Initialize Isotope
    var $container = $('.product-grid');

    // Add to cart notification.
    var $addToCart = $('.js-add-to-cart');
    var performNotification = function() {
      $('.your-cart').addClass('have-items');
      $('.notifications').removeClass('fadeOut').addClass('fadeInLeft');
      setTimeout( function(){
        $('.notifications').removeClass('fadeInLeft').addClass('fadeOut');
      }, 3000 );
    };
    $addToCart.on( 'click', performNotification );

    // Cart Slide Down
    var $cartToggle = $('.js-toggle-cart');
    var performCartToggle = function() {
      $('.cart').toggleClass('show-cart');
    };
    $cartToggle.on( 'click', performCartToggle );

  }); // Document Ready

})(jQuery); // Map jQuery => $