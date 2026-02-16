import uuid
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, SetPasswordSerializer,
)
from .permissions import IsManagerOrAbove, IsOwner


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current authenticated user's profile."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_me(request):
    """Update the current user's profile."""
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password."""
    serializer = PasswordChangeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(serializer.validated_data['old_password']):
        return Response({'old_password': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({'message': 'Password changed successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    """Set a new password on first login (must_change_password=True). No old password required."""
    if not request.user.must_change_password:
        return Response({'error': 'Password change not required.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = SetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.must_change_password = False
    request.user.save(update_fields=['password', 'must_change_password'])
    return Response({'message': 'Password set successfully.'})


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def user_list(request):
    """List all users (managers/owners only). Supports ?role= filter."""
    tenant = getattr(request, 'tenant', None)
    users = User.objects.filter(tenant=tenant)
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsOwner])
def user_create(request):
    """Create a new user (owners only)."""
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def user_detail(request, user_id):
    """Get a user's profile (managers/owners only)."""
    try:
        tenant = getattr(request, 'tenant', None)
        user = User.objects.get(id=user_id, tenant=tenant)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsOwner])
def user_update_role(request, user_id):
    """Update a user's role (owners only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    new_role = request.data.get('role')
    if new_role not in dict(User.ROLE_CHOICES):
        return Response({'error': f'Invalid role. Choose from: {", ".join(dict(User.ROLE_CHOICES).keys())}'}, status=status.HTTP_400_BAD_REQUEST)

    if user == request.user and new_role != 'owner':
        return Response({'error': 'Cannot demote yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    user.role = new_role
    user.save(update_fields=['role'])
    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsOwner])
def user_deactivate(request, user_id):
    """Deactivate a user (owners only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if user == request.user:
        return Response({'error': 'Cannot deactivate yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    user.is_active = False
    user.save(update_fields=['is_active'])
    return Response({'message': f'User {user.username} deactivated.'})


# ========== GDPR ENDPOINTS ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_export(request):
    """
    GDPR Article 15 — Subject Access Request.
    Returns all personal data held for the authenticated user within their tenant.
    """
    user = request.user
    tenant = getattr(request, 'tenant', None)

    # Log the export event
    _log_gdpr_event(user, tenant, 'DATA_EXPORT', 'User requested data export')

    export = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'role': user.role,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'tenant': {
            'slug': tenant.slug if tenant else None,
            'business_name': tenant.business_name if tenant else None,
        },
    }

    # Bookings (as client)
    try:
        from bookings.models import Booking
        bookings = Booking.objects.filter(
            tenant=tenant, client__email=user.email
        ).select_related('service', 'staff')
        export['bookings'] = [{
            'id': b.id,
            'service': b.service.name,
            'staff': b.staff.name if b.staff else None,
            'start_time': b.start_time.isoformat(),
            'end_time': b.end_time.isoformat(),
            'status': b.status,
            'notes': b.notes,
        } for b in bookings]
    except Exception:
        export['bookings'] = []

    # Staff profile
    try:
        from staff.models import StaffProfile
        profile = StaffProfile.objects.filter(tenant=tenant, user=user).first()
        if profile:
            export['staff_profile'] = {
                'display_name': profile.display_name,
                'phone': profile.phone,
                'hire_date': profile.hire_date.isoformat() if profile.hire_date else None,
                'is_active': profile.is_active,
            }
    except Exception:
        pass

    # Comms messages
    try:
        from comms.models import Message
        messages = Message.objects.filter(
            channel__tenant=tenant, author=user
        ).order_by('-created_at')[:100]
        export['messages'] = [{
            'channel': m.channel.name,
            'body': m.body,
            'created_at': m.created_at.isoformat(),
        } for m in messages]
    except Exception:
        export['messages'] = []

    # Documents uploaded by user
    try:
        from documents.models import Document
        docs = Document.objects.filter(tenant=tenant, uploaded_by=user)
        export['documents_uploaded'] = [{
            'id': d.id,
            'title': d.title,
            'category': d.category,
            'created_at': d.created_at.isoformat(),
        } for d in docs]
    except Exception:
        export['documents_uploaded'] = []

    # Business events performed by user
    try:
        from core.models_events import BusinessEvent
        events = BusinessEvent.objects.filter(
            tenant=tenant, performed_by=user
        ).order_by('-created_at')[:200]
        export['business_events'] = [{
            'event_type': e.event_type,
            'action_label': e.action_label,
            'created_at': e.created_at.isoformat(),
        } for e in events]
    except Exception:
        export['business_events'] = []

    export['exported_at'] = timezone.now().isoformat()

    return Response(export)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def data_erase(request):
    """
    GDPR Article 17 — Right to Erasure.
    Anonymises the authenticated user's personal data within their tenant.
    Does NOT delete transactional records (bookings, payments) — anonymises them instead.
    Requires confirmation: { "confirm": true }
    """
    if not request.data.get('confirm'):
        return Response(
            {'error': 'You must send {"confirm": true} to proceed with data erasure.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    tenant = getattr(request, 'tenant', None)

    # Log BEFORE anonymising
    _log_gdpr_event(user, tenant, 'DATA_ERASURE', f'User {user.email} requested erasure')

    anon_id = uuid.uuid4().hex[:8]
    original_email = user.email

    # 1. Anonymise client records linked by email
    try:
        from bookings.models import Client
        Client.objects.filter(tenant=tenant, email=original_email).update(
            name='[erased]', email=f'erased-{anon_id}@erased.local',
            phone='', notes='',
        )
    except Exception:
        pass

    # 2. Anonymise comms messages
    try:
        from comms.models import Message
        Message.objects.filter(channel__tenant=tenant, author=user).update(
            body='[erased]'
        )
    except Exception:
        pass

    # 3. Anonymise staff profile
    try:
        from staff.models import StaffProfile
        StaffProfile.objects.filter(tenant=tenant, user=user).update(
            display_name='[erased]', phone='',
            emergency_contact_name='', emergency_contact_phone='',
            notes='',
        )
    except Exception:
        pass

    # 4. Anonymise the user account itself
    user.first_name = '[erased]'
    user.last_name = ''
    user.email = f'erased-{anon_id}@erased.local'
    user.phone = ''
    user.bio = ''
    user.is_active = False
    user.set_unusable_password()
    user.save()

    return Response({
        'message': 'Your personal data has been erased. Your account has been deactivated.',
        'erased_at': timezone.now().isoformat(),
    })


def _log_gdpr_event(user, tenant, action, detail):
    """Log a GDPR action as a BusinessEvent for audit trail."""
    try:
        from core.models_events import BusinessEvent
        BusinessEvent.log(
            event_type='GDPR_ACTION',
            action_label=action,
            user=user,
            action_detail=detail,
            tenant=tenant,
            payload={'user_id': user.id, 'email': user.email},
        )
    except Exception:
        pass
