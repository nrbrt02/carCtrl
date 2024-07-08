from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('create-account', views.createAccount, name="create-account"),
    path('login', views.loginAccount, name="login"),
    path('logout', views.logoutAc, name="logoutAc"),


    path('owner', views.ownerHome, name="owner-home"),
    path('owner/cars', views.owner_cars, name="owner-cars"),
    path('owner/cars/edit/<int:pk>/', views.owner_cars_edit, name="owner-cars-edit"),
    path('owner/cars/delete/<int:pk>/', views.owner_cars_delete, name="owner-cars-delete"),
    path('owner/appointment', views.owner_appointment, name="owner-appointment"),
    path('owner/appointment/edit/<int:pk>/', views.change_appt_date, name="change-appt-date"),
    path('owner/appointment/cancle/<int:pk>/', views.cancle_appt, name="cancle-appt"),
    path('owner/inspections', views.owner_inspections, name="owner-inspection"),
    path('owner/inspections/<int:pk>', views.owner_inspections_view, name="owner-inspection-view"),
    path('owner/notifications/', views.owner_notifications, name="owner-notifications"),
    path('owner/notifications/<int:pk>', views.view_notification, name="view-notification"),



    path('checkout/<int:pk>/', views.checkout, name = "checkout"),
    path('payment-success/<int:pk>/', views.paymentSuccessful, name = "payment-successful"),
    path('payment-failed/<int:pk>/', views.paymentFailed, name = "payment-failed"),

    path('adminn', views.adminHome, name="admin-home"),
    path('adminn/center', views.center, name="center"),
    path('adminn/center/delete/<int:pk>/', views.deleteCenter, name="delete-center"),
    path('adminn/center/edit/<int:pk>/', views.updateCenter, name="update-center"),
    path('adminn/appointments', views.adminAppointments, name="admin-appointment"),
    path('adminn/appointment/edit/<int:pk>/', views.change_appt_date_admin, name="change-appt-date-admin"),
    path('adminn/appointment/cancle/<int:pk>/', views.cancle_appt_admin, name="cancle-appt-admin"),
    path('adminn/inspections', views.admin_inspections, name="admin-inspections"),
    path('adminn/inspections/add/<int:pk>/', views.add_inspections, name="add-inspections"),
    path('adminn/notifications', views.notifications, name="notofications"),
    path('adminn/notifications/send/<int:pk>', views.send_notifications, name="send-notofications"),
    
    path('', views.home, name="home"),
]
