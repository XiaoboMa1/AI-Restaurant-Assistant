"""
Booking-related tool functions
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
from langchain.tools import tool
from pydantic import ValidationError

from ..api.client import api_client, RestaurantAPIError
from ..api.schemas import (
    BookingRequest, BookingUpdateRequest, CustomerInfo,
    AvailabilityRequest, CancelBookingRequest
)
from ..database.crud import crud
from ..config import config


# Cancellation reason mapping
CANCELLATION_REASONS = {
    1: "Customer Request",
    2: "Restaurant Closure", 
    3: "Weather",
    4: "Emergency",
    5: "No Show"
}

def _parse_date(date_str: str) -> date:
    """解析日期字符串为 date 对象"""
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        raise ValueError(f"无效的日期格式: {date_str}，请使用 YYYY-MM-DD 格式")

def _parse_time(time_str: str) -> time:
    """解析时间字符串为 time 对象"""
    try:
        return datetime.fromisoformat(f"2000-01-01 {time_str}").time()
    except ValueError:
        raise ValueError(f"无效的时间格式: {time_str}，请使用 HH:MM:SS 格式")


@tool
def check_availability_tool(visit_date: str, party_size: int) -> str:
    """
    Check available time slots for specified date and party size
    
    Args:
        visit_date: Dining date in YYYY-MM-DD format
        party_size: Number of diners
    
    Returns:
        JSON format available time slot information
    """
    try:
        # 转换字符串日期为 date 对象
        parsed_date = _parse_date(visit_date)
        
        request = AvailabilityRequest(
            VisitDate=parsed_date,
            PartySize=party_size,
            ChannelCode="ONLINE"
        )
        
        response = api_client.check_availability(request)
        
        # Convert to user-friendly format
        result = {
            "success": True,
            "restaurant": response.restaurant,
            "visit_date": response.visit_date,
            "party_size": response.party_size,
            "available_slots": [
                {
                    "time": slot.time,
                    "available": slot.available,
                    "max_party_size": slot.max_party_size
                }
                for slot in response.available_slots if slot.available
            ],
            "total_available": len([s for s in response.available_slots if s.available])
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except ValidationError as e:
        error_msg = f"Parameter validation failed: {e.errors()[0]['msg']}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
    
    except RestaurantAPIError as e:
        error_msg = f"API call failed: {e.detail}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
    
    except Exception as e:
        error_msg = f"Failed to check availability: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool
def create_booking_tool(
    visit_date: str, visit_time: str, party_size: int, 
    first_name: Optional[str] = None, surname: Optional[str] = None, 
    email: Optional[str] = None, mobile: Optional[str] = None, phone: Optional[str] = None,
    mobile_country_code: Optional[str] = None, phone_country_code: Optional[str] = None,
    special_requests: Optional[str] = None, 
    is_leave_time_confirmed: Optional[bool] = None,
    room_number: Optional[str] = None,
    title: Optional[str] = None,
    # Marketing preference parameters - as supported by API
    receive_email_marketing: Optional[bool] = None,
    receive_sms_marketing: Optional[bool] = None,
    # Extended marketing parameters supported by our schema
    group_email_marketing_opt_in_text: Optional[str] = None,
    group_sms_marketing_opt_in_text: Optional[str] = None,
    receive_restaurant_email_marketing: Optional[bool] = None,
    receive_restaurant_sms_marketing: Optional[bool] = None,
    restaurant_email_marketing_opt_in_text: Optional[str] = None,
    restaurant_sms_marketing_opt_in_text: Optional[str] = None,
    username: Optional[str] = None
) -> str:
    """
    Create new restaurant booking with comprehensive parameter support - ALL API-supported parameters included
    
    **IMPORTANT**: This tool supports ALL parameters that the restaurant booking API accepts.
    The Agent should intelligently ask for these details to provide the best booking experience.
    
    **Required Parameters:**
    - visit_date: Dining date in YYYY-MM-DD format
    - visit_time: Dining time in HH:MM:SS format  
    - party_size: Number of diners
    
    **Booking Details (Optional but Recommended):**
    - special_requests: Special requirements (dietary, seating preferences, celebration notes)
    - is_leave_time_confirmed: Whether departure time is confirmed
    - room_number: Specific room/table number preference
    
    **Customer Information (Optional but Valuable):**
    - title: Customer title (Mr/Mrs/Ms/Dr/Prof/Sir/Lady)
    - first_name: Customer first name
    - surname: Customer surname
    - email: Customer email address (important for confirmations)
    - mobile: Customer mobile number (important for updates)
    - phone: Customer landline number
    - mobile_country_code: Mobile country code (e.g., +44, +1)
    - phone_country_code: Phone country code (e.g., +44, +1)
    
    **Marketing Preferences (Optional but Business-Critical):**
    - receive_email_marketing: Whether to receive general email marketing
    - receive_sms_marketing: Whether to receive general SMS marketing
    - group_email_marketing_opt_in_text: Group email marketing confirmation text
    - group_sms_marketing_opt_in_text: Group SMS marketing confirmation text
    - receive_restaurant_email_marketing: Whether to receive restaurant-specific email marketing
    - receive_restaurant_sms_marketing: Whether to receive restaurant-specific SMS marketing
    - restaurant_email_marketing_opt_in_text: Restaurant email marketing confirmation text
    - restaurant_sms_marketing_opt_in_text: Restaurant SMS marketing confirmation text
    
    **System Parameter:**
    - username: Username for saving booking to local database
    
    **Agent Guidelines:**
    1. Always ask for email and mobile for important communications
    2. Suggest collecting special requests for better service
    3. Ask about marketing preferences (explain benefits like special offers)
    4. For special occasions, ask for room preferences
    5. Use progressive disclosure - don't ask everything at once
    
    Returns:
        JSON format booking result with comprehensive details
    """
    try:
        # 转换字符串日期时间为对象
        parsed_date = _parse_date(visit_date)
        parsed_time = _parse_time(visit_time)
        
        # Build complete customer information if any customer data provided
        customer = None
        if any([first_name, surname, email, mobile, phone, title,
                receive_email_marketing, receive_sms_marketing,
                group_email_marketing_opt_in_text, group_sms_marketing_opt_in_text,
                receive_restaurant_email_marketing, receive_restaurant_sms_marketing,
                restaurant_email_marketing_opt_in_text, restaurant_sms_marketing_opt_in_text]):
            
            customer = CustomerInfo(
                Title=title,
                FirstName=first_name,
                Surname=surname,
                Email=email,
                Mobile=mobile,
                Phone=phone,
                MobileCountryCode=mobile_country_code or "+44",
                PhoneCountryCode=phone_country_code or "+44",
                # Core marketing preferences (API-supported)
                ReceiveEmailMarketing=receive_email_marketing,
                ReceiveSmsMarketing=receive_sms_marketing,
                # Extended marketing preferences (schema-supported)
                GroupEmailMarketingOptInText=group_email_marketing_opt_in_text,
                GroupSmsMarketingOptInText=group_sms_marketing_opt_in_text,
                ReceiveRestaurantEmailMarketing=receive_restaurant_email_marketing,
                ReceiveRestaurantSmsMarketing=receive_restaurant_sms_marketing,
                RestaurantEmailMarketingOptInText=restaurant_email_marketing_opt_in_text,
                RestaurantSmsMarketingOptInText=restaurant_sms_marketing_opt_in_text
            )
        
        # Build comprehensive booking request with ALL supported parameters
        booking_request = BookingRequest(
            VisitDate=parsed_date,
            VisitTime=parsed_time,
            PartySize=party_size,
            ChannelCode="ONLINE",  # Default as per API spec
            Customer=customer,
            # ALL optional booking parameters
            SpecialRequests=special_requests,
            IsLeaveTimeConfirmed=is_leave_time_confirmed,
            RoomNumber=room_number
        )
        
        # Call restaurant API with complete information
        response = api_client.create_booking(booking_request)
        
        # Save to local database if username provided
        if username and response.booking_reference:
            try:
                user = crud.get_user_by_username(username)
                if user:
                    # Prepare comprehensive customer info for local storage
                    customer_info = {}
                    if customer:
                        customer_info = {
                            "title": customer.Title,
                            "first_name": customer.FirstName,
                            "surname": customer.Surname,
                            "email": customer.Email,
                            "mobile": customer.Mobile,
                            "phone": customer.Phone,
                            "mobile_country_code": customer.MobileCountryCode,
                            "phone_country_code": customer.PhoneCountryCode,
                            "receive_email_marketing": customer.ReceiveEmailMarketing,
                            "receive_sms_marketing": customer.ReceiveSmsMarketing,
                            "group_email_marketing_opt_in_text": customer.GroupEmailMarketingOptInText,
                            "group_sms_marketing_opt_in_text": customer.GroupSmsMarketingOptInText,
                            "receive_restaurant_email_marketing": customer.ReceiveRestaurantEmailMarketing,
                            "receive_restaurant_sms_marketing": customer.ReceiveRestaurantSmsMarketing,
                            "restaurant_email_marketing_opt_in_text": customer.RestaurantEmailMarketingOptInText,
                            "restaurant_sms_marketing_opt_in_text": customer.RestaurantSmsMarketingOptInText
                        }
                    
                    # Save complete booking to local database
                    crud.create_booking(
                        user_id=user.id,
                        booking_reference=response.booking_reference,
                        visit_date=visit_date,
                        visit_time=visit_time,
                        party_size=party_size,
                        status="confirmed",
                        special_requests=special_requests,
                        customer_info=customer_info
                    )
            except Exception as db_error:
                # Database error shouldn't fail the booking creation
                print(f"Warning: Failed to save booking to local database: {db_error}")
        
        # Build comprehensive success response
        result = {
            "success": True,
            "message": "Booking created successfully with complete information",
            "booking_reference": response.booking_reference,
            "restaurant": response.restaurant,
            "visit_date": response.visit_date,
            "visit_time": response.visit_time,
            "party_size": response.party_size,
            "customer_name": f"{response.customer.first_name or ''} {response.customer.surname or ''}".strip() if response.customer else "No name provided",
            "status": response.status,
            # Include booking details in response
            "booking_details": {
                "special_requests": special_requests or "None",
                "room_number": room_number or "No preference",
                "leave_time_confirmed": is_leave_time_confirmed or False,
                "customer_contact": {
                    "email": email or "Not provided",
                    "mobile": mobile or "Not provided",
                    "phone": phone or "Not provided"
                }
            },
            "api_response": {
                "booking_reference": response.booking_reference,
                "restaurant": response.restaurant,
                "visit_date": response.visit_date,
                "visit_time": response.visit_time,
                "party_size": response.party_size,
                "status": "confirmed"
            }
        }
        
        # Add marketing preferences to response if provided
        if any([receive_email_marketing, receive_sms_marketing, receive_restaurant_email_marketing, receive_restaurant_sms_marketing]):
            result["marketing_preferences"] = {
                "email_marketing": receive_email_marketing,
                "sms_marketing": receive_sms_marketing,
                "restaurant_email_marketing": receive_restaurant_email_marketing,
                "restaurant_sms_marketing": receive_restaurant_sms_marketing
            }
        
        return json.dumps(result, ensure_ascii=False)
        
    except ValidationError as e:
        error_msg = f"Parameter validation failed: {e.errors()[0]['msg']}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except RestaurantAPIError as e:
        error_msg = f"API call failed: {e.detail}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to create booking: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool
def get_booking_tool(booking_reference: str) -> str:
    """
    Get booking details by reference number
    
    Args:
        booking_reference: Booking reference number
    
    Returns:
        JSON format booking details
    """
    try:
        response = api_client.get_booking(booking_reference)
        
        result = {
            "success": True,
            "booking_reference": response.booking_reference,
            "restaurant": response.restaurant,
            "visit_date": response.visit_date,
            "visit_time": response.visit_time,
            "party_size": response.party_size,
            "customer_name": f"{response.customer.first_name or ''} {response.customer.surname or ''}".strip() if response.customer else "No name provided",
            "customer_email": response.customer.email if response.customer else "Not provided",
            "customer_mobile": response.customer.mobile if response.customer else "Not provided",
            "special_requests": response.special_requests or "None",
            "status": response.status
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except RestaurantAPIError as e:
        error_msg = f"API call failed: {e.detail}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to get booking: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool 
def update_booking_tool(
    booking_reference: str,
    visit_date: Optional[str] = None,
    visit_time: Optional[str] = None, 
    party_size: Optional[int] = None,
    special_requests: Optional[str] = None,
    is_leave_time_confirmed: Optional[bool] = None,
    # Customer information parameters - all optional for updates
    first_name: Optional[str] = None,
    surname: Optional[str] = None,
    title: Optional[str] = None,
    email: Optional[str] = None,
    mobile: Optional[str] = None,
    phone: Optional[str] = None,
    mobile_country_code: Optional[str] = None,
    phone_country_code: Optional[str] = None,
    # Marketing preferences - all optional
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
    Update existing booking with comprehensive parameter support
    
    Args:
        booking_reference: Booking reference number to update
        visit_date: New dining date in YYYY-MM-DD format (optional)
        visit_time: New dining time in HH:MM:SS format (optional)
        party_size: New party size (optional)
        special_requests: New special requests (optional)
        is_leave_time_confirmed: Time confirmation status (optional)
        
        # Customer Information Updates (all optional)
        first_name: New customer first name
        surname: New customer surname  
        title: New customer title (Mr/Mrs/Ms/Dr/Prof/Sir/Lady)
        email: New customer email address
        mobile: New customer mobile number
        phone: New customer landline number
        mobile_country_code: Mobile country code (e.g., +44, +1)
        phone_country_code: Phone country code (e.g., +44, +1)
        
        # Marketing Preferences (all optional)
        receive_email_marketing: Whether to receive email marketing
        receive_sms_marketing: Whether to receive SMS marketing
        group_email_marketing_opt_in_text: Group email marketing confirmation text
        group_sms_marketing_opt_in_text: Group SMS marketing confirmation text
        receive_restaurant_email_marketing: Whether to receive restaurant email marketing
        receive_restaurant_sms_marketing: Whether to receive restaurant SMS marketing
        restaurant_email_marketing_opt_in_text: Restaurant email marketing confirmation text
        restaurant_sms_marketing_opt_in_text: Restaurant SMS marketing confirmation text
    
    Returns:
        JSON format update result
    """
    try:
        # 转换字符串日期时间为对象（如果提供）
        parsed_date = _parse_date(visit_date) if visit_date else None
        parsed_time = _parse_time(visit_time) if visit_time else None
        
        # Build update request with basic booking information
        update_request = BookingUpdateRequest(
            VisitDate=parsed_date,
            VisitTime=parsed_time,
            PartySize=party_size,
            SpecialRequests=special_requests,
            IsLeaveTimeConfirmed=is_leave_time_confirmed
        )
        
        # Call API to update basic booking information
        response = api_client.update_booking(booking_reference, update_request)
        
        # Note: Customer information updates would typically require a separate API call
        # or extended API support. For now, we document what customer info would be updated
        customer_updates = {}
        if any([first_name, surname, title, email, mobile, phone, mobile_country_code, phone_country_code,
                receive_email_marketing, receive_sms_marketing, group_email_marketing_opt_in_text,
                group_sms_marketing_opt_in_text, receive_restaurant_email_marketing, 
                receive_restaurant_sms_marketing, restaurant_email_marketing_opt_in_text,
                restaurant_sms_marketing_opt_in_text]):
            
            # Collect customer information that would be updated
            if first_name is not None:
                customer_updates["FirstName"] = first_name
            if surname is not None:
                customer_updates["Surname"] = surname
            if title is not None:
                customer_updates["Title"] = title
            if email is not None:
                customer_updates["Email"] = email
            if mobile is not None:
                customer_updates["Mobile"] = mobile
            if phone is not None:
                customer_updates["Phone"] = phone
            if mobile_country_code is not None:
                customer_updates["MobileCountryCode"] = mobile_country_code
            if phone_country_code is not None:
                customer_updates["PhoneCountryCode"] = phone_country_code
            if receive_email_marketing is not None:
                customer_updates["ReceiveEmailMarketing"] = receive_email_marketing
            if receive_sms_marketing is not None:
                customer_updates["ReceiveSmsMarketing"] = receive_sms_marketing
            if group_email_marketing_opt_in_text is not None:
                customer_updates["GroupEmailMarketingOptInText"] = group_email_marketing_opt_in_text
            if group_sms_marketing_opt_in_text is not None:
                customer_updates["GroupSmsMarketingOptInText"] = group_sms_marketing_opt_in_text
            if receive_restaurant_email_marketing is not None:
                customer_updates["ReceiveRestaurantEmailMarketing"] = receive_restaurant_email_marketing
            if receive_restaurant_sms_marketing is not None:
                customer_updates["ReceiveRestaurantSmsMarketing"] = receive_restaurant_sms_marketing
            if restaurant_email_marketing_opt_in_text is not None:
                customer_updates["RestaurantEmailMarketingOptInText"] = restaurant_email_marketing_opt_in_text
            if restaurant_sms_marketing_opt_in_text is not None:
                customer_updates["RestaurantSmsMarketingOptInText"] = restaurant_sms_marketing_opt_in_text
        
        result = {
            "success": True,
            "message": "Booking updated successfully",
            "booking_reference": response.booking_reference,
            "restaurant": response.restaurant,
            "booking_updates": response.updates,
            "status": response.status,
            "updated_at": response.updated_at,
            "api_message": response.message
        }
        
        # Add customer updates to result if any were specified
        if customer_updates:
            result["customer_updates_requested"] = customer_updates
            result["note"] = "Customer information updates were noted but may require separate API calls depending on the booking system's capabilities"
        
        return json.dumps(result, ensure_ascii=False)
        
    except ValidationError as e:
        error_msg = f"Parameter validation failed: {e.errors()[0]['msg']}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except RestaurantAPIError as e:
        error_msg = f"API call failed: {e.detail}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to update booking: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool
