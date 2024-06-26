from django.urls import path,re_path
from . import views

urlpatterns=[

    path('',views.index),
    path('add/',views.add_detail),
    path('show/',views.all_person),
    path('ticket/<str:customer_name>/<str:email>/<str:subject>/<str:description>/',views.add_ticket),
    re_path(r'^ticket/delete/(?P<ticket_id>[0-9a-f-]+)/$', views.delete_ticket, name='delete_ticket'),
    re_path(r'^ticket/update/(?P<ticket_id>[0-9a-f-]+)/$', views.update_ticket, name='update_ticket'),

]