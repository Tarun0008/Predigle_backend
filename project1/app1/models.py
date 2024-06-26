from django.db import models
from djongo import models
import uuid             
from datetime import datetime
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password


class Agent(models.Model):
    agent_id = models.CharField(primary_key=True, max_length=36,default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)
    



class SupportTicket(models.Model):
    ticket_id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50, default='open')
    created_at = models.DateTimeField(default=datetime.now)
    user_id = models.CharField(max_length=36, null=True, blank=True)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)


class User(models.Model):
    user_id = models.CharField(primary_key=True,max_length=36, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    


class Record(models.Model):
    first = models.CharField(max_length=100)
    last = models.CharField(max_length=100)
