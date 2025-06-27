from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.db.models import F
from Fit4.models import InitiativeImpact, Initiative  # Adjust to your actual model names

class InitiativeImpactQueryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup minimal data for the test
        initiative = Initiative.objects.create(
            Workstream='Digital',
            overall_status='On Track'
        )
        impact = InitiativeImpact.objects.create(
            initiative=initiative,
            YYear=2024,
            benefittype='OPEX'
        )
        # Add M2M fields if applicable
        # initiative.enabledby.set([...])
        # initiative.Plan_Relevance.set([...])

    def test_query_with_annotations(self):
        oYear = 2024
        bType = 'OPEX'
        filter_params = {}

        query1 = InitiativeImpact.objects.filter(
            **filter_params,
            YYear=oYear,
            benefittype=bType
        ).select_related(
            'initiative'
        ).prefetch_related(
            'initiative__Plan_Relevance',
            'initiative__enabledby'
        ).annotate(
            Workstream=F('initiative__Workstream'),
            overall_status=F('initiative__overall_status'),
            Plan_Relevance=F('initiative__Plan_Relevance'),
            enabledby=F('initiative__enabledby'),
            functions=F('initiative__functions')
        )

        self.assertTrue(query1.exists(), "Query returned no results.")
        item = query1.first()
        self.assertEqual(item.Workstream, 'Digital')
        self.assertEqual(item.overall_status, 'On Track')