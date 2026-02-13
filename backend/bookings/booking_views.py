from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Service, Staff, Client, Booking
from core.models import Config
import requests
from datetime import datetime, timedelta


def get_branding():
    """Get branding config for templates"""
    branding = {}
    for config in Config.objects.filter(category='branding'):
        key = config.key.replace('branding.', '')
        branding[key] = config.value
    return branding


def booking_service_select(request):
    """Step 1: Select service"""
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        request.session['booking_service_id'] = service_id
        return redirect('booking_staff_select')
    
    services = Service.objects.filter(active=True)
    branding = get_branding()
    
    return render(request, 'bookings/service_select.html', {
        'services': services,
        'branding': branding,
    })


def booking_staff_select(request):
    """Step 2: Select staff member"""
    service_id = request.session.get('booking_service_id')
    if not service_id:
        return redirect('booking_service_select')
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        request.session['booking_staff_id'] = staff_id
        return redirect('booking_time_select')
    
    service = get_object_or_404(Service, id=service_id, active=True)
    staff_members = Staff.objects.filter(active=True, services=service)
    branding = get_branding()
    
    return render(request, 'bookings/staff_select.html', {
        'service': service,
        'staff_members': staff_members,
        'branding': branding,
    })


def booking_time_select(request):
    """Step 3: Select date and time"""
    service_id = request.session.get('booking_service_id')
    staff_id = request.session.get('booking_staff_id')
    
    if not service_id or not staff_id:
        return redirect('booking_service_select')
    
    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        request.session['booking_date'] = selected_date
        request.session['booking_time'] = selected_time
        return redirect('booking_details')
    
    service = get_object_or_404(Service, id=service_id, active=True)
    
    if staff_id == 'any':
        staff = None
        staff_name = 'Any Professional'
    else:
        staff = get_object_or_404(Staff, id=staff_id, active=True)
        staff_name = staff.name
    
    branding = get_branding()
    
    # Generate date options (next 14 days)
    today = datetime.now().date()
    dates = []
    for i in range(14):
        date = today + timedelta(days=i)
        dates.append({
            'date': date.strftime('%Y-%m-%d'),
            'display': date.strftime('%a, %b %d'),
            'is_today': i == 0,
        })
    
    return render(request, 'bookings/time_select.html', {
        'service': service,
        'staff': staff,
        'staff_id': staff_id,
        'staff_name': staff_name,
        'dates': dates,
        'branding': branding,
    })


def booking_get_slots(request):
    """API endpoint to get available slots for a date"""
    service_id = request.GET.get('service_id')
    staff_id = request.GET.get('staff_id')
    date = request.GET.get('date')
    
    if not all([service_id, staff_id, date]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    # Call internal API
    try:
        response = requests.get(
            f'http://localhost:8000/api/bookings/slots/',
            params={'service_id': service_id, 'staff_id': staff_id, 'date': date}
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def booking_details(request):
    """Step 4: Enter customer details"""
    service_id = request.session.get('booking_service_id')
    staff_id = request.session.get('booking_staff_id')
    booking_date = request.session.get('booking_date')
    booking_time = request.session.get('booking_time')
    
    if not all([service_id, staff_id, booking_date, booking_time]):
        return redirect('booking_service_select')
    
    if request.method == 'POST':
        # Create or get client
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        notes = request.POST.get('notes', '')
        consent_booking = request.POST.get('consent_booking') == 'on'
        consent_marketing = request.POST.get('consent_marketing') == 'on'
        
        if not all([name, email, phone]) or not consent_booking:
            error = 'Please fill all required fields and accept booking communications.'
            service = get_object_or_404(Service, id=service_id)
            staff = None if staff_id == 'any' else get_object_or_404(Staff, id=staff_id)
            branding = get_branding()
            
            return render(request, 'bookings/details.html', {
                'service': service,
                'staff': staff,
                'staff_id': staff_id,
                'booking_date': booking_date,
                'booking_time': booking_time,
                'error': error,
                'branding': branding,
            })
        
        # Get or create client
        client, created = Client.objects.get_or_create(
            email=email,
            defaults={'name': name, 'phone': phone, 'notes': notes}
        )
        
        if not created:
            client.name = name
            client.phone = phone
            if notes:
                client.notes = notes
            client.save()
        
        # Create booking
        service = get_object_or_404(Service, id=service_id)
        staff = None if staff_id == 'any' else get_object_or_404(Staff, id=staff_id)
        
        # If "any" staff, pick first available
        if not staff:
            staff = Staff.objects.filter(active=True, services=service).first()
        
        start_time = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M:%S")
        
        booking = Booking.objects.create(
            client=client,
            service=service,
            staff=staff,
            start_time=start_time,
            status='pending',
            notes=f"Consent: Booking={consent_booking}, Marketing={consent_marketing}. {notes}"
        )
        
        request.session['booking_id'] = booking.id
        request.session['consent_marketing'] = consent_marketing
        
        return redirect('booking_confirm')
    
    service = get_object_or_404(Service, id=service_id)
    staff = None if staff_id == 'any' else get_object_or_404(Staff, id=staff_id)
    branding = get_branding()
    
    return render(request, 'bookings/details.html', {
        'service': service,
        'staff': staff,
        'staff_id': staff_id,
        'booking_date': booking_date,
        'booking_time': booking_time,
        'branding': branding,
    })


def booking_confirm(request):
    """Step 5: Confirmation page"""
    booking_id = request.session.get('booking_id')
    
    if not booking_id:
        return redirect('booking_service_select')
    
    booking = get_object_or_404(Booking, id=booking_id)
    branding = get_branding()
    
    # Clear session
    for key in ['booking_service_id', 'booking_staff_id', 'booking_date', 'booking_time', 'booking_id']:
        request.session.pop(key, None)
    
    return render(request, 'bookings/confirm.html', {
        'booking': booking,
        'branding': branding,
    })
