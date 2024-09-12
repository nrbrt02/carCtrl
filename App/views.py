from django.shortcuts import render, redirect, get_object_or_404, redirect
from .models import Owner, User, Car, Appointment, Center, Inspection, Notification
from .forms import CreateOwnerAccountForm, LoginForm, CarForm, AppointmentForm, CenterForm, AppointmentFormAdmin, InspectionForm, NotificationForm, ContactForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import datetime
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
import uuid
from django.urls import reverse
from django.db.models import Count

# Create your views here.


def createAccount(request):

    form = CreateOwnerAccountForm()
    if request.method == 'POST':
        form = CreateOwnerAccountForm(request.POST)
        confirm_password = request.POST.get('cpassword')
        if form.is_valid():
            password = form.cleaned_data.get('password')
            if password != confirm_password:
                form.add_error('password', 'Passwords do not match.')
            else:
                owner = form.save(commit=False)
                owner.role = User.Role.OWNER
                owner.password = make_password(password)
                owner.save()
                messages.success(request, "Account created successfuly. Now login")
                return redirect('login') 
        else:
            messages.error(request, f"{form.errors.as_text}")

    contex = {'form': form}
    return render(request, "create-account.html", contex)


def loginAccount(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username = username, password=password)

            if user is not None:
                if user.role == "ADMIN":
                    login(request, user)
                    return redirect('admin-home')
                elif user.role == "OWNER":
                    login(request, user)
                    return redirect('owner-home')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid Clidentials")
    contex = {'form': form}
    return render(request, "login.html", contex)


@login_required(login_url='login')
def logoutAc(request):
    logout(request)
    return redirect('home') 

@login_required(login_url='login')
def ownerHome(request):
    appointments = Appointment.objects.filter(status='pendig', owner_id = request.user.id).count()
    cars = Car.objects.filter(owner_id = request.user.id).count()
    notifications = Notification.objects.filter(status=0, message_to = request.user.id).count()
    inspections = Inspection.objects.filter(appointment_id__owner_id=request.user.id).count()
    context = {'cars': cars, 'appointments': appointments, 'notifications': notifications, 'inspections': inspections} 
    return render(request, "owner-home.html", context)


@login_required(login_url='login')
def owner_notifications(request):
    notifications = Notification.objects.filter(message_to = request.user.id)
    context = {'notifications': notifications}
    return render(request, "owner-notifications.html", context)

@login_required(login_url='login')
def view_notification(request, pk):
    notification = Notification.objects.get(id=pk)
    notification.status = True
    notification.save()
    context = {'notification': notification}
    return render(request, "view-notification.html", context)


@login_required(login_url='login')
def owner_cars(request):
    form = CarForm()
    owner = Owner.objects.get(id = request.user.id)
    cars = Car.objects.filter(owner_id = owner.id)
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save(commit=False)
            car.owner_id = owner
            car.save()
            send_mail("New Car Added", f"From AutoMobile Inspection Center \n Your Account has been linked with a new car with the following information\n plate: {car.plate}\n Model: {car.model}\n Make: {car.make}\n Thank you.", settings.EMAIL_HOST_USER, [owner.email])
            messages.success(request, "Car Added To your Account")
            form = CarForm()
        else:
            messages.error(request, f"{form.errors.as_text()}")
    context = {'form': form, 'cars': cars}
    return render(request, 'owner-cars.html', context)



@login_required(login_url='login')
def owner_cars_edit(request, pk):
    car = Car.objects.get(id=pk)
    owner = Owner.objects.get(id = request.user.id)
    cars = Car.objects.filter(owner_id = owner.id)
    form = CarForm()
    if request.user.id == car.owner_id.id:
        form = CarForm(instance=car)
        if request.method == "POST":
            form = CarForm(request.POST, instance=car)
            if form.is_valid():
                car.save()
                send_mail("Car Edited", f"From AutoMobile Inspection Center \n A car in your Account has been Updated from \nplate: {car.plate}\n Model: {car.model}\n Make: {car.make}\n  to Plate: {form.cleaned_data['plate']}\n Model:{form.cleaned_data['model']}\n Make: {form.cleaned_data['make']}\n Thank you.", settings.EMAIL_HOST_USER, [owner.email])
                messages.success(request, "Car Updated")
                return redirect('owner-cars')
            else:
                messages.error(request, f"{form.errors.as_text}")
    else:
        messages.error(request, "You dont have permission to perform this action")
    context = {'form': form, 'cars': cars}
    return render(request, 'owner-cars-edit.html', context)


