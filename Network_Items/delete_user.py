from app import db

target = input("Enter a username: ")

user = User.query.filter_by(username=target).first()

if user:
	db.session.delete(user)
	db.session.commit()
	print("User Deleted!")
else:
	print("User Not Found!")
