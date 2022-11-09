$( function() {
    var displayed = false;
    $("#registerbutton").click(function(){
        event.preventDefault();
        var Username = $("#username").val(); // get all data
        var Email = $("#email").val();
        var Password = $("#password").val();
        var RepeatPassword = $("#repeatpassword").val();
        var header = document.querySelector('.header');
        
        if(displayed==true){ // if error displayed already, remove it for new error.
            var notif = document.getElementById('notif');
            notif.remove();
        }
        if (Password!=RepeatPassword){
            displayed = true;
            header.insertAdjacentHTML("afterend", "<div id='notif' class='notificationRed'>Passwords don't match.</div>");
        }
        else{
            $.post("/registercheck", {Username: Username, Email: Email, Password: Password}, function(valid){
                // many options for different error returns.
                if (valid=="Registered"){ // a success, direct to household
                    window.location = "/households";
                }
                else if (valid=="Email"){
                    displayed = true;
                    header.insertAdjacentHTML("afterend", "<div id='notif' class='notificationRed'>Email can't be empty.</div>");
                }
                else if(valid=="EmailDupe"){
                    displayed = true;
                    header.insertAdjacentHTML("afterend", '<div id="notif" class="notificationRed">Email already exists.</div>');
                }
                else if(valid=="Password"){
                    displayed = true;
                    header.insertAdjacentHTML("afterend", '<div id="notif" class="notificationRed">Password must be at least 8 long.</div>');
                }
                else{
                    displayed = true;
                    header.insertAdjacentHTML("afterend", "<div id='notif' class='notificationRed'>Username can't be empty.</div>");
                }
            });
        }
      }); 
}); 
