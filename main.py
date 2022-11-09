# import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from flask import request
from flask import Flask,redirect
from flask import session
from flask import url_for
from flask import flash
from werkzeug import security
# create the Flask app
from flask import Flask, render_template
app = Flask(__name__)

# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///splithouse.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "superdupersecretpasswordnooneeverwouldknow"

# set up a 'model' for the data you want to store
from db_schema import Notifications, db, User, Households, Tenancy, Bills, dbinit

# init the database so it can connect with our app
db.init_app(app)

# change this to False to avoid resetting the database every time this app is restarted
resetdb = True
if resetdb:
    with app.app_context():
        # drop everything, create all the tables, then put some data into the tables
        db.drop_all()
        db.create_all()
        dbinit()
# i store the links for the header in a list, and access whichever one is relevant.
defaultLinks = [["/","Home"], ["/login", "Login"], ["/registration", "Register"], ["/about", "About"]]
userLinks = [["/","Home"], ["/households", "Households"], ["/requests", "Requests"], ["/about", "About"], ["/logout", "Logout"]]
adminLinks = [["/","Home"], ["/households", "Households"], ["/requests", "Requests"], ["/about", "About"], ["/logout", "Logout"], ["/admin", "Admin"]]

#access to homepage
@app.route('/')
def index():
    links = getLinks() 
    currentpage = "/"
    return render_template('index.html', currentpage=currentpage, links=links)
#access to registration page
@app.route('/registration')
def registration():
    links = getLinks()
    currentpage = "/registration"
    return render_template('registration.html', currentpage=currentpage, links=links)
# a check for a register user, used by .js
@app.route('/registercheck', methods=["POST"])
def registercheck():
    #we allow already logged in users to access the page, if they register it logs them out and logs them to the new user.
    username = request.form["Username"]
    password = request.form["Password"]
    email = request.form["Email"]
    if len(password) < 8: # get their data and verify it with my parameters. Return relevant error.
        return "Password"
    if len(email) == 0:
        return "Email"
    emailDupe = User.query.filter_by(email=email).first()
    if emailDupe != None:
        return "EmailDupe"
    if len(username)==0:
        return "Username"
    session.pop('userid', None)     #otherwise, we remove any current user, add user to database and log them in.
    session.pop('houseid', None)                             
    hashedPassword = security.generate_password_hash(password) 
    newUser = User(username, email, hashedPassword, False)
    db.session.add(newUser)
    db.session.commit()
    session.pop('userid', None)
    session['userid'] = newUser.id
    return "Registered"                #return a successful register.
#access to login page
@app.route('/login')
def login():
    user_id = session.get('userid')
    if(user_id!=None):                  # a check to make sure not logged in already
        return redirect('/userfound')
    currentpage = "/login"
    return render_template('login.html', currentpage=currentpage, links=defaultLinks, nomatch=False)
# checking if a login is valid
@app.route('/logincheck', methods=["POST"])
def logincheck():
    email = request.form["Email"]
    password = request.form["Password"]
    user = User.query.filter_by(email=email).first()
    if user!=None and security.check_password_hash(user.password, password): #check a password hash for the email specified.
        session.pop('userid', None)
        session['userid'] = user.id
        return "Match"
    else: #if no user for email found or password is wrong, we return a general error as to not give away information about existing users.
        return "NoMatch"
# logout page  
@app.route('/logout')
def logout():
    session.pop('userid', None) #removes current session.
    session.pop('houseid', None)
    return redirect('/login')
# an about page to describe me and the website
@app.route('/about')
def about():
    links = getLinks()
    currentpage="/about"
    return render_template('about.html', currentpage=currentpage, links=links)