@login_required(login_url='login')
def owner_cars_delete(request, pk):
    car = Car.objects.get(id=pk)
    if request.user.id == car.owner_id.id:
        car.delete()
        send_mail("Car Deleted", f"From AutoMobile Inspection Center \n A car with n plate: {car.plate}\n Model: {car.model}\n Make: {car.make}\n has been unlinked with our account Thank you.", settings.EMAIL_HOST_USER, [request.user.email])
        messages.success(request, f"Car with Plate {car.plate} Deleted Successfuly")
    else:
        messages.error(request, "You dont have permission to perform this action")

    return redirect('owner-cars')


@login_required(login_url='login')
def owner_appointment(request):
    form = AppointmentForm(user=request.user)
    appointments = Appointment.objects.filter(owner_id=request.user.id)
    owner = Owner.objects.get(id=request.user.id)  # Ensure correct fetching of the Owner instance

    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appt = form.save(commit=False)

            # Checking the number of slots available
            selected_center = appt.center_id  # Use the selected center from the form
            number_of_appointments = Appointment.objects.filter(
                date=appt.date,  # Using double underscore for field lookup
                center_id=selected_center
            ).count()

            existing_appointment = Appointment.objects.filter(date=appt.date,  owner_id = owner.id,  car_id= appt.car_id.id).count()
            if existing_appointment != 0:
                messages.error(request, f"Already has an appointment on this day")
            elif selected_center.number_of_slots_per_day <= number_of_appointments:    
                messages.error(request, f"No available slots on this day at {selected_center.name}. Please find another day.")
            elif datetime.date.today() >= appt.date:
                messages.error(request, f"Invalid date. Make sure to pick a date in the future and no weekends")
            else: 
                appt.owner_id = owner  # Ensure you assign the correct owner instance
                appt.save()
                appt_id = appt.id
                send_mail("New Appointment Booked", f"From AutoMobile Inspection Center- Appointments \n Your Account has booked an inspection for a car with informations:\nappointment id: {appt_id}\nplate: {appt.car_id.plate}\n Model: {appt.car_id.model}\n Make: {appt.car_id.make}\n Here are the information about your appointment\n Canter:{appt.center_id}\n Date:{appt.date}\nType:{appt.type}\n Make sure to note miss the appointment\n Thank you.", settings.EMAIL_HOST_USER, [request.user.email])
                messages.success(request, "Appointment started, proceed with payment")
                form = AppointmentForm(user=request.user)
                return redirect('checkout', pk=appt_id) 

        else:
            messages.error(request, f"{form.errors.as_text()}")

    context = {'form': form, 'appointments': appointments}
    return render(request, "appointment.html", context)


@login_required(login_url='login')
def change_appt_date(request, pk):
    appt = Appointment.objects.get(id=pk)
    appts = Appointment.objects.filter(owner_id = request.user.id)
    form = AppointmentForm(user=request.user)
    if request.user.id == appt.owner_id.id:
        # appts = Appointment.objects.all()
        form = AppointmentForm(instance=appt, user=request.user)
        if request.method == 'POST':
            form = AppointmentForm(request.POST, instance=appt, user=request.user)
            if form.is_valid():
                form.save()
                send_mail("Appointment Date Changed", f"From AutoMobile Inspection Center- Appointments \n The Date for an appointment in your Account has been  change from {appt.date} to {form.cleaned_data['date']}for inspection f a car with informations:\nplate: {appt.car_id.plate}\n Model: {appt.car_id.model}\n Make: {appt.car_id.make}\n Here are the new information about your appointment\n Canter:{form.cleaned_data['center_id']}\n Date:{form.cleaned_data['date']}\nType:{form.cleaned_data['date']}\n Make sure to note miss the appointment\n Thank you.", settings.EMAIL_HOST_USER, [request.user.email])
                messages.success(request, "Appointment Updated")
                return redirect("owner-appointment")
            else:
                messages.error(request, f"{form.errors.as_text()}")
    else:
        messages.error(request, f"You have No permissions to perform this action")
    
    contex = {'form': form, 'appointments': appts}
    return render(request, 'owner-edit-appointment.html', contex)
        

@login_required(login_url='login')
def cancle_appt(request, pk):
    appt = Appointment.objects.get(id=pk)
    if request.user.id == appt.owner_id.id:
        appt.status = "cancled"
        appt.save()
        send_mail("Appointment Canceld", f"From AutoMobile Inspection Center- Appointments \n Ampointment which was supposed to take place at {appt.date}\nwas cancled Thank you.", settings.EMAIL_HOST_USER, [request.user.email])
        messages.success(request, "Appointment Cancled successfuly")
    else:
        messages.error(request, f"You have No permissions to perform this action")
    return redirect('owner-appointment')

@login_required(login_url='login')
def owner_inspections(request):
    # inspections = Inspection.objects.filter(appointment_id.id == request.user.id)
    inspections = Inspection.objects.all()
    # print(inspections)
    context = {'inspections': inspections}
    return render(request, "owner-insepections.html", context)

