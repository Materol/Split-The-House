$( function() {
    // click event for the add button
    $("#addhousehold").click(function(){
        event.preventDefault();
        var Name = $("#householdname").val();
        $.post("/addhousehold", {HouseholdName: Name}, function(valid){
            // if input is invalid, an error will be displayed thanks to notifications.js
            if(valid=="refresh") window.location = "/households"; // otherwise refresh to update.
          });
      }); 
    // same as above, but for removing.
    $("#removehousehold").click(function(){
    event.preventDefault();
    var id = $("#houseid").val(); 
    $.post("/removehousehold", {HouseID: id}, function(valid){
        if(valid=="refresh") window.location = "/households";
        });
    }); 
}); 