# access to the page displaying all households.
@app.route('/households')
def households():
    currentpage="/households"
    user_id = session.get('userid')
    if user_id == None:
        return redirect('/nouserfound')
    links = getLinks() #we query the amount of houses this user is eligible to see. (those that link them with a approved tenancy to an approved house)
    houseCount = Households.query.filter(Households.id==Tenancy.household_id, user_id==Tenancy.user_id, Tenancy.approved==True, Households.approved==True).count()
    if houseCount!=0:
        households = Households.query.filter(Households.id==Tenancy.household_id, user_id==Tenancy.user_id, Tenancy.approved==True, Households.approved==True)
        userlists = [] # we get those households and then go through every one, adding a list of users for each house to be used by jinja2.
        for house in households:
            users = [] # get the users that have a tenancy with this house, add them to a list
            users.append(User.query.filter(User.id==Tenancy.user_id, house.id==Tenancy.household_id, Tenancy.approved==True))
            userlists.append(users) # add this to a list of users for each house.
        removables = Households.query.filter(Households.id==Tenancy.household_id, Households.head_tenant==user_id, Tenancy.approved==True, Households.approved==True)
        removablesSize = removables.count() #we get the households and the amount of them that can be removed (e.g. the current user is head tenant of)
        removable = False
        if removablesSize>0: # if some houses are removable, we say removable to know when not to show in jinja2
            removable = True
        nohouses=False # since there are houses, we set it to false so we can display houses.
    else:
        removable=False # otherwise, everything is empty, nothing to display.
        nohouses=True
        households=[]
        removables=[]
        userlists=[]
    return render_template('households.html', residences=households, userlists=userlists, currentpage=currentpage, links=links, nohouses=nohouses, removable=removable, removables=removables)
# for adding a household, by requset.
@app.route('/addhousehold', methods=["POST"])
def addhousehold():
    user_id = session.get('userid')
    user = User.query.filter_by(id=user_id).first()
    if user_id == None:
        return redirect('/nouserfound')
    housename = request.form["HouseholdName"]
    if housename== "": # check whether the name is empty, if so, give a notice to the user about it.
        addNotif(user.id, "Household name invalid.", "Red")
        return ""
    # we set the household to be not approved, unless an admin is adding the house (so they don't need to approve their own)
    approved = False
    if user.admin==True:
        approved = True
    newHouse = Households(housename, user_id, approved) #create house and tenancy between the head tenant.
    db.session.add(newHouse)
    db.session.commit()
    tenancy = Tenancy(user_id, newHouse.id, True)
    db.session.add(tenancy)
    db.session.commit()
    if approved == True:    # distinguished messages between admin add and normal request.
        addNotif(user.id, "Household added.", "Green")
        return "refresh"
    else:
        addNotif(user.id, "Household request sent.", "Blue")
        return ""
# for removing households
@app.route('/removehousehold', methods=["POST"])
def removehousehold():
    user_id = session.get('userid')
    if user_id == None:
        return redirect('/nouserfound')
    houseID = request.form["HouseID"]
    house = Households.query.filter_by(id=houseID).first()
    if house.head_tenant!=user_id:
        addNotif(user_id, "Unexpected error.", "Red") # to make sure a post request by a different user is not allowed, a security issue.
        return ""
    db.session.query(Tenancy).filter(Tenancy.household_id==houseID).delete()
    db.session.commit()
    addNotif(user_id, "Household removed.", "Green")
    return "refresh"
# set the current house that's being viewed
@app.route('/setview', methods=["POST"])
def setview():
    user_id = session.get('userid')
    if user_id == None:
        return redirect('/nouserfound')
    house_id=request.form["Household"]
    validTenancy = Tenancy.query.filter(Tenancy.approved==True, Tenancy.household_id==house_id, Tenancy.user_id==user_id)
    if validTenancy==None:
        addNotif(user_id, "Unexpected error.", "Red") # to make sure a post request by a user not in the house is not allowed.
        return ""
    session.pop('houseid', None)
    session['houseid'] = house_id
    return redirect('/viewhousehold')

