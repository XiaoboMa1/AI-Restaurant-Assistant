"""
Intent recognition and guidance tools
"""
import json
from typing import Dict, List, Any
from langchain_core.tools import tool
from datetime import datetime, date


@tool
def identify_user_intent_tool(user_input: str) -> str:
    """
    Identify user intent and provide guidance.
    
    Args:
        user_input: The user's original input.
    
    Returns:
        JSON formatted intent recognition result and guidance.
    """
    user_input_lower = user_input.lower()
    
    # Intent recognition logic
    intent_patterns = {
        "check_availability": ["check", "available", "availability", "time", "when", "see", "any", "slot"],
        "create_booking": ["book", "reserve", "order", "want", "need", "make", "get"],
        "get_booking": ["view booking", "my booking", "booking details", "check my reservation"],
        "update_booking": ["modify", "change", "alter", "adjust", "switch"],
        "cancel_booking": ["cancel", "don't want", "remove", "delete"],
        "user_switch": ["switch user", "change user", "login", "another user"],
        "help": ["help", "how to", "what can you do", "i don't know"]
    }
    
    detected_intents = []
    for intent, keywords in intent_patterns.items():
        if any(keyword in user_input_lower for keyword in keywords):
            detected_intents.append(intent)
    
    # Default to help if no clear intent
    if not detected_intents:
        detected_intents = ["help"]
    
    # Generate guidance
    primary_intent = detected_intents[0]
    guidance = _get_intent_guidance(primary_intent, user_input)
    
    result = {
        "primary_intent": primary_intent,
        "detected_intents": detected_intents,
        "confidence": len([k for k in intent_patterns[primary_intent] if k in user_input_lower]) / len(intent_patterns[primary_intent]),
        "guidance": guidance,
        "user_input": user_input
    }
    
    return json.dumps(result, ensure_ascii=False)


def _get_intent_guidance(intent: str, user_input: str) -> Dict[str, Any]:
    """Generate guidance based on intent."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    guidance_map = {
        "check_availability": {
            "next_steps": ["Ask for dining date", "Ask for party size"],
            "required_info": ["visit_date", "party_size"],
            "example_questions": [
                "For which date would you like to check availability?",
                "How many people will be dining?"
            ]
        },
        "create_booking": {
            "next_steps": ["Confirm date and time", "Confirm party size", "Collect contact information"],
            "required_info": ["visit_date", "visit_time", "party_size", "contact_info"],
            "example_questions": [
                "Could you please confirm the date and time for your meal?",
                "How many people will be dining?",
                "I'll need your contact information to confirm the booking."
            ]
        },
        "get_booking": {
            "next_steps": ["Get booking reference or query all bookings"],
            "required_info": ["booking_reference"],
            "example_questions": [
                "Please provide your booking reference number.",
                "Alternatively, I can look up all your booking records."
            ]
        },
        "update_booking": {
            "next_steps": ["Get booking reference", "Confirm what to modify"],
            "required_info": ["booking_reference", "update_details"],
            "example_questions": [
                "Please provide the reference number of the booking you wish to modify.",
                "What details would you like to change?"
            ]
        },
        "cancel_booking": {
            "next_steps": ["Get booking reference", "Confirm cancellation reason"],
            "required_info": ["booking_reference"],
            "example_questions": [
                "Please provide the reference number of the booking to cancel.",
                "Are you sure you want to cancel this booking?"
            ]
        },
        "user_switch": {
            "next_steps": ["Guide to use the command line command"],
            "required_info": [],
            "response": "To switch users, please use the /switch <username> command in the command line."
        },
        "help": {
            "next_steps": ["Provide a feature overview"],
            "required_info": [],
            "example_questions": [
                "I can help you with: checking availability, creating bookings, viewing/modifying/cancelling bookings.",
                "What would you like to do?"
            ]
        }
    }
    
    return guidance_map.get(intent, guidance_map["help"])


@tool  
def validate_booking_info_tool(info_type: str, value: str) -> str:
    """
    Validate the format and validity of booking information.
    
    Args:
        info_type: The type of information (date, time, party_size, email, phone).
        value: The value to validate.
    
    Returns:
        JSON formatted validation result.
    """
    try:
        result = {"valid": False, "error": None, "normalized_value": value}
        
        if info_type == "date":
            try:
                parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
                if parsed_date < date.today():
                    result["error"] = "Booking date cannot be in the past."
                else:
                    result["valid"] = True
                    result["normalized_value"] = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                result["error"] = "Incorrect date format, please use YYYY-MM-DD, e.g., 2025-01-15"
        
        elif info_type == "time":
            try:
                parsed_time = datetime.strptime(value, "%H:%M").time()
                result["valid"] = True
                result["normalized_value"] = parsed_time.strftime("%H:%M:00")
            except ValueError:
                try:
                    parsed_time = datetime.strptime(value, "%H:%M:%S").time()
                    result["valid"] = True
                    result["normalized_value"] = value
                except ValueError:
                    result["error"] = "Incorrect time format, please use HH:MM, e.g., 19:30"
        
        elif info_type == "party_size":
            try:
                size = int(value)
                if size <= 0:
                    result["error"] = "Party size must be a positive number."
                elif size > 20:
                    result["error"] = "Party size cannot exceed 20. For large parties, please contact the restaurant."
                else:
                    result["valid"] = True
                    result["normalized_value"] = size
            except ValueError:
                result["error"] = "Party size must be a number."
        
        elif info_type == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, value):
                result["valid"] = True
            else:
                result["error"] = "Invalid email format. Please enter a valid email address."
        
        elif info_type == "phone":
            import re
            # Simple phone number validation
            phone_pattern = r'^[\d\-\+\(\)\s]{8,20}$'
            if re.match(phone_pattern, value):
                result["valid"] = True
                result["normalized_value"] = re.sub(r'[\-\+\(\)\s]', '', value)
            else:
                result["error"] = "Invalid phone number format."
        
        else:
            result["error"] = f"Unsupported information type: {info_type}"
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "valid": False, 
            "error": f"Validation process failed: {str(e)}",
            "normalized_value": value
        }, ensure_ascii=False)