@login_required(login_url='login')
def owner_inspections_view(request, pk):
    inspection = Inspection.objects.get(id=pk)
    context={'inspection': inspection}
    return render(request, "view-inspection.html", context)








@login_required(login_url='login')
def adminHome(request):
    center = Center.objects.all().count()
    appointments = Appointment.objects.filter(status='pendig').count()
    inspections = Inspection.objects.all().count()

    pas_insp  = Inspection.objects.filter(result=True).count()
    fail_insp = Inspection.objects.filter(result=False).count()
    insp_list = ['Pass', 'Fail']
    insp_numbers = [pas_insp, fail_insp]

    all_apt = Appointment.objects.all().count()
    comp_appt = Appointment.objects.filter(status="complite").count()
    pend_appt = Appointment.objects.filter(status="pendig").count()
    canc_appt = Appointment.objects.filter(status="cancled").count()
    pay_appt = Appointment.objects.filter(pstatus=True).count()
    nopay_appt = Appointment.objects.filter(pstatus=False).count()

    appt_list = ["All", "Inspected", "Failed", "Passed", "Upcoming","Cancled"]
    appt_numbers = [all_apt, inspections, fail_insp, pas_insp, pend_appt, canc_appt]

    context = {'centers': center, 'appointments': appointments, 'inspections': inspections, 'insp_list': insp_list, 'insp_numbers': insp_numbers, "appt_list": appt_list, "appt_numbers": appt_numbers} 

    # appt_list = ["Complited", "Pending", "Cancled", "Payed", "Not Payed"]
    # appt_numbers = [comp_appt, pend_appt, canc_appt, pay_appt, nopay_appt]

    # context = {'centers': center, 'appointments': appointments, 'inspections': inspections, 'insp_list': insp_list, 'insp_numbers': insp_numbers, "appt_list": appt_list, "appt_numbers": appt_numbers} 
    return render(request, "admin-home.html", context)


@login_required(login_url='login')
def center(request):
    centers = Center.objects.all()
    form = CenterForm()
    
    if request.method == 'POST':
        form = CenterForm(request.POST)
        if form.is_valid():
            center = form.save()
            messages.success(request, "New Inspection Center Created")
            form = CenterForm()
        else:
            messages.error(request, f"{form.errors.as_text()}")    
    contex = {'form': form, 'centers': centers}
    return render(request, 'center.html', contex)

@login_required(login_url='login')
def deleteCenter(request, pk):
    center = Center.objects.get(id=pk)
    center.delete()
    messages.success(request, f"{center.name} Deleted Successfuly")
    return redirect('center')


@login_required(login_url='login')
def updateCenter(request, pk):
    centers = Center.objects.all()
    center = Center.objects.get(id=pk)
    form = CenterForm(instance=center)
    
    if request.method == 'POST':
        form = CenterForm(request.POST, instance=center)
        if form.is_valid():
            form.save()
            messages.success(request, "Inspection Center Updated")
            return redirect("center")
        else:
            messages.error(request, f"{form.errors.as_text}")    
    contex = {'form': form, 'centers': centers}
    return render(request, 'update-center.html', contex)


@login_required(login_url='login')
def adminAppointments(request):
    appts = Appointment.objects.all().order_by('-date')
    context = {'appointments': appts}
    return render(request, 'admin-appointments.html', context)



@login_required(login_url='login')
def change_appt_date_admin(request, pk):
    appt = Appointment.objects.get(id=pk)
    email = appt.owner_id.email
    appts = Appointment.objects.filter()
    if request.method == 'POST':
        form = AppointmentFormAdmin(request.POST, instance=appt)
        if form.is_valid():
            apt = form.save(commit=False)
            
            if datetime.date.today() >= apt.date:
                messages.error(request, f"Invalid date. Make sure to pick a date in the future and no weekends")
            else:
                send_mail("Appointment Changed", f"From AutoMobile Inspection Center- An appointment you had on {appt.date} of vehicle inspection has been changed to a new date{apt.date} by administrator\n Thank you.", settings.EMAIL_HOST_USER, [email])
                messages.success(request, "Appointment Updated")
                return redirect("admin-appointment")
        else:
            messages.error(request, f"{form.errors.as_text()}")
    else:
        form = AppointmentFormAdmin(instance=appt)
    
    context = {'form': form, 'appointments': appts}
    return render(request, 'admin-edit-appointment.html', context)