@app.route('/viewhousehold')
def viewhousehold():
    user_id = session.get('userid')
    house_id = session.get('houseid')
    currentpage="/viewhousehold"
    links = getLinks()
    if user_id == None:
        return redirect('/nouserfound')
    if house_id == None:
        return render_template('viewhousehold.html', currentpage=currentpage, house=None, users=None, links=links, currentid=user_id, bills=None, billscount=0, housefound=False)
    # get the relevant queries
    house = Households.query.filter(Households.id==house_id, Households.approved==True).first()
    if house == None: # if no house found, the session is invalid, remove it and display no house (unlikely error, after restarting database)
        session.pop('houseid', None)
        return render_template('viewhousehold.html', currentpage=currentpage, house=None, users=None, links=links, currentid=user_id, bills=None, billscount=0, housefound=False)

    userssize = User.query.filter(User.id==Tenancy.user_id, house_id==Tenancy.household_id, Tenancy.approved==True).count()
    users = User.query.filter(User.id==Tenancy.user_id, house_id==Tenancy.household_id, Tenancy.approved==True)
    # we get the houses only the relevant user should see, so no extra data is sent to the user.
    if user_id == house.head_tenant:
        allBillsCount = Bills.query.filter(Bills.house_id==house_id, Bills.paid==False).count()
        allBills = Bills.query.filter(Bills.house_id==house_id, Bills.paid==False)
    else:
        allBillsCount = Bills.query.filter(Bills.user_id==user_id, Bills.house_id==house_id, Bills.paid==False).count()
        allBills = Bills.query.filter(Bills.user_id==user_id, Bills.house_id==house_id, Bills.paid==False)

    return render_template('viewhousehold.html', currentpage=currentpage, house=house, users=users, links=links, currentid=user_id, bills=allBills, allbillscount=allBillsCount, userssize=userssize, housefound=True)
# inviting a user to a household.
@app.route('/addusertohouse', methods=["POST"])
def addusertohouse():
    user_id = session.get('userid')

    houseid = request.form["HouseholdID"]
    email = request.form["Email"]
    user = User.query.filter_by(email=email).first()
    if user == None:
        addNotif(user_id, "User does not exist.", "Red")
        return ""

    house = Households.query.filter_by(id=houseid).first()
    if house.head_tenant != user_id:
        addNotif(user_id, "Unexpected error.", "Red") # to make sure an invite by a user not as the head tenant is not allowed
        return ""

    tenancy = Tenancy.query.filter(Tenancy.household_id==houseid, Tenancy.user_id==user.id, Tenancy.approved==False).first() # checking for existing invites (unaccepted tenancies)
    if tenancy != None:
        addNotif(user_id, "User already invited.", "Red")
        return ""

    tenancy = Tenancy.query.filter(Tenancy.household_id==houseid, Tenancy.user_id==user.id, Tenancy.approved==True).first() # checking for existing tenants
    if tenancy != None:
        addNotif(user_id, "User already in household.", "Red")
        return ""
    # add the unapproved tenancy.
    tenancy = Tenancy(user.id, houseid, False)
    addNotif(user.id, "You have been invited to a new household!", "Blue")
    addNotif(user_id, "User has been invited.", "Green")
    db.session.add(tenancy)
    db.session.commit()  
    return ""
# for removing users.
@app.route('/removeuser', methods=["POST"])
def removeuser():
    user_id = session.get('userid')
    if user_id == None:
        return redirect('/nouserfound')
    userID = request.form["UserID"]
    houseID = request.form["HouseID"]
    house = Households.query.filter_by(id=houseID)
    if house.head_tenant != user_id:
        addNotif(user_id, "Unexpected error.", "Red") # to make sure only the head tenant can do this, a security issue to avoid post attacks.
        return ""
    Tenancy.query.filter(Tenancy.household_id==houseID, Tenancy.user_id==userID).delete()
    db.session.commit()
    addNotif(user_id, "User removed.", "Green")
    return "refresh"
