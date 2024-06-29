from django.shortcuts import render
import uuid
import logging
from django.contrib.auth.hashers import make_password
from .models import SupportTicket, CompletedTicket, Agent, User
from django.views.decorators.http import require_http_methods
from .models import SupportTicket
from .models import User
from django.http import HttpResponse,JsonResponse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
from .models import Agent
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.contrib.sessions.models import Session
from .models import Record
from django.contrib.auth import authenticate, login
import requests
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
Str=''
def index(request):
    return HttpResponse("<h1>app is running</h1>")

def add_detail(request):
    # Create a new record
    record = Record(first="tarun", last="S R")
    record.save()
    
    return HttpResponse("added")
@csrf_exempt
@swagger_auto_schema(method='post', request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    },
    required=['username', 'password']
), responses={
    200: openapi.Response(description="Login successful", examples={
        "application/json": {"message": "Login successful", "user_id": "user_id_value"}
    }),
    400: openapi.Response(description="Invalid username or password"),
    405: openapi.Response(description="Method not allowed")
})

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            logger.error("Missing fields in login request")
            return JsonResponse({'message': 'Missing fields'}, status=400)
        
        try:
            # Fetch the user by username
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("Invalid username: %s", username)
            return JsonResponse({'message': 'Invalid username or password'}, status=400)
        
        # Check if the password matches
        if not check_password(password, user.password):
            logger.error("Invalid password for username: %s", username)
            return JsonResponse({'message': 'Invalid username or password'}, status=400)
        
        # Store user_id in the session
        request.session['user_id'] = str(user.user_id)
        print(f"User ID stored in session: {request.session['user_id']}")
        print(request.session.items())
        
        # Return a success response with the user ID
        return JsonResponse({'message': 'Login successful', 'user_id': str(user.user_id)})
    logger.error("Method not allowed for login_user")
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@csrf_exempt
@swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'subject': openapi.Schema(type=openapi.TYPE_STRING, description='Ticket subject'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Ticket description'),
    }
), responses={200: 'Ticket created successfully', 400: 'No available agents', 403: 'User not logged in', 500: 'An error occurred'})
@api_view(['POST'])
def add_ticket(request, subject, description):
    try:
        print("add_ticket function called")

        all_agents = Agent.objects.all()
        available_agents = [agent for agent in all_agents if agent.is_available]
        
        print(f"Available Agents: {available_agents}")

        if available_agents:
            selected_agent = available_agents[0]
            
            # Retrieve user_id from session
            user_id = request.session.get('user_id')
            print(f"User ID from session: {user_id}")

            if not user_id:
                logger.error("User not logged in")
                return JsonResponse({'message': 'User is not logged in'}, status=403)

            try:
                user = User.objects.get(user_id=user_id)
                
            except User.DoesNotExist:
                logger.error("User not found for user_id: %s", user_id)
                return JsonResponse({'message': 'User not found'}, status=404)


            ticket = SupportTicket.objects.create(
                ticket_id=str(uuid.uuid4()),
                subject=subject,
                description=description,
                status='Open',
                user=user,  
                created_at=timezone.now(),
                assigned_agent=selected_agent
            )
            ticket.save()

            selected_agent.is_available = False
            selected_agent.save()
            logger.info("Ticket %s created successfully for user %s", ticket.ticket_id, user_id)
            return JsonResponse({'message': 'Ticket created successfully', 'ticket_id': ticket.ticket_id})
        else:
            logger.error("No available agents at the moment")
            return JsonResponse({'message': 'No available agents at the moment'}, status=400)
    except Exception as e:
        logger.error("An error occurred in add_ticket: %s", str(e))
        print(f"Error: {e}")
        return JsonResponse({'message': f'An error occurred: {e}'}, status=500)
    

@csrf_exempt
@swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Agent name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Agent email'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Agent phone number'),
    }
), responses={200: 'Agent added successfully', 405: 'Method not allowed'})
@api_view(['POST'])
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
            is_available=True  
        )

      
        agent.save()
        
        logger.info("Agent %s added with ID %s", name, agent_id)
        return HttpResponse(f"Agent added with ID: {agent_id}")
    logger.error("Method not allowed for add_agent")
    return HttpResponse(status=405) 

@csrf_exempt
@swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    }
), responses={200: 'User added successfully', 400: 'Username already exists', 500: 'Failed to add user'})
@api_view(['POST'])
def add_user(request, username, email, password):
    try:
        existing_user = User.objects.get(username=username)
        logger.error("Username %s already exists", username)
        return JsonResponse({'message': 'Username already exists'}, status=400)
    except User.DoesNotExist:
        
        user_id = str(uuid.uuid4())
        hashed_password = make_password(password)

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password=hashed_password,
            created_at=datetime.now(),
            is_active=True
        )
        
        user.save()
        logger.info("User %s added with ID %s", username, user_id)
        
        return HttpResponse(f"User added with ID: {user_id}")
    except Exception as e:
        logger.error("Failed to add user: %s", str(e))
        
        return JsonResponse({'message': f'Failed to add user: {str(e)}'}, status=500)
    


