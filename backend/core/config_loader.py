"""
Configuration loader for client.config.json
Loads and validates client-specific configuration
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and access client configuration from client.config.json"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from client.config.json"""
        # Look for client.config.json in parent directory of Django project
        base_dir = Path(__file__).resolve().parent.parent.parent
        config_path = base_dir / 'client.config.json'
        
        if not config_path.exists():
            # Fallback to default configuration
            self._config = self._get_default_config()
            return
        
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load client.config.json: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if client.config.json not found"""
        return {
            "client": {
                "slug": "default",
                "name": "Booking Platform",
                "description": "Default booking platform"
            },
            "branding": {
                "logo_url": "/static/logo.png",
                "primary_color": "#3B82F6",
                "secondary_color": "#10B981",
                "font_family": "Inter, sans-serif"
            },
            "booking": {
                "mode": "slots",
                "staff_enabled": True,
                "any_staff_enabled": True,
                "advance_booking_days": 30,
                "slot_duration_minutes": 15,
                "business_hours": {
                    "monday": {"open": "09:00", "close": "17:00"},
                    "tuesday": {"open": "09:00", "close": "17:00"},
                    "wednesday": {"open": "09:00", "close": "17:00"},
                    "thursday": {"open": "09:00", "close": "17:00"},
                    "friday": {"open": "09:00", "close": "18:00"},
                    "saturday": {"open": "09:00", "close": "16:00"},
                    "sunday": {"open": None, "close": None}
                }
            },
            "features": {
                "sms_enabled": False,
                "email_enabled": True,
                "portal_enabled": True,
                "waitlist_enabled": True,
                "capacity_enabled": False
            },
            "cancellation": {
                "allowed": True,
                "min_hours_notice": 24,
                "fee_percentage": 0
            },
            "database": {
                "name": "booking_db",
                "port": 5432
            },
            "server": {
                "port": 8000
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key
        Example: get('branding.primary_color')
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_client_info(self) -> Dict[str, str]:
        """Get client information"""
        return self._config.get('client', {})
    
    def get_branding(self) -> Dict[str, str]:
        """Get branding configuration"""
        return self._config.get('branding', {})
    
    def get_booking_config(self) -> Dict[str, Any]:
        """Get booking configuration"""
        return self._config.get('booking', {})
    
    def get_features(self) -> Dict[str, bool]:
        """Get feature flags"""
        return self._config.get('features', {})
    
    def get_cancellation_policy(self) -> Dict[str, Any]:
        """Get cancellation policy"""
        return self._config.get('cancellation', {})
    
    def get_business_hours(self, day: str) -> Optional[Dict[str, str]]:
        """
        Get business hours for a specific day
        Returns: {"open": "09:00", "close": "17:00"} or None if closed
        """
        hours = self._config.get('booking', {}).get('business_hours', {})
        return hours.get(day.lower())
    
    def is_open_on_day(self, day: str) -> bool:
        """Check if business is open on a specific day"""
        hours = self.get_business_hours(day)
        return hours is not None and hours.get('open') is not None
    
    def get_booking_mode(self) -> str:
        """Get booking mode: 'slots' or 'sessions'"""
        return self._config.get('booking', {}).get('mode', 'slots')
    
    def is_slots_mode(self) -> bool:
        """Check if booking mode is slots"""
        return self.get_booking_mode() == 'slots'
    
    def is_sessions_mode(self) -> bool:
        """Check if booking mode is sessions"""
        return self.get_booking_mode() == 'sessions'
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self._config.get('features', {}).get(feature, False)
    
    def reload(self):
        """Reload configuration from file"""
        self._config = None
        self._load_config()


# Singleton instance
config = ConfigLoader()


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config.get(key, default)


def get_branding() -> Dict[str, str]:
    """Get branding configuration"""
    return config.get_branding()


def get_booking_mode() -> str:
    """Get booking mode"""
    return config.get_booking_mode()


def is_slots_mode() -> bool:
    """Check if slots mode"""
    return config.is_slots_mode()


def is_sessions_mode() -> bool:
    """Check if sessions mode"""
    return config.is_sessions_mode()


def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled"""
    return config.is_feature_enabled(feature)