# for adding bills to users.
@app.route('/addbill', methods=["POST"])
def addbill():
    userid = session.get('userid')
    if userid == None:
        return redirect('/nouserfound')
    userids = request.form.getlist('SelectedUsers[]') # get all the selected users for bills
    print(request.form)
    houseid = request.form["HouseID"]
    billName = request.form["BillName"]
    billPrice = request.form["BillCost"]
    billSplit = request.form["SplitBill"]
    if len(userids) == 0:
        addNotif(userid, "Must select a user.", "Red")
        return ""
    if "htenant" in userids and len(userids) == 1: # if the only 'user' selected is the head tenant themself, there's no bills to send.
        addNotif(userid, "Can't contain just yourself.", "Red")
        return ""
    if billName == "":
        addNotif(userid, "Must select a bill name.", "Red")
        return ""
    if billPrice == "":
        addNotif(userid, "Must select an amount to pay.", "Red")
        return ""
    billPrice = float(billPrice) # convert to float since it was taken as a string from the POST request.
    totalUsers = len(userids)
    if billSplit == "Yes":  # we split the bill.
        billPrice = billPrice / totalUsers
    # format to 2 decimal places (after dividing)
    billPrice = float("{:.2f}".format(billPrice))
    print("Price:" + str(billPrice))
    for user_id in userids:
        if user_id != "htenant":  # add a bill for everyone other than head tenant, they don't need to pay themself.
            newBill = Bills(billName, user_id, houseid, billPrice, False)
            db.session.add(newBill)
            content = "You have a new bill to pay! ( " + billName + ", £" + str(billPrice) + " )"
            addNotif(user_id, content, "Blue")

    db.session.commit()
    addNotif(userid, "Bills sent.", "Blue")
    return "refresh"
 # for sending a payment settlement to resolve
@app.route('/paybills', methods=["POST"])
def paybills():
    user_id = session.get('userid')
    if user_id == None:
        return redirect('/nouserfound')
    billsids = request.form.getlist('SelectedBills') # get the selected billst o pay
    houseid = request.form['HouseID']
    house = Households.query.filter_by(id=houseid).first()
    if len(billsids)==0:
        addNotif(user_id, "Must select a bill.", "Red") 
        return redirect('/viewhousehold')
    for billid in billsids:
        bill = Bills.query.filter_by(id=billid).first()
        if bill.user_id != user_id:
            addNotif(user_id, "Unexpected error.", "Red") # to prevent security issue of the wrong user using post to pay someone else's bill
            return redirect('/viewhousehold') # we don't commit anything.
        bill.paid = True
    db.session.commit()
    addNotif(house.head_tenant, "You have a new bill to settle.", "Blue")
    addNotif(user_id, "Settle request sent.", "Blue")
    return redirect('/viewhousehold')
# the admin page for approving households.
@app.route('/admin')
def admin():
    currentpage="/admin"
    user_id = session.get('userid')
    user = User.query.filter_by(id=user_id).first()
    if(user_id==None):
        return redirect('/nouserfound')
    if(user.admin==False):          # check validity of user
        return redirect('/nopermissions')
    housescount = Households.query.filter_by(approved=False).count()
    houses = Households.query.filter_by(approved=False)
    users = [] # get all the unapproved houses.
    for house in houses:
        user = User.query.filter(User.id==Tenancy.user_id, Tenancy.household_id==house.id).first()
        users.append(user)
    return render_template('admin.html', currentpage=currentpage, links=adminLinks, residences=houses, users=users, housescount=housescount)
# for approving a house ina dmin
@app.route('/approvehouse', methods=["POST"])
def approvehouse():
    user_id = session.get('userid')
    user = User.query.filter_by(id=user_id).first()
    if(user_id==None):
        return redirect('/nouserfound')
    if(user.admin==False):
        return redirect('/nopermissions')   # check validity 
    houseid = request.form['Household']
    household = Households.query.filter_by(id=houseid).first()
    household.approved = True
    tenancy = Tenancy.query.filter_by(household_id=houseid).first()
    addNotif(tenancy.user_id, "Your household request has been accepted!", "Green")
    db.session.commit()
    return redirect('/admin')
