"""
Phase 8: Compliance Intelligence test scenarios.
Tests the Peace of Mind Score calculation engine.
"""
from django.test import TestCase
from .models import ComplianceCategory, ComplianceItem, PeaceOfMindScore, ScoreAuditLog


class PeaceOfMindScoreTests(TestCase):
    """Test the scoring algorithm against all specified scenarios."""

    def setUp(self):
        self.cat_fire = ComplianceCategory.objects.create(name='Fire Safety', max_score=10, order=1)
        self.cat_first_aid = ComplianceCategory.objects.create(name='First Aid', max_score=10, order=2)

    def _create_items(self, legal_statuses, bp_statuses):
        """Helper: create LEGAL items and BEST_PRACTICE items with given statuses."""
        items = []
        for i, status in enumerate(legal_statuses):
            items.append(ComplianceItem.objects.create(
                title=f'Legal Item {i+1}',
                category=self.cat_fire,
                item_type='LEGAL',
                status=status,
            ))
        for i, status in enumerate(bp_statuses):
            items.append(ComplianceItem.objects.create(
                title=f'BP Item {i+1}',
                category=self.cat_first_aid,
                item_type='BEST_PRACTICE',
                status=status,
            ))
        return items

    def test_case1_all_compliant_score_100(self):
        """Case 1: All compliant → Score 100"""
        self._create_items(
            legal_statuses=['COMPLIANT'] * 5,
            bp_statuses=['COMPLIANT'] * 5,
        )
        # Signal auto-recalculates, but let's be explicit
        result = PeaceOfMindScore.recalculate()
        self.assertEqual(result.score, 100)

    def test_case2_one_legal_overdue_noticeable_drop(self):
        """Case 2: One LEGAL overdue → noticeable score drop"""
        self._create_items(
            legal_statuses=['COMPLIANT', 'COMPLIANT', 'COMPLIANT', 'COMPLIANT', 'OVERDUE'],
            bp_statuses=['COMPLIANT'] * 5,
        )
        result = PeaceOfMindScore.recalculate()
        # Total weight: 5×2 + 5×1 = 15
        # Achieved: 4×2 + 0 + 5×1 = 13
        # Score: 13/15 = 86.67 → 87
        self.assertEqual(result.score, 87)
        self.assertLess(result.score, 100)

    def test_case3_one_bp_overdue_moderate_drop(self):
        """Case 3: Only BEST_PRACTICE overdue → moderate drop"""
        self._create_items(
            legal_statuses=['COMPLIANT'] * 5,
            bp_statuses=['COMPLIANT', 'COMPLIANT', 'COMPLIANT', 'COMPLIANT', 'OVERDUE'],
        )
        result = PeaceOfMindScore.recalculate()
        # Total weight: 10 + 5 = 15
        # Achieved: 10 + 4 = 14
        # Score: 14/15 = 93.33 → 93
        self.assertEqual(result.score, 93)
        # BP overdue causes less drop than LEGAL overdue
        self.assertGreater(result.score, 87)

    def test_case4_all_due_soon_mid_range(self):
        """Case 4: All items due soon → mid-range score (50%)"""
        self._create_items(
            legal_statuses=['DUE_SOON'] * 5,
            bp_statuses=['DUE_SOON'] * 5,
        )
        result = PeaceOfMindScore.recalculate()
        # All at 50% factor → score = 50
        self.assertEqual(result.score, 50)

    def test_legal_weight_double(self):
        """LEGAL items have weight 2, BEST_PRACTICE weight 1"""
        item_legal = ComplianceItem.objects.create(
            title='Legal Test', category=self.cat_fire, item_type='LEGAL', status='COMPLIANT',
        )
        item_bp = ComplianceItem.objects.create(
            title='BP Test', category=self.cat_first_aid, item_type='BEST_PRACTICE', status='COMPLIANT',
        )
        self.assertEqual(item_legal.weight, 2)
        self.assertEqual(item_bp.weight, 1)

    def test_status_factors(self):
        """Status factors: COMPLIANT=1.0, DUE_SOON=0.5, OVERDUE=0.0"""
        item = ComplianceItem.objects.create(
            title='Test', category=self.cat_fire, item_type='LEGAL', status='COMPLIANT',
        )
        self.assertEqual(item.status_factor, 1.0)
        item.status = 'DUE_SOON'
        self.assertEqual(item.status_factor, 0.5)
        item.status = 'OVERDUE'
        self.assertEqual(item.status_factor, 0.0)

    def test_audit_log_created_on_recalculate(self):
        """Every recalculation creates an audit log entry"""
        self._create_items(['COMPLIANT'], ['COMPLIANT'])
        initial_count = ScoreAuditLog.objects.count()
        PeaceOfMindScore.recalculate()
        self.assertGreater(ScoreAuditLog.objects.count(), initial_count)

    def test_score_change_tracking(self):
        """Score tracks previous_score for change messaging"""
        self._create_items(['COMPLIANT'] * 3, ['COMPLIANT'] * 3)
        result1 = PeaceOfMindScore.recalculate()
        self.assertEqual(result1.score, 100)

        # Make one item overdue
        item = ComplianceItem.objects.filter(item_type='LEGAL').first()
        item.status = 'OVERDUE'
        item.save()  # Signal triggers recalculation

        result2 = PeaceOfMindScore.objects.get(pk=1)
        self.assertLess(result2.score, 100)
        self.assertEqual(result2.previous_score, 100)
        self.assertLess(result2.score_change, 0)

    def test_interpretation_messages(self):
        """Dynamic interpretation text based on score"""
        self._create_items(['COMPLIANT'] * 5, ['COMPLIANT'] * 5)
        result = PeaceOfMindScore.recalculate()
        self.assertEqual(result.interpretation, "Your compliance is in strong shape.")

        # Make items overdue to drop score
        ComplianceItem.objects.filter(item_type='LEGAL').update(status='OVERDUE')
        result = PeaceOfMindScore.recalculate()
        # Score: 5×0 + 5×1 = 5/15 = 33%
        self.assertEqual(result.interpretation, "There are overdue compliance items.")

    def test_colour_coding(self):
        """Colour: green ≥80, amber ≥60, red <60"""
        self._create_items(['COMPLIANT'] * 5, ['COMPLIANT'] * 5)
        result = PeaceOfMindScore.recalculate()
        self.assertEqual(result.colour, 'green')

        # Drop to amber range
        ComplianceItem.objects.filter(item_type='LEGAL').update(status='DUE_SOON')
        result = PeaceOfMindScore.recalculate()
        # Score: 5×1 + 5×1 = 10/15 = 67%
        self.assertEqual(result.colour, 'amber')

    def test_empty_items_score_100(self):
        """No items → score defaults to 100 (nothing to worry about)"""
        result = PeaceOfMindScore.recalculate()
        self.assertEqual(result.score, 100)

    def test_category_scores_updated(self):
        """ComplianceCategory scores update when items recalculate"""
        self._create_items(['COMPLIANT', 'OVERDUE'], ['COMPLIANT'])
        PeaceOfMindScore.recalculate()
        self.cat_fire.refresh_from_db()
        # Fire Safety has 2 LEGAL items: 1 compliant (2), 1 overdue (0) = 2/4 = 50% of max_score 10 = 5
        self.assertEqual(self.cat_fire.current_score, 5)
