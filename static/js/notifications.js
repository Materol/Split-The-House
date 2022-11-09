$(document).ready( function() {

    function checkNotifications() {
        $.post("/getnotif", function(html){
            if(html!=""){
                var header = document.querySelector('.header'); 
                header.insertAdjacentHTML("afterend", html); // put notification directly below header.
                $(".closebutton").click(function(){
                    var div = this.parentElement;      // get the whole notification div element
                    div.style.opacity = "0";           // set opacity to nothing (css opacity transition will give it a fading look)
                    setTimeout(function(){ div.style.display = "none"; }, 500); // wait before removing the element 0.5 secs (the time it takes for the css transition fade)
                });
            }    
        });
    }

    checkNotifications();
    var notifInterval = setInterval(checkNotifications, 1000); 
}); 