def cancel_booking_tool(booking_reference: str, cancellation_reason: Optional[int] = 1) -> str:
    """
    Cancel booking
    
    Args:
        booking_reference: Booking reference number to cancel
        cancellation_reason: Cancellation reason code (1-5), default is 1 (Customer Request)
    
    Returns:
        JSON format cancellation result
    """
    try:
        # Validate cancellation reason
        if cancellation_reason not in CANCELLATION_REASONS:
            cancellation_reason = 1
        
        # Create cancel request
        cancel_request = CancelBookingRequest(
            micrositeName="TheHungryUnicorn",  # Use the restaurant name from config
            bookingReference=booking_reference,
            cancellationReasonId=cancellation_reason
        )
        
        response = api_client.cancel_booking(cancel_request)
        
        result = {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_reference": response.booking_reference,
            "restaurant": response.restaurant,
            "cancellation_reason": CANCELLATION_REASONS[cancellation_reason],
            "cancelled_at": response.cancelled_at if hasattr(response, 'cancelled_at') else "Just now"
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except RestaurantAPIError as e:
        error_msg = f"API call failed: {e.detail}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to cancel booking: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool
def user_get_bookings_validated_tool(username: str) -> str:
    """
    Get all bookings for specified user with API validation - CRITICAL FIX for data consistency
    
    This tool validates each booking against the API server to ensure accurate status reporting.
    Used by user-aware tools to prevent showing cancelled bookings as active.
    
    Args:
        username: Username to query bookings for
    
    Returns:
        JSON format list of user bookings with validated status
    """
    try:
        user = crud.get_user_by_username(username)
        if not user:
            return json.dumps({
                "success": False, 
                "error": f"User {username} not found"
            }, ensure_ascii=False)
        
        # Get bookings from local database
        local_bookings = crud.get_user_bookings(user.id)
        
        result = {
            "success": True,
            "username": username,
            "total_bookings": 0,
            "bookings": [],
            "validation_notes": []
        }
        
        validated_bookings = []
        
        for booking in local_bookings:
            try:
                # CRITICAL FIX: Validate each booking against API server
                api_response = api_client.get_booking(booking.booking_reference)
                
                # Parse customer info
                try:
                    customer_info = json.loads(booking.customer_info_json) if booking.customer_info_json else {}
                except (json.JSONDecodeError, TypeError):
                    customer_info = {}
                
                # Use API server as source of truth for status
                validated_booking = {
                    "booking_reference": booking.booking_reference,
                    "visit_date": booking.visit_date,
                    "visit_time": booking.visit_time,
                    "party_size": api_response.party_size,  # Use API data
                    "status": api_response.status,  # Use API status (CRITICAL)
                    "special_requests": api_response.special_requests or "None",
                    "customer_info": customer_info,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                    "api_validated": True  # Mark as validated
                }
                
                # Only include non-cancelled bookings
                if api_response.status != "cancelled":
                    validated_bookings.append(validated_booking)
                else:
                    result["validation_notes"].append(f"Booking {booking.booking_reference} is cancelled on API server - excluded from results")
                    
            except Exception as api_error:
                # If API validation fails, mark booking as potentially stale
                result["validation_notes"].append(f"Could not validate booking {booking.booking_reference}: {str(api_error)}")
                
                # Include local data with warning
                try:
                    customer_info = json.loads(booking.customer_info_json) if booking.customer_info_json else {}
                except (json.JSONDecodeError, TypeError):
                    customer_info = {}
                
                stale_booking = {
                    "booking_reference": booking.booking_reference,
                    "visit_date": booking.visit_date,
                    "visit_time": booking.visit_time,
                    "party_size": booking.party_size,
                    "status": f"{booking.status} (UNVALIDATED)",  # Mark as unvalidated
                    "special_requests": booking.special_requests or "None",
                    "customer_info": customer_info,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                    "api_validated": False,
                    "warning": "Could not validate with API server"
                }
                validated_bookings.append(stale_booking)
        
        result["bookings"] = validated_bookings
        result["total_bookings"] = len(validated_bookings)
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to get user bookings: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


@tool
def get_user_bookings_tool(username: str) -> str:
    """
    Get all bookings for specified user from local database (LEGACY VERSION)
    
    Note: This version queries local database only and may show stale data.
    For production use, prefer user_get_bookings_validated_tool.
    
    Args:
        username: Username to query bookings for
    
    Returns:
        JSON format list of user bookings from local database
    """
    try:
        user = crud.get_user_by_username(username)
        if not user:
            return json.dumps({
                "success": False, 
                "error": f"User {username} not found"
            }, ensure_ascii=False)
        
        bookings = crud.get_user_bookings(user.id)
        
        result = {
            "success": True,
            "username": username,
            "total_bookings": len(bookings),
            "bookings": [],
            "warning": "Data from local database only - may not reflect latest API status"
        }
        
        for booking in bookings:
            try:
                customer_info = json.loads(booking.customer_info_json) if booking.customer_info_json else {}
            except (json.JSONDecodeError, TypeError):
                customer_info = {}
            
            booking_data = {
                "booking_reference": booking.booking_reference,
                "visit_date": booking.visit_date,
                "visit_time": booking.visit_time,
                "party_size": booking.party_size,
                "status": booking.status,
                "special_requests": booking.special_requests or "None",
                "customer_info": customer_info,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            }
            result["bookings"].append(booking_data)
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Failed to get user bookings: {str(e)}"
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


# Create alias for user-aware version - REMOVED, replaced with direct call
# def user_get_bookings_tool() -> str:
#     return json.dumps({
#         "success": False,
#         "error": "This tool should be called via user-aware wrapper"
#     }, ensure_ascii=False)


@tool
def update_user_profile_tool(
    username: str,
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
    Update user profile, save customer information for future bookings
    
    Args:
        username: Username
        Other parameters: Customer information fields
    
    Returns:
        Update result
    """
    try:
        # Get current user profile
        user = crud.get_user_by_username(username)
        if not user:
            return f"User {username} not found"
        
        current_profile = {}
        try:
            current_profile = json.loads(user.profile_json) if user.profile_json else {}
        except (json.JSONDecodeError, TypeError):
            current_profile = {}
        
        # Update only provided fields
        updates = {}
        if first_name is not None:
            updates["FirstName"] = first_name
        if surname is not None:
            updates["Surname"] = surname
        if title is not None:
            updates["Title"] = title
        if email is not None:
            updates["Email"] = email
        if mobile is not None:
            updates["Mobile"] = mobile
        if phone is not None:
            updates["Phone"] = phone
        if mobile_country_code is not None:
            updates["MobileCountryCode"] = mobile_country_code
        if phone_country_code is not None:
            updates["PhoneCountryCode"] = phone_country_code
        if receive_email_marketing is not None:
            updates["ReceiveEmailMarketing"] = receive_email_marketing
        if receive_sms_marketing is not None:
            updates["ReceiveSMSMarketing"] = receive_sms_marketing
        if receive_restaurant_email_marketing is not None:
            updates["ReceiveRestaurantEmailMarketing"] = receive_restaurant_email_marketing
        if receive_restaurant_sms_marketing is not None:
            updates["ReceiveRestaurantSMSMarketing"] = receive_restaurant_sms_marketing
        
        # Merge with current profile
        current_profile.update(updates)
        
        # Save updated profile
        crud.update_user_profile(username, current_profile)
        
        return f"User profile updated successfully. Updated fields: {', '.join(updates.keys())}"
        
    except Exception as e:
        return f"Failed to update user profile: {str(e)}"

@tool
def smart_availability_search_tool(
    party_size: int, 
    start_date: str, 
    max_days_to_check: int = 20
) -> str:
    """
    智能可用性搜索工具 - 在指定日期范围内循环查找可用时间
    
    解决Agent执行链终止但用户期望继续查找的问题。
    在单个工具调用中完成多天查找，避免虚假承诺。
    
    Args:
        party_size: 用餐人数 (1-20)
        start_date: 开始搜索的日期，格式：YYYY-MM-DD
        max_days_to_check: 最大查找天数，默认20天（可配置）
    
    Returns:
        JSON格式的搜索结果，包含找到的第一个可用日期或完整搜索报告
    """
    try:
        from datetime import datetime, timedelta
        import json
        from ..config import config
        
        # 使用配置中的最大搜索天数
        max_days_to_check = min(max_days_to_check, config.MAX_AVAILABILITY_SEARCH_DAYS)
        
        # 验证参数
        if party_size <= 0 or party_size > 20:
            return json.dumps({
                "success": False,
                "error": "用餐人数必须在1-20之间"
            }, ensure_ascii=False)
        
        # 解析开始日期
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return json.dumps({
                "success": False,
                "error": f"日期格式错误：{start_date}，请使用YYYY-MM-DD格式"
            }, ensure_ascii=False)
        
        search_results = {
            "success": False,
            "search_summary": {
                "party_size": party_size,
                "start_date": start_date,
                "days_checked": 0,
                "max_days_to_check": max_days_to_check,
                "first_available_date": None,
                "total_available_slots": 0
            },
            "daily_results": [],
            "found_availability": False,
            "recommendation": None
        }
        
        # 智能循环查找
        for day_offset in range(max_days_to_check):
            current_date = start_date_obj + timedelta(days=day_offset)
            current_date_str = current_date.strftime("%Y-%m-%d")
            
            search_results["search_summary"]["days_checked"] = day_offset + 1
            
            try:
                # 直接调用API客户端，不通过工具层
                request = AvailabilityRequest(
                    VisitDate=current_date,
                    PartySize=party_size,
                    ChannelCode="ONLINE"
                )
                
                response = api_client.check_availability(request)
                
                # 过滤可用时段
                available_slots = [
                    {
                        "time": slot.time,
                        "available": slot.available,
                        "max_party_size": slot.max_party_size
                    }
                    for slot in response.available_slots if slot.available
                ]
                
                daily_result = {
                    "date": current_date_str,
                    "weekday": current_date.strftime("%A"),
                    "available_slots": available_slots,
                    "total_available": len(available_slots),
                    "checked": True,
                    "api_success": True
                }
                
                search_results["daily_results"].append(daily_result)
                
                # 检查是否找到可用时间
                if len(available_slots) > 0:
                    search_results["success"] = True
                    search_results["found_availability"] = True
                    search_results["search_summary"]["first_available_date"] = current_date_str
                    search_results["search_summary"]["total_available_slots"] = len(available_slots)
                    
                    # 生成成功推荐
                    available_times = [slot["time"] for slot in available_slots]
                    search_results["recommendation"] = {
                        "action": "book_now",
                        "message": f"找到可用时间！{current_date_str}（{current_date.strftime('%A')}）有{len(available_times)}个时间段可选",
                        "available_times": available_times,
                        "booking_suggestion": f"推荐预订{current_date_str}的{available_times[0] if available_times else '第一个可用时间'}"
                    }
                    
                    # 找到第一个可用日期后立即返回
                    break
                    
            except ValidationError as e:
                # 记录参数验证失败
                daily_result = {
                    "date": current_date_str,
                    "weekday": current_date.strftime("%A"),
                    "available_slots": [],
                    "total_available": 0,
                    "checked": True,
                    "api_success": False,
                    "error": f"参数验证失败: {e.errors()[0]['msg']}"
                }
                search_results["daily_results"].append(daily_result)
                continue
                
            except RestaurantAPIError as e:
                # 记录API调用失败
                daily_result = {
                    "date": current_date_str,
                    "weekday": current_date.strftime("%A"),
                    "available_slots": [],
                    "total_available": 0,
                    "checked": True,
                    "api_success": False,
                    "error": f"API调用失败: {e.detail}"
                }
                search_results["daily_results"].append(daily_result)
                continue
                
            except Exception as day_error:
                # 记录其他单日查询失败，但继续其他日期
                daily_result = {
                    "date": current_date_str,
                    "weekday": current_date.strftime("%A"),
                    "available_slots": [],
                    "total_available": 0,
                    "checked": True,
                    "api_success": False,
                    "error": f"查询失败: {str(day_error)}"
                }
                search_results["daily_results"].append(daily_result)
                continue
        
        # 如果循环结束仍未找到，生成明确的"未找到"反馈
        if not search_results["found_availability"]:
            search_results["recommendation"] = {
                "action": "suggest_alternatives",
                "message": f"很抱歉，在{start_date}开始的{max_days_to_check}天内没有找到{party_size}人的可用时间",
                "suggestions": [
                    f"建议减少用餐人数（当前：{party_size}人）",
                    f"建议选择更晚的日期（{max_days_to_check}天后）",
                    "建议选择其他用餐时段",
                    "建议联系餐厅了解是否有临时空位"
                ],
                "next_search_date": (start_date_obj + timedelta(days=max_days_to_check)).strftime("%Y-%m-%d")
            }
        
        return json.dumps(search_results, ensure_ascii=False)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"智能搜索失败: {str(e)}",
            "fallback_suggestion": "请尝试单日查询或联系客服"
        }
        return json.dumps(error_result, ensure_ascii=False)

# Export all tools - 更新工具列表
BOOKING_TOOLS = [
    check_availability_tool,
    smart_availability_search_tool,  # 新增智能搜索工具
    create_booking_tool,
    get_booking_tool,
    update_booking_tool,
    cancel_booking_tool,
    get_user_bookings_tool,  # Legacy version
    user_get_bookings_validated_tool,  # New validated version
    update_user_profile_tool
]