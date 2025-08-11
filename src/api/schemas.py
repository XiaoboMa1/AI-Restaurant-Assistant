"""
Pydantic model definitions for API requests and responses.
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, time
import re


class CustomerInfo(BaseModel):
    """Customer information model - full version supporting all marketing parameters."""
    Title: Optional[str] = Field(None, description="Title", max_length=10)
    FirstName: Optional[str] = Field(None, description="First Name", max_length=50)
    Surname: Optional[str] = Field(None, description="Surname", max_length=50)
    Email: Optional[EmailStr] = Field(None, description="Email address")
    Mobile: Optional[str] = Field(None, description="Mobile number", max_length=20)
    Phone: Optional[str] = Field(None, description="Landline phone", max_length=20)
    MobileCountryCode: Optional[str] = Field(None, description="Mobile country code", max_length=5)
    PhoneCountryCode: Optional[str] = Field(None, description="Phone country code", max_length=5)
    # Basic marketing parameters
    ReceiveEmailMarketing: Optional[bool] = Field(None, description="Receive email marketing")
    ReceiveSmsMarketing: Optional[bool] = Field(None, description="Receive SMS marketing")
    # Group marketing parameters
    GroupEmailMarketingOptInText: Optional[str] = Field(None, description="Group email marketing opt-in text", max_length=200)
    GroupSmsMarketingOptInText: Optional[str] = Field(None, description="Group SMS marketing opt-in text", max_length=200)
    # Restaurant marketing parameters
    ReceiveRestaurantEmailMarketing: Optional[bool] = Field(None, description="Receive restaurant email marketing")
    ReceiveRestaurantSmsMarketing: Optional[bool] = Field(None, description="Receive restaurant SMS marketing")
    RestaurantEmailMarketingOptInText: Optional[str] = Field(None, description="Restaurant email marketing opt-in text", max_length=200)
    RestaurantSmsMarketingOptInText: Optional[str] = Field(None, description="Restaurant SMS marketing opt-in text", max_length=200)

    @field_validator('Mobile', 'Phone')
    @classmethod
    def validate_phone_format(cls, v):
        """Validate phone number format."""
        if v is None or v == "":
            return v
        # Basic phone number format validation - allows only digits, spaces, hyphens, parentheses, plus sign
        if not re.match(r'^[\d\s\-\(\)\+]+$', v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator('Title')
    @classmethod
    def validate_title(cls, v):
        """Validate title format."""
        if v is None or v == "":
            return v
        valid_titles = ['Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Sir', 'Lady']
        if v not in valid_titles:
            raise ValueError(f"Title must be one of: {', '.join(valid_titles)}")
        return v


class AvailabilityRequest(BaseModel):
    """Availability check request model."""
    VisitDate: date = Field(..., description="Visit date")
    PartySize: int = Field(..., gt=0, le=20, description="Party size must be between 1-20")
    ChannelCode: str = Field(default="ONLINE", description="Booking channel", max_length=20)
    
    @field_validator('VisitDate')
    @classmethod
    def validate_visit_date(cls, v):
        """Validate that the visit date is not in the past."""
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError("Visit date cannot be in the past")
        return v

    @field_validator('ChannelCode')
    @classmethod
    def validate_channel_code(cls, v):
        """Validate the booking channel."""
        valid_channels = ['ONLINE', 'PHONE', 'WALK_IN', 'PARTNER']
        if v.upper() not in valid_channels:
            raise ValueError(f"Booking channel must be one of: {', '.join(valid_channels)}")
        return v.upper()


class BookingRequest(BaseModel):
    """Booking request model."""
    VisitDate: date = Field(..., description="Visit date")
    VisitTime: time = Field(..., description="Visit time")
    PartySize: int = Field(..., gt=0, le=20, description="Party size must be between 1-20")
    ChannelCode: str = Field(default="ONLINE", description="Booking channel", max_length=20)
    SpecialRequests: Optional[str] = Field(None, description="Special requests", max_length=500)
    IsLeaveTimeConfirmed: Optional[bool] = Field(None, description="Leave time confirmed")
    RoomNumber: Optional[str] = Field(None, description="Room number", max_length=10)
    Customer: Optional[CustomerInfo] = Field(None, description="Customer information")
    
    @field_validator('VisitDate')
    @classmethod
    def validate_visit_date(cls, v):
        """Validate that the visit date is not in the past."""
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError("Visit date cannot be in the past")
        return v

    @field_validator('VisitTime')
    @classmethod
    def validate_visit_time(cls, v):
        """Validate that the visit time is within business hours."""
        # Assuming business hours are 11:00-23:00
        from datetime import time as time_obj
        opening_time = time_obj(11, 0)
        closing_time = time_obj(23, 0)
        
        if not (opening_time <= v <= closing_time):
            raise ValueError("Visit time must be within business hours (11:00-23:00)")
        return v

    @field_validator('ChannelCode')
    @classmethod
    def validate_channel_code(cls, v):
        """Validate the booking channel."""
        valid_channels = ['ONLINE', 'PHONE', 'WALK_IN', 'PARTNER']
        if v.upper() not in valid_channels:
            raise ValueError(f"Booking channel must be one of: {', '.join(valid_channels)}")
        return v.upper()


class BookingUpdateRequest(BaseModel):
    """Booking update request model."""
    VisitDate: Optional[date] = Field(None, description="New visit date")
    VisitTime: Optional[time] = Field(None, description="New visit time")
    PartySize: Optional[int] = Field(None, gt=0, le=20, description="New party size")
    SpecialRequests: Optional[str] = Field(None, description="Special requests", max_length=500)
    IsLeaveTimeConfirmed: Optional[bool] = Field(None, description="Leave time confirmed")
    
    @field_validator('VisitDate')
    @classmethod
    def validate_visit_date(cls, v):
        """Validate that the visit date is not in the past."""
        if v is None:
            return v
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError("Visit date cannot be in the past")
        return v

    @field_validator('VisitTime')
    @classmethod
    def validate_visit_time(cls, v):
        """Validate that the visit time is within business hours."""
        if v is None:
            return v
        # Assuming business hours are 11:00-23:00
        from datetime import time as time_obj
        opening_time = time_obj(11, 0)
        closing_time = time_obj(23, 0)
        
        if not (opening_time <= v <= closing_time):
            raise ValueError("Visit time must be within business hours (11:00-23:00)")
        return v


class CancelBookingRequest(BaseModel):
    """Cancel booking request model."""
    micrositeName: str = Field(..., description="Microsite name", min_length=1, max_length=100)
    bookingReference: str = Field(..., description="Booking reference number", min_length=1, max_length=20)
    cancellationReasonId: int = Field(..., ge=1, le=5, description="Cancellation reason ID must be between 1-5")

    @field_validator('bookingReference')
    @classmethod
    def validate_booking_reference(cls, v):
        """Validate booking reference format."""
        if not re.match(r'^[A-Z0-9]{3,20}$', v):
            raise ValueError("Booking reference must be 3-20 uppercase letters and numbers")
        return v


class TimeSlot(BaseModel):
    """Time slot model."""
    time: str = Field(..., description="Time", pattern=r'^\d{2}:\d{2}:\d{2}$')
    available: bool = Field(..., description="Is available")
    max_party_size: int = Field(..., ge=1, description="Maximum party size")
    current_bookings: int = Field(..., ge=0, description="Current number of bookings")


class AvailabilityResponse(BaseModel):
    """Availability check response model."""
    restaurant: str = Field(..., description="Restaurant name")
    restaurant_id: int = Field(..., description="Restaurant ID")
    visit_date: str = Field(..., description="Visit date")
    party_size: int = Field(..., gt=0, description="Party size")
    channel_code: str = Field(..., description="Booking channel")
    available_slots: List[TimeSlot] = Field(..., description="List of available time slots")
    total_slots: int = Field(..., ge=0, description="Total number of time slots")


class CustomerResponse(BaseModel):
    """Customer response model."""
    id: int = Field(..., description="Customer ID")
    first_name: Optional[str] = Field(None, description="First name")
    surname: Optional[str] = Field(None, description="Surname")
    email: Optional[str] = Field(None, description="Email")


class BookingResponse(BaseModel):
    """Booking response model."""
    booking_reference: str = Field(..., description="Booking reference number")
    booking_id: int = Field(..., description="Booking ID")
    restaurant: str = Field(..., description="Restaurant name")
    visit_date: str = Field(..., description="Visit date")
    visit_time: str = Field(..., description="Visit time")
    party_size: int = Field(..., gt=0, description="Party size")
    status: str = Field(..., description="Status")
    customer: Optional[CustomerResponse] = Field(None, description="Customer information")
    created_at: str = Field(..., description="Creation time")


class BookingDetailsResponse(BaseModel):
    """Booking details response model."""
    booking_reference: str = Field(..., description="Booking reference number")
    booking_id: int = Field(..., description="Booking ID")
    restaurant: str = Field(..., description="Restaurant name")
    visit_date: str = Field(..., description="Visit date")
    visit_time: str = Field(..., description="Visit time")
    party_size: int = Field(..., gt=0, description="Party size")
    status: str = Field(..., description="Status")
    special_requests: Optional[str] = Field(None, description="Special requests")
    customer: Optional[CustomerResponse] = Field(None, description="Customer information")
    created_at: str = Field(..., description="Creation time")
    updated_at: str = Field(..., description="Update time")


class BookingUpdateResponse(BaseModel):
    """Booking update response model."""
    booking_reference: str = Field(..., description="Booking reference number")
    booking_id: int = Field(..., description="Booking ID")
    restaurant: str = Field(..., description="Restaurant name")
    updates: dict = Field(..., description="Updated content")
    status: str = Field(..., description="Status")
    updated_at: str = Field(..., description="Update time")
    message: str = Field(..., description="Message")


class CancelBookingResponse(BaseModel):
    """Cancel booking response model."""
    booking_reference: str = Field(..., description="Booking reference number")
    booking_id: int = Field(..., description="Booking ID")
    restaurant: str = Field(..., description="Restaurant name")
    cancellation_reason_id: int = Field(..., ge=1, le=5, description="Cancellation reason ID")
    cancellation_reason: str = Field(..., description="Cancellation reason")
    status: str = Field(..., description="Status")
    cancelled_at: str = Field(..., description="Cancellation time")
    message: str = Field(..., description="Message")


class APIError(BaseModel):
    """API error model."""
    detail: str = Field(..., description="Error details")