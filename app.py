import datetime
from flask_cors import CORS
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from models import database, user_model, service_model, service_request_model, feedback_model
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
CORS(app)
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://test:password@localhost/cleaning"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:password@localhost:5432/cleaning"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://bananamana77:v2_3wJKR_8kkfpFwyPW6gbUMWPqQAytU@db.bit.io/bananamana77/cleaning"

database.db.init_app(app)

with app.app_context():
    database.db.create_all()


# Route to create a new user
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    user = user_model.User.query.filter_by(email=data["email"]).first()
    if not user:
        new_user = user_model.User(
            email=data["email"],
            password=generate_password_hash(data["password"]),
            user_type=data["user_type"],
            address=data["address"],
            phone=data["phone"],
        )
        database.db.session.add(new_user)
        database.db.session.commit()
        return make_response("User created", 201)
    else:
        return make_response("User already exists", 202)


# Route to login a user
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = user_model.User.query.filter_by(email=data["email"]).first()
    if user:
        if check_password_hash(user.password, data["password"]):
            user_data = {}
            user_data["id"] = user.id
            user_data["email"] = user.email
            user_data["user_type"] = user.user_type
            user_data["address"] = user.address
            user_data["phone"] = user.phone
            return jsonify({"curr_user": user_data})
        else:
            return make_response("Incorrect password", 401)
    else:
        return make_response("User does not exist", 404)


# Route to get list of users
@app.route("/users", methods=["GET"])
def get_users():
    users = user_model.User.query.all()
    result = []

    for user in users:
        user_data = {}
        user_data["id"] = user.id
        user_data["email"] = user.email
        user_data["user_type"] = user.user_type
        user_data["address"] = user.address
        user_data["phone"] = user.phone
        result.append(user_data)

    return jsonify({"users": result})


# Route to create a new service
@app.route("/services", methods=["POST"])
def create_service():
    data = request.get_json()

    if "user_id" not in data or "start_date" not in data \
            or "end_date" not in data or "start_time" not in data or "end_time" not in data:
        return make_response("Missing data", 400)

    user = user_model.User.query.filter_by(id=data["user_id"]).first()

    if not user:
        return make_response("User does not exist", 404)

    if user.user_type != "VENDOR":
        return make_response("User is not a vendor", 401)

    services = data["services"]

    start_hour = int(data["start_time"].split(":")[0])
    end_hour = int(data["end_time"].split(":")[0])

    start_date = datetime.datetime.strptime(data["start_date"], "%Y/%m/%d")
    end_date = datetime.datetime.strptime(data["end_date"], "%Y/%m/%d")

    time_delta = datetime.timedelta(days=1)

    # Create service for each day and each hour
    while start_date <= end_date:
        for hour in range(start_hour, end_hour + 1):
            for service in services:
                new_service = service_model.Service(
                    service_type=service["service_type"],
                    description=service["description"],
                    date=start_date,
                    time=f"{hour}:00",
                    price=service["price"],
                    location=service["location"],
                    user_id=data["user_id"],
                )
                database.db.session.add(new_service)
        start_date += time_delta

    database.db.session.commit()

    return make_response("Service created", 201)


# Route to book a service
@app.route("/services/book", methods=["POST"])
def book_service():
    data = request.get_json()

    user = user_model.User.query.filter_by(id=data["user_id"]).first()

    if not user:
        return make_response("User does not exist", 404)

    if user.user_type != "CUSTOMER":
        return make_response("User is not a customer", 401)

    service = service_model.Service.query.filter_by(
        id=data["service_id"]).first()

    if not service:
        return make_response("Service does not exist", 404)

    if service.status != "ACTIVE":
        return make_response("Service is not active", 401)

    new_service_request = service_request_model.ServiceRequest(
        service_id=data["service_id"],
        customer_id=data["user_id"],
        image=data["image"]
    )
    database.db.session.add(new_service_request)

    # Update service status to BOOKED
    service.status = "BOOKED"

    database.db.session.commit()
    return make_response("Service booked", 201)


# Route to create feedback
@app.route("/feedback", methods=["POST"])
def create_feedback():
    data = request.get_json()

    user = user_model.User.query.filter_by(id=data["user_id"]).first()

    if not user:
        return make_response("User does not exist", 404)

    if user.user_type == "VENDOR":
        return make_response("Vendors cannot create feedback", 401)

    service_request = service_request_model.ServiceRequest.query.filter_by(
        id=data["service_request_id"]
    ).first()
    if service_request:
        new_feedback = feedback_model.Feedback(
            service_request_id=data["service_request_id"],
            feedback=data["feedback"],
            rating=data["rating"],
            image=data["image"],
        )
        database.db.session.add(new_feedback)
        database.db.session.commit()
        return make_response("Feedback created", 201)
    else:
        return make_response("Service request does not exist", 404)


# Route for vendor to update service status
@app.route("/services/<service_request_id>", methods=["PUT"])
def update_service_status(service_request_id):
    data = request.get_json()

    service_request = service_request_model.ServiceRequest.query.filter_by(
        id=service_request_id).first()

    if not service_request:
        return make_response("Service request does not exist", 404)

    service_request.status = data["status"]

    database.db.session.commit()
    return make_response("Service status updated", 200)


