"""
Seed the Document Vault with UK legal document requirements for small businesses.
Creates placeholder documents that the business owner needs to upload.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from documents.models import Document, DocumentTag


# UK legal documents every small business should have
UK_REQUIRED_DOCUMENTS = [
    # ── Legal Requirements ──
    {
        'title': 'Employers\' Liability Insurance Certificate',
        'category': 'INSURANCE',
        'description': 'Mandatory if you employ anyone. Must be displayed or easily accessible. Minimum £5m cover.',
        'regulatory_ref': 'Employers\' Liability (Compulsory Insurance) Act 1969',
        'access_level': 'staff',
    },
    {
        'title': 'Public Liability Insurance',
        'category': 'INSURANCE',
        'description': 'Covers claims from members of the public for injury or property damage on your premises.',
        'regulatory_ref': '',
        'access_level': 'manager',
    },
    {
        'title': 'Professional Indemnity Insurance',
        'category': 'INSURANCE',
        'description': 'Covers claims of negligence or inadequate service/advice.',
        'regulatory_ref': '',
        'access_level': 'manager',
    },
    {
        'title': 'Health & Safety Policy',
        'category': 'POLICY',
        'description': 'Written H&S policy required if you employ 5 or more people. Should cover general policy, organisation, and arrangements.',
        'regulatory_ref': 'Health and Safety at Work etc. Act 1974, Section 2(3)',
        'access_level': 'staff',
    },
    {
        'title': 'Fire Risk Assessment',
        'category': 'HEALTH_SAFETY',
        'description': 'Must be carried out and kept up to date. Required for all business premises.',
        'regulatory_ref': 'Regulatory Reform (Fire Safety) Order 2005',
        'access_level': 'staff',
    },
    {
        'title': 'General Risk Assessment',
        'category': 'HEALTH_SAFETY',
        'description': 'Assess risks to employees and others. Must be recorded if you employ 5 or more people.',
        'regulatory_ref': 'Management of Health and Safety at Work Regulations 1999',
        'access_level': 'staff',
    },
    {
        'title': 'COSHH Assessment',
        'category': 'HEALTH_SAFETY',
        'description': 'Control of Substances Hazardous to Health. Required if you use chemicals, dyes, or cleaning products.',
        'regulatory_ref': 'Control of Substances Hazardous to Health Regulations 2002',
        'access_level': 'staff',
    },
    {
        'title': 'Data Protection / Privacy Policy',
        'category': 'LEGAL',
        'description': 'GDPR-compliant privacy policy covering how you collect, store, and process personal data.',
        'regulatory_ref': 'UK GDPR / Data Protection Act 2018',
        'access_level': 'staff',
    },
    {
        'title': 'ICO Registration Certificate',
        'category': 'LEGAL',
        'description': 'Registration with the Information Commissioner\'s Office if you process personal data.',
        'regulatory_ref': 'Data Protection Act 2018',
        'access_level': 'manager',
    },
    {
        'title': 'Terms & Conditions',
        'category': 'LEGAL',
        'description': 'Business terms and conditions for clients/customers.',
        'regulatory_ref': 'Consumer Rights Act 2015',
        'access_level': 'staff',
    },
    {
        'title': 'Complaints Procedure',
        'category': 'POLICY',
        'description': 'Written procedure for handling client complaints.',
        'regulatory_ref': '',
        'access_level': 'staff',
    },
    # ── HR / Employment ──
    {
        'title': 'Staff Handbook / Employee Handbook',
        'category': 'HR',
        'description': 'Covers employment policies, procedures, code of conduct, disciplinary process, etc.',
        'regulatory_ref': 'Employment Rights Act 1996',
        'access_level': 'staff',
    },
    {
        'title': 'Equal Opportunities Policy',
        'category': 'POLICY',
        'description': 'Policy on equality, diversity, and inclusion in the workplace.',
        'regulatory_ref': 'Equality Act 2010',
        'access_level': 'staff',
    },
    {
        'title': 'Disciplinary & Grievance Procedure',
        'category': 'HR',
        'description': 'Written procedure for handling disciplinary matters and employee grievances.',
        'regulatory_ref': 'ACAS Code of Practice',
        'access_level': 'manager',
    },
    {
        'title': 'Template Employment Contract',
        'category': 'CONTRACT',
        'description': 'Written statement of employment particulars. Must be provided to employees on or before their first day.',
        'regulatory_ref': 'Employment Rights Act 1996, Section 1',
        'access_level': 'manager',
    },
    # ── Compliance ──
    {
        'title': 'Accident Book / RIDDOR Log',
        'category': 'COMPLIANCE',
        'description': 'Record of workplace accidents and incidents. RIDDOR-reportable incidents must be logged.',
        'regulatory_ref': 'RIDDOR 2013 / Social Security (Claims and Payments) Regulations 1979',
        'access_level': 'staff',
    },
    {
        'title': 'First Aid Policy & Needs Assessment',
        'category': 'HEALTH_SAFETY',
        'description': 'Assessment of first aid needs and policy on first aid provision.',
        'regulatory_ref': 'Health and Safety (First-Aid) Regulations 1981',
        'access_level': 'staff',
    },
    {
        'title': 'PAT Testing Certificate',
        'category': 'COMPLIANCE',
        'description': 'Portable Appliance Testing records for electrical equipment.',
        'regulatory_ref': 'Electricity at Work Regulations 1989',
        'access_level': 'manager',
    },
    {
        'title': 'Gas Safety Certificate',
        'category': 'COMPLIANCE',
        'description': 'Annual gas safety check certificate (if applicable).',
        'regulatory_ref': 'Gas Safety (Installation and Use) Regulations 1998',
        'access_level': 'manager',
    },
    {
        'title': 'Electrical Installation Condition Report (EICR)',
        'category': 'COMPLIANCE',
        'description': 'Periodic inspection of fixed electrical installations. Recommended every 5 years.',
        'regulatory_ref': 'Electricity at Work Regulations 1989 / BS 7671',
        'access_level': 'manager',
    },
    {
        'title': 'Business Rates Bill / Exemption Letter',
        'category': 'LEGAL',
        'description': 'Current business rates bill or small business rate relief confirmation.',
        'regulatory_ref': 'Local Government Finance Act 1988',
        'access_level': 'owner',
    },
    {
        'title': 'Premises Lease / Tenancy Agreement',
        'category': 'CONTRACT',
        'description': 'Current lease or tenancy agreement for business premises.',
        'regulatory_ref': '',
        'access_level': 'owner',
    },
    {
        'title': 'Business Insurance Schedule',
        'category': 'INSURANCE',
        'description': 'Full schedule of all business insurance policies (contents, buildings, business interruption).',
        'regulatory_ref': '',
        'access_level': 'owner',
    },
]

TAGS = [
    {'name': 'Legal', 'colour': '#ef4444'},
    {'name': 'Insurance', 'colour': '#f59e0b'},
    {'name': 'H&S', 'colour': '#22c55e'},
    {'name': 'HR', 'colour': '#6366f1'},
    {'name': 'Compliance', 'colour': '#3b82f6'},
    {'name': 'Policy', 'colour': '#8b5cf6'},
    {'name': 'Contract', 'colour': '#64748b'},
]


class Command(BaseCommand):
    help = 'Seed the Document Vault with UK legal document requirements for small businesses'

    def handle(self, *args, **options):
        import traceback
        try:
            # Create tags
            for tag_data in TAGS:
                DocumentTag.objects.get_or_create(
                    name=tag_data['name'],
                    defaults={'colour': tag_data['colour']}
                )
            self.stdout.write(f'  Tags: {DocumentTag.objects.count()}')

            # Create placeholder documents
            created = 0
            for doc_data in UK_REQUIRED_DOCUMENTS:
                _, was_created = Document.objects.get_or_create(
                    title=doc_data['title'],
                    defaults={
                        'category': doc_data['category'],
                        'description': doc_data['description'],
                        'regulatory_ref': doc_data.get('regulatory_ref', ''),
                        'access_level': doc_data.get('access_level', 'staff'),
                        'is_placeholder': True,
                    }
                )
                if was_created:
                    created += 1

            total = Document.objects.count()
            self.stdout.write(self.style.SUCCESS(
                f'  Document Vault: {created} new placeholders created ({total} total documents)'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  seed_document_vault FAILED: {e}'))
            traceback.print_exc()
            raise
