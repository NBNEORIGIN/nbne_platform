"""
API Views for Payment Integration
Endpoints for external payment system to interact with booking system
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Booking, Client
from .models_payment import ClassPackage, ClientCredit, PaymentTransaction
from .serializers_payment import (
    ClassPackageSerializer,
    ClientCreditSerializer,
    PaymentTransactionSerializer
)


class ClassPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ClassPackage (read-only for public)
    
    Endpoints:
    - GET /api/packages/ - List all active packages
    - GET /api/packages/{id}/ - Get package details
    """
    queryset = ClassPackage.objects.filter(active=True)
    serializer_class = ClassPackageSerializer


class ClientCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ClientCredit
    
    Endpoints:
    - GET /api/credits/ - List all credits (admin)
    - GET /api/credits/by-client/?client_id=X - Get client's credits
    - POST /api/credits/use/ - Use a credit for booking
    - POST /api/credits/refund/ - Refund a credit
    """
    queryset = ClientCredit.objects.all()
    serializer_class = ClientCreditSerializer
    
    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """
        Get all valid credits for a client
        GET /api/credits/by-client/?client_id=X
        """
        client_id = request.query_params.get('client_id')
        
        if not client_id:
            return Response(
                {'error': 'client_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        credits = ClientCredit.objects.filter(
            client_id=client_id,
            active=True,
            remaining_classes__gt=0
        ).order_by('-purchased_at')
        
        # Filter out expired credits
        valid_credits = [c for c in credits if not c.is_expired]
        
        serializer = self.get_serializer(valid_credits, many=True)
        return Response({
            'client_id': client_id,
            'total_credits': sum(c.remaining_classes for c in valid_credits),
            'credits': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def use(self, request):
        """
        Use a credit for a booking
        POST /api/credits/use/
        Body: {"credit_id": 1, "booking_id": 123}
        """
        credit_id = request.data.get('credit_id')
        booking_id = request.data.get('booking_id')
        
        if not credit_id or not booking_id:
            return Response(
                {'error': 'credit_id and booking_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        credit = get_object_or_404(ClientCredit, id=credit_id)
        booking = get_object_or_404(Booking, id=booking_id)
        
        if credit.use_credit():
            # Update booking payment status
            booking.payment_status = 'credit_used'
            booking.payment_type = 'credit'
            booking.payment_id = f"credit_{credit.id}"
            booking.status = 'confirmed'
            booking.save()
            
            return Response({
                'success': True,
                'remaining_classes': credit.remaining_classes,
                'booking_id': booking.id,
                'booking_status': booking.status
            })
        else:
            return Response(
                {'error': 'Credit not valid or already used'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def refund(self, request):
        """
        Refund a credit (e.g., booking cancelled)
        POST /api/credits/refund/
        Body: {"credit_id": 1}
        """
        credit_id = request.data.get('credit_id')
        
        if not credit_id:
            return Response(
                {'error': 'credit_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        credit = get_object_or_404(ClientCredit, id=credit_id)
        
        if credit.refund_credit():
            return Response({
                'success': True,
                'remaining_classes': credit.remaining_classes
            })
        else:
            return Response(
                {'error': 'Cannot refund credit'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentIntegrationViewSet(viewsets.ViewSet):
    """
    ViewSet for payment system integration
    Called by external payment system
    """
    
    @action(detail=False, methods=['post'])
    def confirm_payment(self, request):
        """
        Confirm payment for a booking
        Called by payment system after successful payment
        
        POST /api/payment/confirm-payment/
        Body: {
            "booking_id": 123,
            "payment_id": "stripe_pi_xxx",
            "amount": 25.00,
            "payment_type": "single_class"
        }
        """
        booking_id = request.data.get('booking_id')
        payment_id = request.data.get('payment_id')
        amount = request.data.get('amount')
        payment_type = request.data.get('payment_type', 'single_class')
        
        if not all([booking_id, payment_id, amount]):
            return Response(
                {'error': 'booking_id, payment_id, and amount required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Update booking payment status
        booking.payment_status = 'paid'
        booking.payment_id = payment_id
        booking.payment_amount = amount
        booking.payment_type = payment_type
        booking.status = 'confirmed'
        booking.save()
        
        return Response({
            'success': True,
            'booking_id': booking.id,
            'status': booking.status,
            'payment_status': booking.payment_status
        })
    
    @action(detail=False, methods=['post'])
    def create_credit(self, request):
        """
        Create credit record after package purchase
        Called by payment system after successful package purchase
        
        POST /api/payment/create-credit/
        Body: {
            "client_id": 1,
            "package_id": 2,
            "payment_id": "stripe_pi_xxx",
            "amount_paid": 100.00
        }
        """
        client_id = request.data.get('client_id')
        package_id = request.data.get('package_id')
        payment_id = request.data.get('payment_id')
        amount_paid = request.data.get('amount_paid')
        
        if not all([client_id, package_id, payment_id, amount_paid]):
            return Response(
                {'error': 'client_id, package_id, payment_id, and amount_paid required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client = get_object_or_404(Client, id=client_id)
        package = get_object_or_404(ClassPackage, id=package_id)
        
        # Create credit record
        credit = ClientCredit.objects.create(
            client=client,
            package=package,
            total_classes=package.class_count,
            remaining_classes=package.class_count,
            payment_id=payment_id,
            amount_paid=amount_paid,
            expires_at=timezone.now() + timedelta(days=package.validity_days),
            active=True
        )
        
        # Create transaction record
        transaction = PaymentTransaction.objects.create(
            client=client,
            transaction_type='purchase',
            status='completed',
            payment_system_id=payment_id,
            amount=amount_paid,
            package=package,
            credit=credit
        )
        
        serializer = ClientCreditSerializer(credit)
        return Response({
            'success': True,
            'credit': serializer.data,
            'transaction_id': transaction.id
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def booking_status(self, request):
        """
        Check payment status of a booking
        GET /api/payment/booking-status/?booking_id=123
        """
        booking_id = request.query_params.get('booking_id')
        
        if not booking_id:
            return Response(
                {'error': 'booking_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        return Response({
            'booking_id': booking.id,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'payment_id': booking.payment_id,
            'payment_amount': str(booking.payment_amount) if booking.payment_amount else None,
            'payment_type': booking.payment_type
        })
