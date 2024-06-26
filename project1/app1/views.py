from django.shortcuts import render
import uuid
from django.contrib.auth.hashers import make_password
from .models import SupportTicket
from .models import User
from django.http import HttpResponse,JsonResponse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
from .models import Agent
from django.utils import timezone
from django.conf import settings
from .models import Record
Str=''
def index(request):
    return HttpResponse("<h1>app is running</h1>")

def add_detail(request):
    # Create a new record
    record = Record(first="tarun", last="S R")
    record.save()
    
    return HttpResponse("added")

@csrf_exempt
def add_ticket(request, customer_name, email, subject, description):
    try:
        # Debug: Print statement to check if the function is called
        print("add_ticket function called")

        # Retrieve all agents
        all_agents = Agent.objects.all()
        
        # Filter available agents
        available_agents = [agent for agent in all_agents if agent.is_available]

        # Debug: Print the available agents
        print(f"Available Agents: {available_agents}")

        if available_agents:
            # Select an available agent (Example: First available agent)
            selected_agent = available_agents[0]

            # Create a support ticket
            ticket = SupportTicket.objects.create(
                ticket_id=uuid.uuid4(),
                customer_name=customer_name,
                email=email,
                subject=subject,
                description=description,
                status='Open',
                created_at=timezone.now(),
                assigned_agent=selected_agent  # Assign the selected agent to the ticket
            )
            ticket.save()

            # Optionally mark the agent as unavailable after assignment
            selected_agent.is_available = False
            selected_agent.save()

            return HttpResponse("Ticket created successfully.")
        else:
            return HttpResponse("No available agents at the moment.")
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse(f"An error occurred: {e}")    
@csrf_exempt
def add_agent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        phone_number = data.get('phone_number')

        # Create a unique ID for the agent
        agent_id = str(uuid.uuid4())
        
        # Create the agent with the extracted data
        agent = Agent(
            agent_id=agent_id,
            name=name,
            email=email,
            phone_number=phone_number,
            created_at=datetime.now(),
            is_available=True  # Assuming new agents are active by default
        )

        # Save the agent to the database
        agent.save()
        
        # Return a success response with the agent ID
        return HttpResponse(f"Agent added with ID: {agent_id}")
    return HttpResponse(status=405)  # Method not allowed

@csrf_exempt
def add_user(request, username, email, password):
    # Create a unique ID for the user
    user_id = str(uuid.uuid4())
    
    hashed_password = make_password(password)
    # Create the user with the extracted data
    user = User(
        user_id=user_id,
        username=username,
        email=email,
        password=hashed_password,
        created_at=datetime.now(),
        is_active=True  # Assuming new users are active by default
    )
    request.session['user_id'] = user_id
    # Save the user to the database
    user.save()
    
    
    # Return a success response with the user ID
    return HttpResponse(f"User added with ID: {user_id}")

@csrf_exempt
def delete_ticket(request, ticket_id):
    # Convert ticket_id to string (if necessary)
    ticket_id = str(ticket_id)

    try:
        # Try to find and delete the ticket
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
        ticket.delete()
        return HttpResponse(f"Support ticket with ID: {ticket_id} deleted successfully.")
    except SupportTicket.DoesNotExist:
        return HttpResponse(f"Ticket with ID {ticket_id} does not exist.", status=404)
@csrf_exempt
def update_ticket(request, ticket_id):
    if request.method == 'PATCH':
        # Convert ticket_id to string (if necessary)
        ticket_id = str(ticket_id)

        try:
            # Find the ticket by ID
            ticket = SupportTicket.objects.get(ticket_id=ticket_id)
        except SupportTicket.DoesNotExist:
            return JsonResponse({"error": f"Ticket with ID {ticket_id} does not exist."}, status=404)

        # Parse the JSON data from the request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        # Update the ticket fields with the provided data
        if 'customer_name' in data:
            ticket.customer_name = data['customer_name']
        if 'email' in data:
            ticket.email = data['email']
        if 'subject' in data:
            ticket.subject = data['subject']
        if 'description' in data:
            ticket.description = data['description']
        
        # Save the updated ticket
        ticket.save()

        # Send email notification about the update
        recipient_email = ticket.email  # Retrieve recipient's email from the ticket object
        send_mail(
                        "test",
                        'The change has been updated',
                        '71762131056@cit.edu.in',
                        [recipient_email], 
                        fail_silently=False,
                    )
        return JsonResponse({"message": f"Support ticket with ID: {ticket_id} updated successfully."})
    else:
        return JsonResponse({"error": "Method not allowed. Use PATCH method to update a ticket."}, status=405)
@csrf_exempt
def search_tickets(request):
    if request.method == 'GET':
        # Parse query parameters
        customer_name = request.GET.get('customer_name', None)
        ticket_id = request.GET.get('ticket_id', None)
        date_gt = request.GET.get('date_gt', None)
        date_lt = request.GET.get('date_lt', None)
        date_eq = request.GET.get('date_eq', None)

        # Build search criteria
        match_stage = {}

        if customer_name:
            match_stage['customer_name'] = customer_name
        if ticket_id:
            match_stage['ticket_id'] = ticket_id
        if date_gt:
            try:
                match_stage['created_at__gt'] = datetime.fromisoformat(date_gt)
            except ValueError:
                return JsonResponse({"error": "Invalid date format for date_gt"}, status=400)
        if date_lt:
            try:
                match_stage['created_at__lt'] = datetime.fromisoformat(date_lt)
            except ValueError:
                return JsonResponse({"error": "Invalid date format for date_lt"}, status=400)
        if date_eq:
            try:
                match_stage['created_at'] = datetime.fromisoformat(date_eq)
            except ValueError:
                return JsonResponse({"error": "Invalid date format for date_eq"}, status=400)

        # Execute the query
        try:
            results = SupportTicket.objects.filter(**match_stage).order_by('created_at')
        except SupportTicket.DoesNotExist:
            return JsonResponse({"error": "No tickets found matching the criteria"}, status=404)

        # Serialize results
        serialized_results = list(results.values())

        return JsonResponse(serialized_results, safe=False)

    else:
        return JsonResponse({"error": "Method not allowed. Use GET method to search for tickets."}, status=405)