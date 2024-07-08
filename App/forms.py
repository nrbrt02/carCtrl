from django import forms
from App.models import User, Owner, Car, Appointment, Center, Inspection, Notification



class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ContactForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'email', 'placeholder': 'Email Address...'}))
    message= forms.Textarea(attrs={ 'class': 'form-control', 'cols': 50, 'rows': 3}),


class CreateOwnerAccountForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = '__all__'
        exclude = ['is_superuser', 'last_login', 'is_staff', 'is_active', 'date_joined', 'role', 'groups', 'user_permissions']
        widgets={
           'password': forms.PasswordInput(),
           'email': forms.EmailInput(attrs={'required': 'required'}),
           'phone_number': forms.TextInput(attrs={'value': "+250"}),
        }

    
   

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = '__all__'
        exclude = ['owner_id']
        widgets = {
            'plate': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'car_id': forms.Select(attrs={'class': 'form-control'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        exclude = ['owner_id', 'status', 'pstatus']
        widgets = {
            'date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date'}),
            'center_id': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'car_id': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        id = user.id
        super().__init__(*args, **kwargs)
        if user:
            self.fields['car_id'].queryset = Car.objects.filter(owner_id= id)

class AppointmentFormAdmin(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        exclude = ['status', 'pstatus']
        widgets = {
            'owner_id': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date'}),
            'center_id': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'type': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'car_id': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
        }

    def __init__(self, *args, **kwargs):
        super(AppointmentFormAdmin, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['owner_id'].required = False
            self.fields['center_id'].required = False
            self.fields['type'].required = False
            self.fields['car_id'].required = False
            
            self.fields['owner_id'].initial = self.instance.owner_id
            self.fields['center_id'].initial = self.instance.center_id
            self.fields['type'].initial = self.instance.type
            self.fields['car_id'].initial = self.instance.car_id

    # def save(self, commit=True):
    #     instance = super(AppointmentFormAdmin, self).save(commit=False)
    #     # Retain the values of the disabled fields
    #     if self.instance:
    #         instance.owner_id = self.instance.owner_id
    #         instance.center_id = self.instance.center_id
    #         instance.type = self.instance.type
    #         instance.car_id = self.instance.car_id
    #     if commit:
    #         instance.save()
    #     return instance


class CenterForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = '__all__'
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'operating_hours': forms.Select(attrs={'class': 'form-control'}),
            'number_of_slots_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = '__all__'
        exclude = ['appointment_id']
        widgets = {
            'result': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recomendations': forms.Textarea(attrs={ 'class': 'form-control', 'cols': 30, 'rows': 8}),
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['message']
        widget = {
            'message': forms.Textarea(attrs={ 'class': 'form-control', 'cols': 30, 'rows': 8})
        }