@csrf_exempt
@swagger_auto_schema(methods=['delete'], manual_parameters=[
    openapi.Parameter('ticket_id', openapi.IN_PATH, description="Ticket ID to delete", type=openapi.TYPE_STRING)
], responses={200: 'Ticket deleted successfully', 404: 'Ticket not found', 500: 'An error occurred'})
@api_view(['DELETE'])
def delete_ticket(request, ticket_id):
    ticket_id = str(ticket_id)

    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
        ticket.delete()
        logger.info("Support ticket with ID %s deleted successfully", ticket_id)
        return HttpResponse(f"Support ticket with ID: {ticket_id} deleted successfully.")
    except SupportTicket.DoesNotExist:
        logger.error("Ticket with ID %s does not exist", ticket_id)
        return HttpResponse(f"Ticket with ID {ticket_id} does not exist.", status=404)
    

@csrf_exempt    
@swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'payload': openapi.Schema(type=openapi.TYPE_STRING, description='Webhook payload'),
    }
), responses={200: 'Webhook received successfully', 500: 'Failed to process webhook'})
@api_view(['POST'])
def webhook_receiver(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process the received data as needed
            logger.info("Webhook received successfully with data: %s", data)
            return JsonResponse({"message": "Webhook received successfully!"})
        except json.JSONDecodeError:
            logger.error("Invalid JSON format received in webhook")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    else:
        logger.error("Method not allowed for webhook_receiver")
        return JsonResponse({"error": "Method not allowed."}, status=405)


@csrf_exempt
@swagger_auto_schema(methods=['patch'], manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_PATH, description="User ID to update", type=openapi.TYPE_STRING)
], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='New username'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='New email'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
    }
), responses={200: 'User updated successfully', 404: 'User not found', 500: 'An error occurred'})
@api_view(['PATCH'])
def update_user(request, user_id):
    if request.method == 'PATCH':
        user_id = str(user_id)

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            logger.error("User with ID %s does not exist", user_id)
            return JsonResponse({"error": f"User with ID {user_id} does not exist."}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in update_user")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        # Update user fields if provided in the request
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.password = data['password']  # Ensure to hash the password in a real application
        
        user.save()

        # Webhook URL to notify the user
        webhook_url = 'http://localhost:8000/app1/webhook/' 
        payload = {
            "message": f"User with ID {user_id} has been updated.",
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Webhook notification sent successfully for user %s", user_id)
        except requests.exceptions.RequestException as e:
            logger.error("Failed to send webhook notification: %s", str(e))
            return JsonResponse({"error": f"Failed to send webhook notification: {e}"}, status=500)
        logger.info("User with ID %s updated successfully", user_id)
        return JsonResponse({"message": f"User with ID {user_id} updated successfully"})
    else:
        logger.error("Method not allowed for update_user")
        return JsonResponse({"error": "Method not allowed."}, status=405)



@csrf_exempt
@swagger_auto_schema(methods=['patch'], manual_parameters=[
    openapi.Parameter('agent_id', openapi.IN_PATH, description="Agent ID to update", type=openapi.TYPE_STRING)
], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='New agent name'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='New agent email'),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='New agent phone number'),
    }
), responses={200: 'Agent updated successfully', 404: 'Agent not found', 500: 'An error occurred'})
@api_view(['PATCH'])
def update_agent(request, agent_id):
    if request.method == 'PATCH':
        agent_id = str(agent_id)

        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error("Agent with ID %s does not exist", agent_id)
            return JsonResponse({"error": f"Agent with ID {agent_id} does not exist."}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in update_agent")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        # Update agent fields if provided in the request
        if 'name' in data:
            agent.name = data['name']
        if 'email' in data:
            agent.email = data['email']
        if 'phone_number' in data:
            agent.phone_number = data['phone_number']
        if 'is_available' in data:
            agent.is_available = data['is_available']

        agent.save()

        # Webhook URL to notify about agent update
        webhook_url = 'http://localhost:8000/app1/webhook/' 
        payload = {
            "message": f"Agent with ID {agent_id} has been updated.",
            "agent_id": agent_id,
            "name": agent.name,
            "email": agent.email,
            "phone_number": agent.phone_number,
            "is_available": agent.is_available,
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Webhook notification sent successfully for agent %s", agent_id)
        except requests.exceptions.RequestException as e:
            logger.error("Failed to send webhook notification: %s", str(e))
            return JsonResponse({"error": f"Failed to send webhook notification: {e}"}, status=500)

        logger.info("Agent with ID %s updated successfully", agent_id)
        return JsonResponse({"message": f"Agent with ID {agent_id} updated successfully"})
    else:
        logger.error("Method not allowed for update_agent")
        return JsonResponse({"error": "Method not allowed."}, status=405)



@csrf_exempt
@swagger_auto_schema(methods=['get'], manual_parameters=[
    openapi.Parameter('ticket_id', openapi.IN_QUERY, description="Filter by ticket ID", type=openapi.TYPE_STRING),
    openapi.Parameter('date', openapi.IN_QUERY, description="Filter by creation date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
], responses={200: 'Search results returned successfully', 500: 'An error occurred'})
@api_view(['GET'])
def search_tickets(request):
    if request.method == 'GET':
        ticket_id = request.GET.get('ticket_id', None)
        date_gt = request.GET.get('date_gt', None)
        date_lt = request.GET.get('date_lt', None)
        date_eq = request.GET.get('date_eq', None)
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size',2)

        match_stage = {}

        if ticket_id:
            match_stage['ticket_id'] = ticket_id
        if date_gt:
            try:
                match_stage['created_at__gt'] = datetime.fromisoformat(date_gt)
            except ValueError:
                logger.error("Invalid date format for date_gt: %s", date_gt)
                return JsonResponse({"error": "Invalid date format"}, status=400)
        if date_lt:
            try:
                match_stage['created_at__lt'] = datetime.fromisoformat(date_lt)
            except ValueError:
                logger.error("Invalid date format for date_lt: %s", date_lt)
                return JsonResponse({"error": "Invalid date format"}, status=400)
        if date_eq:
            try:
                match_stage['created_at'] = datetime.fromisoformat(date_eq)
            except ValueError:
                logger.error("Invalid date format for date_eq: %s", date_eq)
                return JsonResponse({"error": "Invalid date format"}, status=400)

        # Execute the query
        try:
            results = SupportTicket.objects.filter(**match_stage).order_by('created_at')
            logger.info("Search tickets results: %s", results)
        except SupportTicket.DoesNotExist:
            logger.error("No tickets found matching criteria")
            return JsonResponse({"error": "No tickets found matching"}, status=404)

        # Paginate results
        paginator = Paginator(results, page_size)
        try:
            paginated_results = paginator.page(page)
        except PageNotAnInteger:
            paginated_results = paginator.page(1)
        except EmptyPage:
            paginated_results = paginator.page(paginator.num_pages)

        # Serialize results
        serialized_results = list(paginated_results.object_list.values())

        response = {
            'results': serialized_results,
            'page': paginated_results.number,
            'pages': paginator.num_pages,
            'total': paginator.count
        }

        return JsonResponse(response, safe=False)

    else:
        logger.error("Method not allowed for search_tickets")
        return JsonResponse({"error": "Method not allowed"}, status=405)
    

@csrf_exempt
@require_http_methods(["POST"])
@swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'ticket_id': openapi.Schema(type=openapi.TYPE_STRING, description='Ticket ID to close'),
    }
), responses={200: 'Ticket closed successfully', 404: 'Ticket not found', 500: 'An error occurred'})
@api_view(['POST'])
def close_ticket(request):
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            logger.error("Ticket ID not provided in request body")
            return JsonResponse({'message': 'Ticket ID not provided'}, status=400)

        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
        logger.info("Closing ticket: %s", ticket_id)

        # Handle case where user may not exist
        try:
            user = ticket.user
        except User.DoesNotExist:
            user = None
        
        # Handle case where agent may not exist
        try:
            assigned_agent = ticket.assigned_agent
        except Agent.DoesNotExist:
            assigned_agent = None

        completed_ticket = CompletedTicket.objects.create(
            ticket_id=ticket.ticket_id,
            subject=ticket.subject,
            description=ticket.description,
            status='closed',
            created_at=ticket.created_at,
            user=user,
            assigned_agent=assigned_agent,
            completed_at=timezone.now()
        )
        completed_ticket.save()

        # Update agent availability if agent exists
        if assigned_agent:
            assigned_agent.is_available = True
            assigned_agent.save()

        # Delete the original ticket
        ticket.delete()
        
        logger.info("Ticket %s closed successfully", ticket_id)

        # Send webhook notification
        webhook_url = 'http://localhost:8000/app1/webhook/'
        payload = {
            "message": f"Ticket has been closed.",
            'ticket_id': completed_ticket.ticket_id,
            'status': 'closed',
            'completed_at': str(completed_ticket.completed_at),
            'user': {
                'user_id': user.user_id if user else None,
                'username': user.username if user else None,
                'email': user.email if user else None,
            },
            'assigned_agent': {
                'agent_id': assigned_agent.agent_id if assigned_agent else None,
                'name': assigned_agent.name if assigned_agent else None,
                'email': assigned_agent.email if assigned_agent else None,
            }
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Webhook notification sent successfully for ticket %s", ticket_id)
            return JsonResponse({'message': 'Ticket closed successfully and user notified via webhook'})
        except requests.exceptions.RequestException as e:
            logger.error("Failed to send webhook notification: %s", str(e))
            return JsonResponse({'message': f'Failed to send webhook notification: {e}'}, status=500)

    except json.JSONDecodeError:
        logger.error("Invalid JSON data")
        return JsonResponse({'message': 'Invalid JSON data'}, status=400)
    except SupportTicket.DoesNotExist:
        logger.error("Ticket not found: %s", ticket_id)
        return JsonResponse({'message': 'Ticket not found'}, status=404)
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        return JsonResponse({'message': f'An error occurred: {e}'}, status=500)