"""
Nightly management command: update_service_intelligence
Recalculates all service performance metrics and generates pricing recommendations.
"""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F


class Command(BaseCommand):
    help = 'Recalculate service intelligence metrics and pricing recommendations'

    def handle(self, *args, **options):
        from bookings.models import Service, Booking, ServiceOptimisationLog

        now = timezone.now()
        ninety_days_ago = now - timedelta(days=90)
        thirty_days_ago = now - timedelta(days=30)

        services = Service.objects.all()
        updated = 0

        for svc in services:
            bookings = Booking.objects.filter(service=svc)
            recent = bookings.filter(start_time__gte=ninety_days_ago)

            # --- Core metrics ---
            total = recent.count()
            completed = recent.filter(status='completed').count()
            no_shows = recent.filter(status='no_show').count()
            cancelled = recent.filter(status='cancelled').count()
            ns_rate = round(no_shows / total * 100, 1) if total > 0 else 0

            revenue = recent.filter(status='completed').aggregate(
                total=Sum('service__price')
            )['total'] or Decimal('0')

            avg_value = revenue / completed if completed > 0 else Decimal('0')
            avg_risk = recent.exclude(risk_score__isnull=True).aggregate(
                avg=Avg('risk_score')
            )['avg'] or 0

            # --- Utilisation (peak = 10-14, off-peak = rest) ---
            peak_bookings = recent.filter(
                start_time__hour__gte=10, start_time__hour__lt=14
            ).count()
            off_peak_bookings = total - peak_bookings

            # Estimate capacity: 4 peak hours * 90 days / duration
            slots_per_hour = 60 / max(svc.duration_minutes, 15)
            peak_capacity = max(1, 4 * slots_per_hour * 90)
            off_peak_capacity = max(1, 6 * slots_per_hour * 90)

            peak_util = min(100, round(peak_bookings / peak_capacity * 100, 1))
            off_peak_util = min(100, round(off_peak_bookings / off_peak_capacity * 100, 1))

            # --- Demand index (30-day) ---
            recent_30 = bookings.filter(start_time__gte=thirty_days_ago).count()
            demand = min(100, round(recent_30 * 3.3, 1))  # normalise ~30 bookings/month = 100

            # --- Pricing Recommendation Engine (Phase 3) ---
            rec_price = None
            rec_deposit = None
            rec_payment = ''
            rec_reason = ''
            confidence = 0

            if total >= 3:  # need minimum data
                reasons = []

                # High utilisation + reliable clients → price increase
                if peak_util > 80:
                    avg_reliability = recent.exclude(
                        client__reliability_score__isnull=True
                    ).aggregate(avg=Avg('client__reliability_score'))['avg'] or 0

                    if avg_reliability > 70:
                        increase = round(float(svc.price) * 0.08, 2)
                        rec_price = svc.price + Decimal(str(increase))
                        reasons.append(f'Peak utilisation {peak_util:.0f}% with avg reliability {avg_reliability:.0f}% — suggest +8% price increase')
                        confidence = max(confidence, 75)
                    else:
                        increase = round(float(svc.price) * 0.05, 2)
                        rec_price = svc.price + Decimal(str(increase))
                        reasons.append(f'Peak utilisation {peak_util:.0f}% — suggest +5% price increase')
                        confidence = max(confidence, 60)

                # Low utilisation → off-peak discount
                if off_peak_util < 40 and svc.off_peak_discount_allowed:
                    reasons.append(f'Off-peak utilisation only {off_peak_util:.0f}% — suggest off-peak discount window')
                    confidence = max(confidence, 55)

                # High no-show rate → deposit/full payment
                if ns_rate > 15:
                    rec_deposit = 100
                    rec_payment = 'full'
                    reasons.append(f'No-show rate {ns_rate:.1f}% — recommend full prepayment')
                    confidence = max(confidence, 80)
                elif ns_rate > 8:
                    rec_deposit = 50
                    rec_payment = 'deposit'
                    reasons.append(f'No-show rate {ns_rate:.1f}% — recommend 50% deposit')
                    confidence = max(confidence, 65)

                # Loyalty detection
                repeat_clients = recent.values('client').annotate(
                    cnt=Count('id')
                ).filter(cnt__gte=3).count()
                if repeat_clients >= 2 and total >= 5:
                    reasons.append(f'{repeat_clients} loyal repeat clients — consider loyalty incentive')
                    confidence = max(confidence, 50)

                rec_reason = ' | '.join(reasons) if reasons else ''

            # --- Save metrics ---
            svc.total_bookings = total
            svc.total_revenue = revenue
            svc.avg_booking_value = avg_value
            svc.no_show_rate = ns_rate
            svc.avg_risk_score = round(avg_risk, 1)
            svc.peak_utilisation_rate = peak_util
            svc.off_peak_utilisation_rate = off_peak_util
            svc.demand_index = demand
            svc.recommended_base_price = rec_price
            svc.recommended_deposit_percent = rec_deposit
            svc.recommended_payment_type = rec_payment
            svc.recommendation_reason = rec_reason
            svc.recommendation_confidence = confidence
            svc.recommendation_snapshot = {
                'total_bookings': total,
                'completed': completed,
                'no_shows': no_shows,
                'cancelled': cancelled,
                'revenue': float(revenue),
                'avg_risk': round(avg_risk, 1),
                'peak_util': peak_util,
                'off_peak_util': off_peak_util,
                'demand_index': demand,
                'ns_rate': ns_rate,
            }
            svc.last_optimised_at = now
            svc.save()

            # Log if recommendation changed
            if rec_reason:
                ServiceOptimisationLog.objects.create(
                    service=svc,
                    reason=rec_reason,
                    ai_recommended=True,
                    owner_override=False,
                    input_metrics=svc.recommendation_snapshot,
                    output_recommendation={
                        'recommended_price': float(rec_price) if rec_price else None,
                        'recommended_deposit': rec_deposit,
                        'recommended_payment': rec_payment,
                        'confidence': confidence,
                    },
                )

            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated intelligence for {updated} services'))
