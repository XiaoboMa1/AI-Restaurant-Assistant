"""
User-aware tool wrapper - automatically injects username and stored preferences into tool calls.
"""
from typing import List, Optional
from langchain_core.tools import tool
from .booking_tools import (
    check_availability_tool,
    create_booking_tool, 
    get_booking_tool,
    update_booking_tool,
    cancel_booking_tool,
    get_user_bookings_tool,
    user_get_bookings_validated_tool,  # Import the validated version
    update_user_profile_tool,
    smart_availability_search_tool # Add the new tool
)
from ..storage.manager import storage
import json


def create_user_aware_tools(username: str) -> List:
    """Creates a list of user-aware tools for the specified user, automatically filling in stored user preferences."""
    
    def _get_user_profile():
        """Get user profile information."""
        user_data = storage.get_user(username)
        if not user_data:
            return {}
        return user_data.get("profile", {})
    
    @tool
    def user_create_booking_tool(
        visit_date: str, visit_time: str, party_size: int,
        # Customer basic info - uses stored info if not provided
        first_name: Optional[str] = None, 
        surname: Optional[str] = None, 
        title: Optional[str] = None,
        email: Optional[str] = None, 
        mobile: Optional[str] = None,
        phone: Optional[str] = None,
        mobile_country_code: Optional[str] = None,
        phone_country_code: Optional[str] = None,
        # Booking details
        special_requests: Optional[str] = None,
        is_leave_time_confirmed: Optional[bool] = None,
        room_number: Optional[str] = None,
        # Marketing preferences - uses stored preferences if not provided
        receive_email_marketing: Optional[bool] = None,
        receive_sms_marketing: Optional[bool] = None,
        group_email_marketing_opt_in_text: Optional[str] = None,
        group_sms_marketing_opt_in_text: Optional[str] = None,
        receive_restaurant_email_marketing: Optional[bool] = None,
        receive_restaurant_sms_marketing: Optional[bool] = None,
        restaurant_email_marketing_opt_in_text: Optional[str] = None,
        restaurant_sms_marketing_opt_in_text: Optional[str] = None
    ) -> str:
        """
        Creates a new restaurant booking and saves it to the local database.
        Automatically fills in the user's stored personal information and marketing preferences to reduce repetitive questions.
        
        Args:
            visit_date: Dining date, format YYYY-MM-DD
            visit_time: Dining time, format HH:MM:SS
            party_size: Number of diners
            
            # Customer Information (will autofill from stored info)
            first_name: Customer's first name
            surname: Customer's surname
            title: Title (Mr/Mrs/Ms/Dr etc.)
            email: Customer's email
            mobile: Customer's mobile number
            phone: Customer's landline number
            mobile_country_code: Mobile country code
            phone_country_code: Landline country code
            
            # Booking Details
            special_requests: Special requirements
            is_leave_time_confirmed: Leave time confirmation
            room_number: Room/table number preference
            
            # Marketing Preferences (will autofill from stored preferences)
            receive_email_marketing: Whether to receive email marketing
            receive_sms_marketing: Whether to receive SMS marketing
            group_email_marketing_opt_in_text: Group email marketing opt-in text
            group_sms_marketing_opt_in_text: Group SMS marketing opt-in text
            receive_restaurant_email_marketing: Whether to receive restaurant email marketing
            receive_restaurant_sms_marketing: Whether to receive restaurant SMS marketing
            restaurant_email_marketing_opt_in_text: Restaurant email marketing opt-in text
            restaurant_sms_marketing_opt_in_text: Restaurant SMS marketing opt-in text
        
        Returns:
            JSON formatted booking result.
        """
        # Get user's stored personal information and preferences
        user_profile = _get_user_profile()
        
        # Autofill customer basic info (if not provided and stored info exists)
        if first_name is None and user_profile.get('FirstName'):
            first_name = user_profile['FirstName']
        if surname is None and user_profile.get('Surname'):
            surname = user_profile['Surname']
        if title is None and user_profile.get('Title'):
            title = user_profile['Title']
        if email is None and user_profile.get('Email'):
            email = user_profile['Email']
        if mobile is None and user_profile.get('Mobile'):
            mobile = user_profile['Mobile']
        if phone is None and user_profile.get('Phone'):
            phone = user_profile['Phone']
        if mobile_country_code is None and user_profile.get('MobileCountryCode'):
            mobile_country_code = user_profile['MobileCountryCode']
        if phone_country_code is None and user_profile.get('PhoneCountryCode'):
            phone_country_code = user_profile['PhoneCountryCode']
            
        # Autofill marketing preferences (if not provided and stored preferences exist)
        if receive_email_marketing is None and user_profile.get('ReceiveEmailMarketing') is not None:
            receive_email_marketing = user_profile['ReceiveEmailMarketing']
        if receive_sms_marketing is None and user_profile.get('ReceiveSMSMarketing') is not None:
            receive_sms_marketing = user_profile['ReceiveSMSMarketing']
        if group_email_marketing_opt_in_text is None and user_profile.get('GroupEmailMarketingOptInText'):
            group_email_marketing_opt_in_text = user_profile['GroupEmailMarketingOptInText']
        if group_sms_marketing_opt_in_text is None and user_profile.get('GroupSmsMarketingOptInText'):
            group_sms_marketing_opt_in_text = user_profile['GroupSmsMarketingOptInText']
        if receive_restaurant_email_marketing is None and user_profile.get('ReceiveRestaurantEmailMarketing') is not None:
            receive_restaurant_email_marketing = user_profile['ReceiveRestaurantEmailMarketing']
        if receive_restaurant_sms_marketing is None and user_profile.get('ReceiveRestaurantSMSMarketing') is not None:
            receive_restaurant_sms_marketing = user_profile['ReceiveRestaurantSMSMarketing']
        if restaurant_email_marketing_opt_in_text is None and user_profile.get('RestaurantEmailMarketingOptInText'):
            restaurant_email_marketing_opt_in_text = user_profile['RestaurantEmailMarketingOptInText']
        if restaurant_sms_marketing_opt_in_text is None and user_profile.get('RestaurantSmsMarketingOptInText'):
            restaurant_sms_marketing_opt_in_text = user_profile['RestaurantSmsMarketingOptInText']
        
        # Call the full booking tool with all parameters
        return create_booking_tool.invoke({
            "visit_date": visit_date,
            "visit_time": visit_time,
            "party_size": party_size,
            "first_name": first_name,
            "surname": surname,
            "title": title,
            "email": email,
            "mobile": mobile,
            "phone": phone,
            "mobile_country_code": mobile_country_code,
            "phone_country_code": phone_country_code,
            "special_requests": special_requests,
            "is_leave_time_confirmed": is_leave_time_confirmed,
            "room_number": room_number,
            "receive_email_marketing": receive_email_marketing,
            "receive_sms_marketing": receive_sms_marketing,
            "group_email_marketing_opt_in_text": group_email_marketing_opt_in_text,
            "group_sms_marketing_opt_in_text": group_sms_marketing_opt_in_text,
            "receive_restaurant_email_marketing": receive_restaurant_email_marketing,
            "receive_restaurant_sms_marketing": receive_restaurant_sms_marketing,
            "restaurant_email_marketing_opt_in_text": restaurant_email_marketing_opt_in_text,
            "restaurant_sms_marketing_opt_in_text": restaurant_sms_marketing_opt_in_text,
            "username": username  # Automatically inject username
        })
    
    @tool
    def user_update_booking_tool(
        booking_reference: str, 
        visit_date: Optional[str] = None, 
        visit_time: Optional[str] = None, 
        party_size: Optional[int] = None,
        special_requests: Optional[str] = None,
        is_leave_time_confirmed: Optional[bool] = None,
        # Add support for updating customer info
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        title: Optional[str] = None,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        phone: Optional[str] = None,
        mobile_country_code: Optional[str] = None,
        phone_country_code: Optional[str] = None,
        # Add support for updating marketing preferences
        receive_email_marketing: Optional[bool] = None,
        receive_sms_marketing: Optional[bool] = None,
        group_email_marketing_opt_in_text: Optional[str] = None,
        group_sms_marketing_opt_in_text: Optional[str] = None,
        receive_restaurant_email_marketing: Optional[bool] = None,
        receive_restaurant_sms_marketing: Optional[bool] = None,
        restaurant_email_marketing_opt_in_text: Optional[str] = None,
        restaurant_sms_marketing_opt_in_text: Optional[str] = None
    ) -> str:
        """
        Updates booking information, supporting a full range of parameter updates.
        
        Args:
            booking_reference: Booking reference number
            visit_date: New dining date, format YYYY-MM-DD (optional)
            visit_time: New dining time, format HH:MM:SS (optional)
            party_size: New number of diners (optional)
            special_requests: New special requests (optional)
            is_leave_time_confirmed: Leave time confirmation (optional)
            
            # Customer Information Updates (all optional)
            first_name: New customer first name
            surname: New customer surname
            title: New title
            email: New email
            mobile: New mobile number
            phone: New landline number
            mobile_country_code: New mobile country code
            phone_country_code: New landline country code
            
            # Marketing Preference Updates (all optional)
            receive_email_marketing: Whether to receive email marketing
            receive_sms_marketing: Whether to receive SMS marketing
            (other marketing preference parameters...)
        
        Returns:
            JSON formatted update result.
        """
        return update_booking_tool.invoke({
            "booking_reference": booking_reference,
            "visit_date": visit_date,
            "visit_time": visit_time,
            "party_size": party_size,
            "special_requests": special_requests,
            "is_leave_time_confirmed": is_leave_time_confirmed,
            "first_name": first_name,
            "surname": surname,
            "title": title,
            "email": email,
            "mobile": mobile,
            "phone": phone,
            "mobile_country_code": mobile_country_code,
            "phone_country_code": phone_country_code,
            "receive_email_marketing": receive_email_marketing,
            "receive_sms_marketing": receive_sms_marketing,
            "group_email_marketing_opt_in_text": group_email_marketing_opt_in_text,
            "group_sms_marketing_opt_in_text": group_sms_marketing_opt_in_text,
            "receive_restaurant_email_marketing": receive_restaurant_email_marketing,
            "receive_restaurant_sms_marketing": receive_restaurant_sms_marketing,
            "restaurant_email_marketing_opt_in_text": restaurant_email_marketing_opt_in_text,
            "restaurant_sms_marketing_opt_in_text": restaurant_sms_marketing_opt_in_text
        })
    
    @tool
    def user_cancel_booking_tool(booking_reference: str, cancellation_reason: int = 1) -> str:
        """
        Cancels a restaurant booking - requires collecting a cancellation reason to provide better service.

        Mandatory validation:
        - Before cancellation, fetch all bookings of the current user and verify the provided booking_reference exists.
        - If not found, proactively refuse the cancellation.

        Workflow:
        1. Validate the booking reference belongs to the current user (via user_get_bookings_validated_tool).
        2. Collect/receive cancellation reason (1-5).
        3. If valid, call cancel_booking_tool to execute the cancellation.

        Returns:
            JSON formatted result.
        """
        # Step 1: Validate booking_reference belongs to current user
        try:
            bookings_resp = user_get_bookings_validated_tool.invoke({"username": username})
            bookings_data = json.loads(bookings_resp) if isinstance(bookings_resp, str) else bookings_resp
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"无法验证用户预订列表: {str(e)}",
                "code": "USER_BOOKINGS_VALIDATION_ERROR"
            }, ensure_ascii=False)

        if not bookings_data or not bookings_data.get("success"):
            return json.dumps({
                "success": False,
                "error": bookings_data.get("error", "failed to fetch user bookings") if isinstance(bookings_data, dict) else "failed to fetch user bookings",
                "code": "USER_BOOKINGS_FETCH_FAILED"
            }, ensure_ascii=False)

        user_refs = {b.get("booking_reference") for b in bookings_data.get("bookings", []) if b and b.get("booking_reference")}
        if booking_reference not in user_refs:
            return json.dumps({
                "success": False,
                "error": f"reference number {booking_reference} does not exist or does not belong to the current user, request cancelled.",
                "valid_references": sorted(list(user_refs)),
                "code": "BOOKING_NOT_FOUND_FOR_USER"
            }, ensure_ascii=False)

        # Step 2: Proceed to cancel
        return cancel_booking_tool.invoke({
            "booking_reference": booking_reference,
            "cancellation_reason": cancellation_reason
        })
    
    @tool
    def user_get_bookings_tool() -> str:
        """
        Gets all booking records for the current user.
        
        Returns:
            JSON formatted list of user bookings.
        """
        return user_get_bookings_validated_tool.invoke({
            "username": username
        })
    
    @tool 
    def user_update_profile_tool(
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        title: Optional[str] = None,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        phone: Optional[str] = None,
        mobile_country_code: Optional[str] = None,
        phone_country_code: Optional[str] = None,
        receive_email_marketing: Optional[bool] = None,
        receive_sms_marketing: Optional[bool] = None,
        receive_restaurant_email_marketing: Optional[bool] = None,
        receive_restaurant_sms_marketing: Optional[bool] = None
    ) -> str:
        """
        Updates user's personal profile and preference settings.
        
        Args:
            first_name: First name
            surname: Surname  
            title: Title
            email: Email
            mobile: Mobile number
            phone: Landline number
            mobile_country_code: Mobile country code
            phone_country_code: Landline country code
            receive_email_marketing: Whether to receive email marketing
            receive_sms_marketing: Whether to receive SMS marketing
            receive_restaurant_email_marketing: Whether to receive restaurant email marketing
            receive_restaurant_sms_marketing: Whether to receive restaurant SMS marketing
        
        Returns:
            Update result.
        """
        return update_user_profile_tool.invoke({
            "username": username,
            "first_name": first_name,
            "surname": surname,
            "title": title,
            "email": email,
            "mobile": mobile,
            "phone": phone,
            "mobile_country_code": mobile_country_code,
            "phone_country_code": phone_country_code,
            "receive_email_marketing": receive_email_marketing,
            "receive_sms_marketing": receive_sms_marketing,
            "receive_restaurant_email_marketing": receive_restaurant_email_marketing,
            "receive_restaurant_sms_marketing": receive_restaurant_sms_marketing
        })
    
    # Return all tools, including the enhanced user-aware versions
    return [
        # Booking management tools (user-aware)
        user_create_booking_tool,
        user_update_booking_tool, 
        user_cancel_booking_tool,
        user_get_bookings_tool,
        
        # Basic tools (do not require user info)
        check_availability_tool,        # Check availability (no user info needed)
        smart_availability_search_tool,  # Smart availability search (new)
        get_booking_tool,               # Get booking by reference
        update_user_profile_tool        # Update user profile
    ]