from django.shortcuts import render
import uuid
from .models import c1
from django.http import HttpResponse,JsonResponse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
import smtplib
from django.conf import settings

def index(request):
    return HttpResponse("<h1>app is runnning</h1>")
def add_detail(request):
    records={
        "first":"tarun",
        "last":"S R" 
    }
    c1.insert_one(records)
    return HttpResponse("added")
def all_person(request):
    a=c1.find()
    return HttpResponse(a)
@csrf_exempt
def add_ticket(request, customer_name, email, subject, description):
    # Create a unique ID for the support ticket

    customer_name = customer_name.replace('%20', ' ')
    email = email.replace('%20', ' ')
    subject = subject.replace('%20', ' ')
    description = description.replace('%20', ' ')
    ticket_id = str(uuid.uuid4())

    # Create the support ticket with the extracted data
    ticket = {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "email": email,
        "subject": subject,
        "description": description,
        "status": "open",  # Default status
        "created_at": datetime.now()
    }

    # Insert the support ticket into the collection
    c1.insert_one(ticket)
    
    # Return a success response with the ticket ID
    return HttpResponse(f"Support ticket added with ID: {ticket_id}")
@csrf_exempt    
def delete_ticket(request, ticket_id):
    
        # Convert ticket_id to string (if necessary)
        ticket_id = str(ticket_id)

        # Check if the ticket exists
        ticket = c1.find_one({"ticket_id": ticket_id})
        if ticket:
            # Delete the ticket from the collection
            c1.delete_one({"ticket_id": ticket_id})
            return HttpResponse(f"Support ticket with ID: {ticket_id} deleted successfully.")
        else:
            return HttpResponse(f"Ticket with ID {ticket_id} does not exist.", status=404)
    
        # Handle other HTTP methods (e.g., GET, POST, PUT)


@csrf_exempt  # Temporarily exempt from CSRF protection for demonstration (not recommended in production)
def update_ticket(request, ticket_id):
    if request.method == 'PATCH':
        # Convert ticket_id to string (if necessary)
        ticket_id = str(ticket_id)

        # Check if the ticket exists
        ticket = c1.find_one({"ticket_id": ticket_id})
        if ticket:
            # Parse the JSON data from the request body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)

            # Update the ticket with the provided data
            update_data = {}
            if 'customer_name' in data:
                update_data['customer_name'] = data['customer_name']
            if 'email' in data:
                update_data['email'] = data['email']
            if 'subject' in data:
                update_data['subject'] = data['subject']
            if 'description' in data:
                update_data['description'] = data['description']
            

            c1.update_one({"ticket_id": ticket_id}, {"$set": update_data})
            updated_ticket = c1.find_one({"ticket_id": ticket_id})
            if updated_ticket:
                recipient_email = updated_ticket.get('email', '')
            else:
                return HttpResponse(f"Ticket with ID {ticket_id} not found.", status=404)
            send_mail(
                        "test",
                        'The change has been updated',
                        '71762131056@cit.edu.in',
                        [recipient_email], 
                        fail_silently=False,
                    )

            # Notify the customer about the update via email
            print(f"Support ticket with ID: {ticket_id} updated successfully.")

            return HttpResponse(f"Support ticket with ID: {ticket_id} updated successfully.")
        else:
            return HttpResponse(f"Ticket with ID {ticket_id} does not exist.", status=404)
    else:
        # Handle other HTTP methods (e.g., GET, POST, DELETE)
        return HttpResponse("Method not allowed. Use PATCH method to update a ticket.", status=405)