# declining a household request as admin
@app.route('/declinehouse', methods=["POST"])
def declinehouse():
    user_id = session.get('userid')
    user = User.query.filter_by(id=user_id).first()
    if(user_id==None):
        return redirect('/nouserfound')
    if(user.admin==False):
        return redirect('/nopermissions') # check permissions
    houseid = request.form['Household']
    tenancy = Tenancy.query.filter_by(household_id=houseid).first()
    addNotif(tenancy.user_id, "Your household request has been rejected!", "Red")
    Tenancy.query.filter_by(household_id=houseid).delete() # delete the tenancy and house, it's rejected.
    Households.query.filter_by(id=houseid).delete()
    db.session.commit()
    return redirect('/admin')
# for a head tenant to approve the bill
@app.route('/approvebill', methods=["POST"])
def approvebill():
    user_id = session.get('userid')
    if(user_id==None):
        return redirect('/nouserfound')
    billid = request.form['BillID']
    bill = Bills.query.filter_by(id=billid).first()
    if bill==None:
        addNotif(user_id, "Unexpected error.", "Red") # no bill found (possible post exploit)
        return redirect('/requests')
    house = Households.query.filter_by(id=bill.house_id).first()
    if user_id!=house.head_tenant:
        addNotif(user_id, "Unexpected error.", "Red") # a bill removal attempt by the non relevant head tenant, likely post exploit.
        return redirect('/requests')
    billuserid = Bills.query.filter_by(id=billid).first().user_id
    addNotif(billuserid, "Your " + bill.name + " bill for £" + str(bill.to_pay) + " has been resolved.", "Green") 
    Bills.query.filter_by(id=billid).delete() # remove bill
    db.session.commit()
    return redirect('/requests')

@app.route('/declinebill', methods=["POST"])
def declinebill():
    user_id = session.get('userid')
    if(user_id==None):
        return redirect('/nouserfound')
    billid = request.form['BillID']
    bill = Bills.query.filter_by(id=billid).first()
    if bill==None:
        addNotif(user_id, "Unexpected error.", "Red") # no bill found (possible post exploit)
        return redirect('/requests')
    house = Households.query.filter_by(id=bill.house_id).first()
    if user_id!=house.head_tenant:
        addNotif(user_id, "Unexpected error.", "Red") # a bill removal attempt by the non relevant head tenant, likely post exploit.
        return redirect('/requests')
    bill.paid = False # set the bill to not paid, so the user will see it again.
    billuserid = Bills.query.filter_by(id=billid).first().user_id
    addNotif(billuserid, "Your " + bill.name + " bill for £" + str(bill.to_pay) + " has been declined.", "Red") 
    db.session.commit()
    return redirect('/requests')
# page for viewing requests.
@app.route('/requests')
def requests():
    links = getLinks()
    currentpage="/requests"
    user_id = session.get('userid')
    if(user_id==None):
        return redirect('/nouserfound')
    tenancycount = Tenancy.query.filter(Tenancy.user_id==user_id, Tenancy.approved==False).count()
    tenancies = Tenancy.query.filter(Tenancy.user_id==user_id, Tenancy.approved==False)
    houses = []
    users = []
    # go through all invalid tenancies with the user (household invites)
    for tenancy in tenancies:
        # we also add users and houses to a list alongside to be used in jinja2 displayment.
        house = Households.query.filter_by(id=tenancy.household_id).first()
        user = User.query.filter(User.id==Tenancy.user_id, Tenancy.household_id==house.id, house.head_tenant==User.id).first()
        houses.append(house)
        users.append(user)
    headHouses = Households.query.filter(Households.head_tenant==user_id)
    allBills = []
    billHouses = []
    billUsers = []
    # go through every house the user is a head tenant of
    for house in headHouses:
        bills = Bills.query.filter(Bills.house_id==house.id, Bills.paid==True)
        # then go through bills of this house that are claimed as paid, to be resolved.
        for bill in bills:
            #add relevant users and houses alongside bills for display with jinja2
            billHouses.append(house)
            allBills.append(bill)
            user1 = User.query.filter_by(id=bill.user_id).first()
            billUsers.append(user1)
    return render_template('requests.html', currentpage=currentpage, links=links, requests=tenancies, residences=houses, users=users, requestcount=tenancycount, allBills=allBills, billHouses=billHouses, billUsers=billUsers, billsCount = len(allBills))
