$( function() {
    var displayed = false;

    $("#addusertohouse").click(function(){
        event.preventDefault();
        var email = $("#email").val();
        var houseid = $("#houseid").val();
        $.post("/addusertohouse", {HouseholdID: houseid, Email: email}, function(valid){  // just use it to send post request without updating the page.
          });
      }); 

    $("#addbills").click(function(){
        event.preventDefault();
        var users = []
        $(".userid").each(function(){
            var user = this.value;
            if(this.checked){
                users.push(user);  // if a user is checked, we add it to the list to post.
            }
             
        });
        var billName = $("#billname").val();
        var billValue = $("#billvalue").val();
        var houseID = $("#houseid").val();
        var splitBillBox = document.querySelector('#split') // get the checkbox
        splitBill="No";
        if(splitBillBox.checked){ // if ticked, we are splitting the bill.
            splitBill="Yes";
        }
        $.post("/addbill", {HouseID: houseID, SelectedUsers: users, BillCost: billValue, BillName: billName, SplitBill: splitBill}, function(valid){
                if(valid=="refresh"){
                    window.location = "/viewhousehold"; // if updated, refresh page.
                }
            });
    }); 

    $("#removeuser").click(function(){
        event.preventDefault();
        var userid = $("#userid").val();
        var houseid = $("#houseid").val();
        $.post("/removeuser", {UserID: userid, HouseID: houseid}, function(valid){  // just use it to send post request without updating the page.
            if(valid=="refresh"){
                window.location = "/viewhousehold";
            }
          });
      }); 
}); 