# Route to get all services that are active and satisfy the search criteria
@app.route("/services", methods=["GET"])
def get_services():
    today_date = datetime.datetime.now().date()

    # Get all services that are active and have a date greater than or equal to today's date
    services = service_model.Service.query.filter(
        service_model.Service.status == "ACTIVE",
        service_model.Service.date >= today_date,
    ).all()

    result = []

    for service in services:
        service_data = {}
        service_data["id"] = service.id
        service_data["service_type"] = service.service_type
        service_data["description"] = service.description
        # service_data["date"] = service.date.strftime("%Y/%m/%d")
        service_data["date"] = service.date
        service_data["time"] = service.time
        service_data["price"] = service.price
        service_data["location"] = service.location
        service_data["user_id"] = service.user_id
        result.append(service_data)

    query_date = request.args.get("date")
    if query_date:
        query_date = datetime.datetime.strptime(query_date, "%Y/%m/%d").date()
    print(f"query date {query_date}")
    print(f"service {services[0].date == query_date}")
    query_location = request.args.get("location")
    query_service_type = request.args.get("service-type")

    if query_date:
        result = list(filter(lambda x: x["date"] == query_date, result))

    if query_location:
        result = list(
            filter(lambda x: x["location"] == query_location, result))

    if query_service_type:
        result = list(
            filter(lambda x: x["service_type"] == query_service_type, result))

    return jsonify({"services": result})


# Route to get all service requests for a user - past and future
@app.route("/services/requests/<user_id>", methods=["GET"])
def get_service_requests(user_id):
    service_requests = []
    user = user_model.User.query.filter_by(id=user_id).first()
    if(user.user_type=="CUSTOMER"):
        service_requests = service_request_model.ServiceRequest.query\
            .join(service_model.Service, service_model.Service.id == service_request_model.ServiceRequest.service_id)\
            .join(feedback_model.Feedback, feedback_model.Feedback.service_request_id == service_request_model.ServiceRequest.id, isouter=True)\
            .add_columns(service_request_model.ServiceRequest.id, service_request_model.ServiceRequest.service_id, service_request_model.ServiceRequest.customer_id, service_request_model.ServiceRequest.status, service_request_model.ServiceRequest.image, service_model.Service.service_type, service_model.Service.description, service_model.Service.date, service_model.Service.time, service_model.Service.price, service_model.Service.location, feedback_model.Feedback.feedback, feedback_model.Feedback.rating, feedback_model.Feedback.image)\
            .filter(service_request_model.ServiceRequest.customer_id == user_id)\
            .all()
    else:
        service_requests = service_request_model.ServiceRequest.query\
            .join(service_model.Service, service_model.Service.id == service_request_model.ServiceRequest.service_id)\
            .join(feedback_model.Feedback, feedback_model.Feedback.service_request_id == service_request_model.ServiceRequest.id, isouter=True)\
            .add_columns(service_request_model.ServiceRequest.id, service_request_model.ServiceRequest.service_id, service_request_model.ServiceRequest.customer_id, service_request_model.ServiceRequest.status, service_request_model.ServiceRequest.image, service_model.Service.service_type, service_model.Service.description, service_model.Service.date, service_model.Service.time, service_model.Service.price, service_model.Service.location, feedback_model.Feedback.feedback, feedback_model.Feedback.rating, feedback_model.Feedback.image)\
            .filter(service_model.Service.user_id == user_id)\
            .all()

    result = []

    for service_request in service_requests:
        service_request_data = {}
        print(service_request)
        service_request_data["id"] = service_request.id
        service_request_data["customer_id"] = service_request.customer_id
        service_request_data["status"] = service_request.status
        service_request_data["image"] = service_request.image
        service_request_data["feedback"] = {
            "feedback": service_request.feedback,
            "rating": service_request.rating
        }
        service_request_data["service_type"] = service_request.service_type
        service_request_data["description"] = service_request.description
        service_request_data["date"] = service_request.date
        service_request_data["time"] = service_request.time
        service_request_data["price"] = service_request.price
        service_request_data["location"] = service_request.location
        result.append(service_request_data)

    # Add services that have a date before today in past_services list and services that have a date after today in future_services list
    past_services = []
    future_services = []
    for service in result:
        if service["date"] < datetime.datetime.now().date():
            past_services.append(service)
        else:
            future_services.append(service)

    return jsonify({"past_services": past_services, "future_services": future_services})

# Route to get a feedback
@app.route("/feedback/<service_id>", methods=["GET"])
def get_feedback(service_id):
    service = service_model.Service.query.filter_by(id=service_id).first()

    if not service:
        return make_response("No service for this id exists", 404)

    feedback = service_request_model.ServiceRequest.query\
        .join(service_model.Service, service_model.Service.id == service_request_model.ServiceRequest.service_id)\
        .join(feedback_model.Feedback, feedback_model.Feedback.service_request_id == service_request_model.ServiceRequest.id, isouter=True)\
        .add_columns(feedback_model.Feedback.id, service_request_model.ServiceRequest.service_id, feedback_model.Feedback.feedback, feedback_model.Feedback.rating, feedback_model.Feedback.image)\
        .filter(service_model.Service.id == service_id)\
        .first()
 
    if not feedback:
        return make_response("No feedback for this service id exists", 404)
    
    feedback_data = {}
    feedback_data["id"] = feedback.id
    feedback_data["service_id"] = feedback.service_id
    feedback_data["rating"] = feedback.rating
    feedback_data["image"] = feedback.image
    feedback_data["feedback"] = feedback.feedback    

    return jsonify({"feedback": feedback_data})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
