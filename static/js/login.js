$( function() {
    var displayed = false;
    // instead of using normal notifications, we have a sticky one at the top that can not be closed nor stacked.
    $("#loginbutton").click(function(){
        event.preventDefault();
        var Email = $("#email").val();
        var Password = $("#password").val();
        $.post("/logincheck", {Email: Email, Password: Password}, function(valid){
            if (valid=="Match"){ // if a succesfull login, move to households page.
                window.location = "/households";
            }
            else if(displayed==false){
                // if a notification is not being displayed, display it.
                displayed = true;
                var header = document.querySelector('.header');
                header.insertAdjacentHTML("afterend", '<div class="notificationRed">Email / Password combination incorrect!</div>')
            }
          });
      }); 
}); 