@login_required(login_url='login')
def cancle_appt_admin(request, pk):
    appt = Appointment.objects.get(id=pk)
    appt.status = "cancled"
    appt.save()
    send_mail("Appointment Canceld by Admin", f"From AutoMobile Inspection Center- Appointments \n Appointment which was supposed to take place at {appt.date}\nwas cancled by admin Thank you.", settings.EMAIL_HOST_USER, [appt.owner_id.email])
    messages.success(request, "Appointment Cancled successfuly")
    return redirect('admin-appointment')

@login_required(login_url='login')
def admin_inspections(request):
    inspts = Inspection.objects.all()
    context = {'inspections': inspts}
    return render(request, "admin-inspections.html", context)

@login_required(login_url='login')
def add_inspections(request, pk):
    appt = Appointment.objects.get(id=pk)
    form = InspectionForm()
    if request.method == 'POST':
        form = InspectionForm(request.POST)
        if form.is_valid():
            insp = form.save(commit=False)
            insp.appointment_id = appt
            insp.save()
            send_mail("Inspection Results", f"From AutoMobile Inspection Center- Inspections \n from an inspection done on {appt.date} from the results here is your inspections results\n Result: {form.cleaned_data['result']}\n Recomendations: {form.cleaned_data['recomendations']}\n We look forward on our next inspection stay safe\n Thank you", settings.EMAIL_HOST_USER, [appt.owner_id.email])
            Appointment.objects.filter(pk=pk).update(status="complite")
            messages.success(request, "Inspection Added")
            return redirect("admin-appointment")
    else:
        messages.error(request, f"{form.errors.as_text()}")
    context = {'appointment': appt, 'form': form}
    return render(request, "add-inspections.html", context)

@login_required(login_url='login')
def notifications(request):
    users = User.objects.filter(role = "OWNER")
    context = {"users": users}
    return render(request, "admin-notification.html", context)


@login_required(login_url='login')
def send_notifications(request, pk):
    user_to = Owner.objects.get(id = pk)
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            to_phone = user_to.phone_number[1:]
            message = form.save(commit=False)
            message.message_to = user_to
            message.message_from = request.user
            message.save()
            # responseData = sms.send_message({"from": "CarCtrl - Message from Admin", "to": to_phone,"text": message.message })
            # if responseData["messages"][0]["status"] == "0":
            #     print("Message sent successfully.")
            send_mail("Inspection Message from Admin", f"Admin {request.user.username} sent you the following message \n{form.cleaned_data['message']}\n Thank you", settings.EMAIL_HOST_USER, [user_to.email])
            messages.success(request, "Notification Sent")
            return redirect("notofications")
        else:
            messages.error(request, f"{form.errors.as_text()}")
    else:
        form = NotificationForm()
        context = {"form": form}
        return render(request, "send_notification.html", context)


def home(request):
    if request.method == 'POST':
      email = request.POST.get('email')
      message = request.POST.get('message')
      send_mail(
                  "support Email",
                  message +"\n from --"+email,
                  settings.EMAIL_HOST_USER,
                  ['normuyomba@gmail.com'],
                  fail_silently=False,
               )
      messages.success(request, "Your message has been submitted successfully! we'll contact you as soon")
    return render(request, "index.html")




def checkout(request, pk):
    appointment = Appointment.objects.get(id=pk)
    host = request.get_host()
    payment_amount = 0
    if appointment.type == "first":
        payment_amount = 19.14
    else:
        payment_amount = 11.48
    paypal_checkout = {
      'business': settings.PAYPAL_RECEIVER_EMAIL,
      'amount': payment_amount,
      'court_name': appointment.center_id.name,
      'invoice': uuid.uuid4(),
      'currency_code': 'USD',
      'notify_url': f"http://{host}{reverse('paypal-ipn')}",
      'return_url': f"http://{host}{reverse('payment-successful', kwargs={'pk':appointment.pk})}",
      'cancle_url': f"http://{host}{reverse('payment-failed', kwargs={'pk':appointment.pk})}"
    }

    paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)
    context = {'appointment': appointment, 'paypal': paypal_payment}
   
    return render(request, 'chekout.html',context)


def paymentSuccessful(request, pk):
    appointment = Appointment.objects.get(id=pk)
    payment_amount = 0
    if appointment.type == "first":
        payment_amount = 25000
    else:
        payment_amount = 15000
    if not appointment.pstatus:
        appointment.pstatus = True
        appointment.save()
        send_mail(
                    "Appointment Payment Successful",
                    "You have complited you appointment scheduling process \nDo not miss the date \n Thank you ",
                    settings.EMAIL_HOST_USER,
                    [appointment.owner_id.email],
                    fail_silently=False,
                )
    context = {'appointment': appointment, 'payment_amount': payment_amount}
    return render(request, 'payment-successful.html', context)


def paymentFailed(request, pk):
   booking = Booking.objects.get(id=pk)
   context = {'booking': booking}
   return render(request, 'payment-failed.html', context)