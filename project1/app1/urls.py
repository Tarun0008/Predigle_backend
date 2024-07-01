from django.urls import path,re_path
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Support Ticket API",
        default_version='v1',
        description="API documentation for the Support Ticket system",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



urlpatterns=[

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    #path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('',views.index),
    path('add/',views.add_detail),
    ##path('show/',views.all_person),
    path('user/<str:username>/<str:email>/<str:password>/',views.add_user),
    #path('ticket/<str:subject>/<str:description>/',views.add_ticket),
    path('delete/<str:ticket_id>/',views.delete_ticket),
    path('update_user/<str:user_id>/', views.update_user),
    path('search/',views.search_tickets),
    path('add_agent/', views.add_agent),
    path('login/',views.login_user),
    path('webhook/', views.webhook_receiver),
    path('ticket/close/',views.close_ticket),
    path('update_agent/<str:agent_id>/', views.update_agent),
    path('all/<str:tk>/',views.support_ticket_detail),
    path('myticket/',views.use_tickets),
    path('agent/<str:agt>/',views.agent_tickets),
    path('mytickets/<str:subject>/<str:description>/',views.user_tickets)

]