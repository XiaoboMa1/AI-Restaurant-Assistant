"""
Restaurant API Client - Handles communication with the external mock server.
This module acts as an Anti-Corruption Layer, strictly isolating the internal system from the external API.
"""
import requests
from typing import Dict, Any, Optional
from datetime import date, time
from ..config import config
from . import schemas
import json

class RestaurantAPIError(Exception):
    """Custom Restaurant API error to encapsulate all exceptions from the API."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")

class RestaurantAPIClient:
    """Restaurant API client, responsible for all HTTP communication and data formatting."""
    
    def __init__(self):
        self.base_url = f"{config.RESTAURANT_API_BASE_URL}/api/ConsumerApi/v1/Restaurant/{config.RESTAURANT_NAME}"
        self.headers = {
            "Authorization": f"Bearer {config.RESTAURANT_API_TOKEN}",
        }
    
    def _flatten_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Core Implementation] Flattens the customer data dictionary into 'Customer[Key]': 'Value' format
        to meet the 'application/x-www-form-urlencoded' requirement.
        """
        if not customer_data:
            return {}
        
        flat_data = {}
        for key, value in customer_data.items():
            if value is not None:
                if isinstance(value, bool):
                    flat_data[f"Customer[{key}]"] = str(value).lower()
                else:
                    flat_data[f"Customer[{key}]"] = str(value)
        return flat_data

    def _convert_date_time_to_strings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts date and time objects to string format for the external API.
        """
        converted_data = data.copy()
        
        # Convert date object
        if 'VisitDate' in converted_data and isinstance(converted_data['VisitDate'], date):
            converted_data['VisitDate'] = converted_data['VisitDate'].isoformat()
        
        # Convert time object
        if 'VisitTime' in converted_data and isinstance(converted_data['VisitTime'], time):
            converted_data['VisitTime'] = converted_data['VisitTime'].isoformat()
            
        return converted_data

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Unified HTTP request method with robust error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, data=data, timeout=10)
            response.raise_for_status()
            return response.json() if response.content else {"status": "success", "message": "Operation successful"}
        except requests.exceptions.HTTPError as e:
            try:
                error_details = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                error_details = e.response.text
            raise RestaurantAPIError(e.response.status_code, error_details) from e
        except requests.exceptions.RequestException as e:
            raise RestaurantAPIError(0, f"Network connection error: {e}") from e

    def check_availability(self, request: schemas.AvailabilityRequest) -> schemas.AvailabilityResponse:
        """Check for available time slots."""
        endpoint = "/AvailabilitySearch"
        
        # Convert Pydantic model to dictionary and handle date/time
        data = request.model_dump()
        data = self._convert_date_time_to_strings(data)
        
        response_data = self._make_request("POST", endpoint, data=data)
        return schemas.AvailabilityResponse.model_validate(response_data)

    def create_booking(self, request: schemas.BookingRequest) -> schemas.BookingResponse:
        """Create a new booking."""
        endpoint = "/BookingWithStripeToken"
        
        # Separate customer data from booking data
        booking_data = request.model_dump(exclude={'Customer'}, exclude_none=True)
        customer_data = request.Customer.model_dump(exclude_none=True) if request.Customer else {}

        # Convert date/time format
        booking_data = self._convert_date_time_to_strings(booking_data)

        # Flatten customer data
        flat_customer_data = self._flatten_customer_data(customer_data)
        final_data = {**booking_data, **flat_customer_data}
        
        response_data = self._make_request("POST", endpoint, data=final_data)
        return schemas.BookingResponse.model_validate(response_data)

    def get_booking(self, booking_reference: str) -> schemas.BookingDetailsResponse:
        """Get booking details."""
        endpoint = f"/Booking/{booking_reference}"
        response_data = self._make_request("GET", endpoint)
        return schemas.BookingDetailsResponse.model_validate(response_data)

    def update_booking(self, booking_reference: str, request: schemas.BookingUpdateRequest) -> schemas.BookingUpdateResponse:
        """Update a booking."""
        endpoint = f"/Booking/{booking_reference}"
        
        # Get data and convert date/time format
        data = request.model_dump(exclude_none=True)
        data = self._convert_date_time_to_strings(data)
            
        response_data = self._make_request("PATCH", endpoint, data=data)
        return schemas.BookingUpdateResponse.model_validate(response_data)

    def cancel_booking(self, request: schemas.CancelBookingRequest) -> schemas.CancelBookingResponse:
        """Cancel a booking."""
        endpoint = f"/Booking/{request.bookingReference}/Cancel"
        data = request.model_dump()
        response_data = self._make_request("POST", endpoint, data=data)
        return schemas.CancelBookingResponse.model_validate(response_data)

api_client = RestaurantAPIClient()