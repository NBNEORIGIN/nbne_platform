JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "NBNE Business Platform",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "NBNE Platform",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "NBNE Platform",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": None,

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": "admin/img/logo.webp",

    # Welcome text on the login screen
    "welcome_sign": "Welcome to NBNE Business Platform",

    # Copyright on the footer
    "copyright": "NBNE Business Platform 2026",

    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": "bookings.Client",

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############

    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
        # model admin to link to (Permissions checked against model)
        {"model": "bookings.Booking"},
        {"model": "bookings.Client"},
    ],

    #############
    # User Menu #
    #############

    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"model": "auth.user"}
    ],

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": False,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [
        "compliance.IncidentPhoto",
        "compliance.SignOff",
        "compliance.EquipmentInspection",
        "compliance.ComplianceItem",
        "compliance.PeaceOfMindScore",
        "compliance.ScoreAuditLog",
        "compliance.HazardFinding",
        "compliance.ComplianceCategory",
    ],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["bookings", "compliance", "core", "auth"],

    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "bookings.Booking": "fas fa-calendar-check",
        "bookings.Client": "fas fa-user-friends",
        "bookings.Service": "fas fa-spa",
        "bookings.Staff": "fas fa-user-tie",
        "bookings.Session": "fas fa-chalkboard-teacher",
        "bookings.BusinessHours": "fas fa-clock",
        "bookings.StaffSchedule": "fas fa-calendar-alt",
        "bookings.Closure": "fas fa-ban",
        "bookings.StaffLeave": "fas fa-plane",
        "bookings.IntakeProfile": "fas fa-clipboard-list",
        "bookings.IntakeWellbeingDisclaimer": "fas fa-file-medical",
        "bookings.ClassPackage": "fas fa-box",
        "bookings.ClientCredit": "fas fa-coins",
        "bookings.PaymentTransaction": "fas fa-credit-card",
        "core.SiteConfig": "fas fa-cog",
        "compliance": "fas fa-hard-hat",
        "compliance.IncidentReport": "fas fa-exclamation-triangle",
        "compliance.IncidentPhoto": "fas fa-camera",
        "compliance.SignOff": "fas fa-check-double",
        "compliance.RiskAssessment": "fas fa-clipboard-check",
        "compliance.HazardFinding": "fas fa-search",
        "compliance.Equipment": "fas fa-tools",
        "compliance.EquipmentInspection": "fas fa-wrench",
        "compliance.ComplianceCategory": "fas fa-chart-bar",
        "compliance.ComplianceItem": "fas fa-tasks",
        "compliance.PeaceOfMindScore": "fas fa-heart",
        "compliance.ScoreAuditLog": "fas fa-history",
        "compliance.RAMSDocument": "fas fa-file-alt",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-olive",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-olive",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