# accept a a household invite
@app.route('/approvetenancy', methods=["POST"])
def approvetenancy():
    user_id = session.get('userid')
    if user_id==None:
        return redirect('/nouserfound')
    houseid = request.form['HouseID']
    house = Households.query.filter_by(id=houseid).first()
    tenancy = Tenancy.query.filter(Tenancy.household_id==houseid, Tenancy.user_id==user_id).first()
    if tenancy == None:
        addNotif(user_id, "Unexpected error.", "Red") # an accept request not for an existing house, attempted post exploit.
        return redirect('/requests')
    tenancy.approved = True # set the tenancy to approved, so are part of house.
    db.session.commit()
    user = User.query.filter(User.id==Tenancy.user_id, Tenancy.household_id==houseid, house.head_tenant==User.id).first()
    addNotif(user.id, "A join request to one of your households has been accepted!", "Green")
    return redirect('/requests')
# reject household invite.
@app.route('/rejecttenancy', methods=["POST"])
def rejecttenancy():
    user_id = session.get('userid')
    if(user_id==None):
        return redirect('/nouserfound')
    userid = request.form['UserID']
    houseid = request.form['HouseID']
    house = Households.query.filter_by(id=houseid).first()
    tenancy = Tenancy.query.filter(Tenancy.household_id==houseid, Tenancy.user_id==userid).first()
    if tenancy == None:
        addNotif(user_id, "Unexpected error.", "Red") # an accept request not for an existing house, attempted post exploit.
        return redirect('/requests')
    # delete the 'invite', it's been rejected
    Tenancy.query.filter(Tenancy.household_id==houseid, Tenancy.user_id==userid).delete() 
    db.session.commit()
    user = User.query.filter(User.id==Tenancy.user_id, Tenancy.household_id==houseid, house.head_tenant==User.id).first()
    addNotif(user.id, "A join request to one of your households has been rejected!", "Red")
    return redirect('/requests')
# error pages
@app.route('/nouserfound')
def nouserfound():
    links = getLinks()
    currentpage="nouserfound"
    return render_template('nouserfound.html', currentpage=currentpage, links=links)

@app.route('/userfound')
def userfound():
    links = getLinks()
    currentpage="userfound"
    return render_template('userfound.html', currentpage=currentpage, links=links)
   
@app.route('/nopermissions')
def nopermissions():
    links = getLinks()
    currentpage="nopermissions"
    return render_template('nopermissions.html', currentpage=currentpage, links=links)
# add a notification with given parameters.
@app.route('/addnotif')
def addNotif(user_id, content, color):
    newNotif = Notifications(user_id, content, color)
    db.session.add(newNotif)
    db.session.commit()
# get notifications for current user, called by jscript every second
@app.route('/getnotif', methods=["POST"])
def getNotif():
    user_id = session.get('userid')
    if user_id == None:
        return ""
    notification = Notifications.query.filter_by(user_id=user_id).first() #get notifications
    if notification == None:
        return ""
    content = notification.content # combine elements into a returnable html to display as an 'alert', styled with css
    color = notification.color
    HTMLtext = ('<div class="notification'+ color +'"><span class="closebutton">&times;</span>'+ content +'</div>') #'&times' gives us the x symbol to close it.
    Notifications.query.filter_by(id=notification.id).delete()
    db.session.commit()
    return HTMLtext
# get the links depending on login / admin status.
def getLinks():
    user_id = session.get('userid')
    user = User.query.filter_by(id=user_id).first()
    if(user==None):
        return defaultLinks
    if(user.admin==True):
        return adminLinks
    else:
        return userLinks




