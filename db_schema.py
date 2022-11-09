from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, text
from werkzeug import security
from sqlalchemy.orm import relationship
# create the database interface
db = SQLAlchemy()
# user interface to store each user
class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20)) # i am allowing repeat usernames, but emails will be unique.
    email = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(1000)) 
    admin = db.Column(db.Boolean)

    def __init__(self, username, email, password, isadmin):  
        self.username=username
        self.email=email
        self.password=password
        self.admin = isadmin
# household model to store each house
class Households(db.Model):
    __tablename__='households'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text()) 
    head_tenant = db.Column(db.Integer)
    approved = db.Column(db.Boolean)

    def __init__(self, name, head_tenant, approved):
        self.name=name
        self.head_tenant=head_tenant
        self.approved=approved
# since a house and user have a many to many relationships, we normalise it with an intermittary table
class Tenancy(db.Model):
    __tablename__='tenancy'
    user_id = db.Column(db.Integer, primary_key=True)      #a composite key of foreign key userid and householdid
    household_id = db.Column(db.Integer, primary_key=True)
    approved = db.Column(db.Boolean)                       #to approve households before making them accessible
    
    def __init__(self, userid, householdid, approved):
        self.user_id = userid
        self.household_id = householdid
        self.approved = approved
# Bills model to store individual bills
class Bills(db.Model):
    __tablename__='bills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())        
    user_id = db.Column(db.Integer)      # we treat the bills individually for each user.
    house_id = db.Column(db.Integer)
    to_pay = db.Column(db.Float )
    paid = db.Column(db.Boolean)         # to determine when the bill has been claimed as paid, for resolving settlements.

    def __init__(self, name, userid, houseid, topay, paid):
        self.name = name
        self.user_id = userid
        self.house_id = houseid
        self.to_pay = topay
        self.paid = paid
#notification table to store instances of notifications. 
class Notifications(db.Model):
    __tablename__='notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)    #a notificatino belongs to a user, with content and a colour.
    content = db.Column(db.Text())
    color = db.Column(db.Text())
    
    def __init__(self, userid, content, color):
        self.user_id = userid
        self.content = content
        self.color = color

def dbinit():
    #some premade users.
    user_list = [          
        User("BingusEnjoyer", "bingus@bingus.com", security.generate_password_hash("ilovebingus"), True), 
        User("BigBingus", "bigbingus@bingus.com", security.generate_password_hash("ireallylovebingus"), False),
        User("BingusHater", "ihatebingus@floppa.com", security.generate_password_hash("deathtobingus"), False),
        User("Ryuko", "clothesarebad@lifefibers.com", security.generate_password_hash("DONTLOSEYOURWAY"), True)
        ]
    db.session.add_all(user_list)
    db.session.commit()
    
    BingusHouse = Households("Bingus House", user_list[0].id, True)
    db.session.add(BingusHouse)
    db.session.commit()
    # one premade household
    tenancy_list = [
        Tenancy(user_list[0].id, BingusHouse.id, True), 
        Tenancy(user_list[1].id, BingusHouse.id, True),
        Tenancy(user_list[2].id, BingusHouse.id, True)
        ]
    db.session.add_all(tenancy_list)
    db.session.commit()
        




