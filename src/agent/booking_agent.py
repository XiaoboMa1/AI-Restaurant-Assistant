"""
Restaurant Booking AI Agent - LangChain-based conversational booking assistant
"""
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

from ..config import config
from ..tools.booking_tools import BOOKING_TOOLS
from ..tools.user_aware_tools import create_user_aware_tools
from ..storage.manager import storage

class BookingAgent:
    """Restaurant Booking AI Agent - Supports intent recognition and guided interaction"""
    
    def __init__(self, username: str):
        self.username = username
        self.user_data = storage.get_user(username)
        
        if not self.user_data:
            raise ValueError(f"User {username} does not exist")
        
        # Use a user-aware toolset that automatically fills in stored preferences
        self.tools = create_user_aware_tools(username)
        
        # Initialize LLM - Supports Gemini and OpenAI
        if "gemini" in config.OPENAI_MODEL.lower():
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=config.OPENAI_API_KEY,
                model=config.OPENAI_MODEL,
                temperature=0.1
            )
        else:
            llm_kwargs = {
                "openai_api_key": config.OPENAI_API_KEY,
                "model_name": config.OPENAI_MODEL,
                "temperature": 0.1
            }
            if config.OPENAI_BASE_URL:
                llm_kwargs["openai_api_base"] = config.OPENAI_BASE_URL
            
            self.llm = ChatOpenAI(**llm_kwargs)
        
        # Create an enhanced prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_enhanced_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create the executor - fixed configuration to support full workflow
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,  # Increase iterations to support complex flows
            return_intermediate_steps=True,  # Return intermediate steps for debugging
            handle_parsing_errors=True  # Improve error handling
            # Removed early_stopping_method="force" - this is a key fix
        )
        
        # Load chat history
        self._load_chat_history()
    
    def _get_enhanced_system_prompt(self) -> str:
        """Get the enhanced system prompt - supports intent recognition and intelligent parameter collection"""
        # Get current date and time
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        current_weekday = datetime.now().strftime("%A")
        
        user_profile = self.user_data.get("profile", {})
        
        profile_text = ""
        marketing_preferences_status = ""
        if user_profile:
            profile_text = f"\n\n【User Profile Information】\n"
            for key, value in user_profile.items():
                if value:
                    profile_text += f"- {key}: {value}\n"
            profile_text += "\n📋 When creating a booking, please prioritize using this personal information as default values, without repeatedly asking for existing information."
            
            # Analyze marketing preference status
            marketing_fields = ['ReceiveEmailMarketing', 'ReceiveSMSMarketing', 'ReceiveRestaurantEmailMarketing', 'ReceiveRestaurantSMSMarketing']
            has_marketing_prefs = any(user_profile.get(field) is not None for field in marketing_fields)
            
            if has_marketing_prefs:
                marketing_preferences_status = f"\n\n🔔 【Marketing Preferences Set】\nUser has set marketing preferences. When creating a booking, use the stored preferences directly without asking again.\nCurrent settings:\n"
                for field in marketing_fields:
                    if field in user_profile:
                        marketing_preferences_status += f"- {field}: {user_profile[field]}\n"
            else:
                marketing_preferences_status = f"\n\n🔔 【Marketing Preferences Not Set】\nUser has not yet set marketing preferences. You need to ask and save them during the first booking."
        
        return f"""You are a professional restaurant booking AI assistant, helping users manage their reservations at TheHungryUnicorn restaurant.

【IMPORTANT: Current Time Information】
- Current Date: {current_date}
- Current Time: {current_time}  
- Today is: {current_weekday}
- Please always base your understanding of the user's time requirements (e.g., "today", "tomorrow", "next week") on the current date.

【IMPORTANT: Current User Information】
- Current Username: {self.username}
- When calling tools that require a username parameter, please use: {self.username}

【Core Functions & Intent Recognition】
You need to recognize the user's intent and provide the corresponding service:

1. **Check Availability** (check_availability_tool, smart_availability_search_tool)
   - Keywords: query, check, available, time, when, is there
   - Information needed: date, number of people
   - **Tool Selection Strategy**:
     For a single day query: use check_availability_tool
     To find availability over multiple days or "find the earliest available time": use smart_availability_search_tool
   - **Strictly Prohibit False Promises**: Never say "I am searching", "continuing to look", or other unimplemented actions.
   - **Actual Execution Principle**: Every query must be completed by a tool call. The result returned by the tool is the final result.

2. **Smart Availability Search Usage Guide**:
   - When the user needs to "find the earliest available time" or "check for openings next week", use smart_availability_search_tool.
   - This tool checks multiple days in a single call, avoiding execution chain termination issues.
   - The tool will return a clear "found" or "not found" result, requiring no further processing.
   - Maximum search days: {config.MAX_AVAILABILITY_SEARCH_DAYS} days (configurable).

2. **Create Booking** (user_create_booking_tool)  
   - Keywords: book, reserve, order, want, make
   - **Mandatory Workflow**:
     1. You must first call check_availability_tool or smart_availability_search_tool to check availability.
     2. Collect all necessary booking information (including all API-supported parameters, like leave_time_confirmed).
     3. Finally, call user_create_booking_tool to create the booking.

【Intelligent Parameter Collection Strategy】

When creating a booking, you must collect the following information and include it in the tool call:

**Basic Information (Required):**
- Dining date, time, number of people

**Customer Information (Intelligently Collected):**
- title: Title (Mr/Mrs/Ms/Dr, etc.) - If unknown, politely ask "How should I address you?"
- first_name, surname: Name - Prioritize using stored information.
- email, mobile: Contact information - Prioritize using stored information. If missing, explain its importance and ask.
- phone: Landline number - Optional, ask "Would you like to leave a landline number as a backup contact?"
- mobile_country_code, phone_country_code: Country code: Automatically identify based on the user's number.

**Additional Requirements (Must be collected, ask all at once):**
- special_requests, room_number, is_leave_time_confirmed: Special requests - Proactively ask "Do you have any special requests? Such as seating preferences, dietary restrictions, or celebrations? Do you have a preference for a seating area? Is there a planned departure time?"

**Marketing Preferences (State-aware Handling):**
{marketing_preferences_status}

**Marketing Preference Collection Rules:**
1. **Prioritize Stored Preferences**: If the user's profile already has marketing preferences, use them directly without asking.
2. **Ask Only on First Time or Explicit Request**:
   - For new users or those without set preferences: Politely ask "To provide better service, would you like to receive promotional offers and dining reminders? This is completely optional and you can unsubscribe at any time."
   - When the user actively requests a change: Update the preference settings.
3. **Must Be Included in Tool Call**: Regardless of the source (stored or newly collected), all marketing preference parameters must be included in the create_booking tool call.
4. **Save New Settings**: If new preferences are collected, use update_user_profile_tool to save them.

【Progressive Collection Strategy】
1. **Do not ask for all information at once** - Collect it gradually as the conversation flows naturally.
2. **Prioritize using known information** - Autofill from the user's profile.
3. **Provide smart prompts** - Explain why certain information is needed.
4. **Confirm important information** - Confirm key details before creating the booking.


3. **Cancel Booking** (user_cancel_booking_tool)
   - Keywords: cancel, don't want, unsubscribe, not going, delete, revoke
   - **Mandatory Workflow**:
     1. Validate the booking reference belongs to the current user by calling user_get_bookings_tool first. If the reference is not found in the user's bookings, you must refuse the request and STOP. Do not ask for a cancellation reason in this case.
     2. Only after validation passes, ask for the cancellation reason (1-5). Never use a default value without asking.
     3. Call the user_cancel_booking_tool to execute the cancellation.
   - **Cancellation Reason Collection Strategy**:
     - Proactively ask: "Please tell me the reason for cancellation."
     - Provide options: "Is it for personal reasons(1), restaurant issues(2), weather(3), an emergency(4), or another reason?"
   - **Forbidden**:
     - Do not ask for a cancellation reason before validating the booking reference belongs to the current user.
     - Never claim a booking is cancelled without calling the tool.

4. **View Booking** (user_get_bookings_tool, get_booking_tool)
   - Keywords: view, my booking, booking details, check booking
   - **Mandatory Requirement**: You must call the corresponding tool to get real data.

5. **Modify Booking** (user_update_booking_tool)
   - Keywords: modify, change, alter, adjust, switch
   - **Mandatory Requirement**: You must call the tool to perform the modification, do not give an answer based on speculation.

【Mandatory Tool Call Principle】
- **Absolutely No False Promises**: Strictly forbidden to tell the user "I am querying", "I am processing", "I am looking" without calling a tool.
- **Actual Execution**: Every function must be completed by calling the corresponding tool. You cannot provide answers based on speculation.
- **Transparency Principle**: The result of a tool call is the final result. If the tool returns "not found", inform the user directly.
- **Cancellation-Specific Rule**: For cancellation intent, you MUST first call user_get_bookings_tool to validate that the provided booking reference belongs to the current user. If not, refuse immediately and do NOT ask for a cancellation reason.
- **No Loop Promises**: Do not promise to "keep searching" or "look for other times for you", as this requires additional execution chains.

【Smart Search Strategy】
- Single-day query: Use check_availability_tool directly.
- Range query: Use smart_availability_search_tool to complete a multi-day search in one go.
- Search result processing: Provide suggestions to the user based on the 'recommendation' field returned by the tool.

【Special Command Handling】
- When the user mentions "switch user", "change user", "login as another user", etc.:
  Reply: "To switch users, please use the /switch <username> command in the command line. For example: /switch john"

【Error Handling Strategy】
- **API Errors**: Explain the problem in simple language and provide suggestions for resolution.
- **Missing Parameters**: Politely ask for the missing information and explain why it's needed.
- **Validation Failures**: Point out the specific issue and guide the user to provide the correct format.

【Dialogue Style】
- Always communicate with the user in a friendly and professional English.
- Avoid technical jargon; explain things in everyday language.
- Proactively offer helpful suggestions.
- Provide confirmation and next steps for successful operations.

Current user: {self.username}{profile_text}

Based on the user's input, identify their intent and immediately execute the corresponding tool call. Remember: prioritize using stored user information, only collect missing parameters when necessary, and ensure all API-required parameters are included in the tool call."""
    
    
    def _load_chat_history(self):
        """Load chat history"""
        session_data = storage.get_session(self.username)
        self.chat_history = []
        
        for msg in session_data.get("chat_history", []):
            if msg["type"] == "human":
                self.chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                self.chat_history.append(AIMessage(content=msg["content"]))
    
    def _save_chat_history(self):
        """Save chat history"""
        # Convert to serializable format
        history_data = []
        for msg in self.chat_history:
            if isinstance(msg, HumanMessage):
                history_data.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history_data.append({"type": "ai", "content": msg.content})
        
        storage.save_session(self.username, {"chat_history": history_data})
    
    def chat(self, user_input: str) -> str:
        """Handle user input and return response (simple version)"""
        response, _ = self.chat_with_debug(user_input)
        return response
    
    def chat_with_debug(self, user_input: str) -> tuple[str, Dict[str, Any]]:
        """Handle user input and return response with debug information"""
        start_time = time.time()
        debug_info = {
            "agent_steps": [],
            "api_calls": [],
            "tool_calls": [],
            "agent_executed_steps": 0,
            "agent_reasoning": [],
            "decisions": [],
            "performance": {}
        }
        
        try:
            # Refresh user data to get latest profile information
            self.user_data = storage.get_user(self.username)
            
            # Add user message to history
            self.chat_history.append(HumanMessage(content=user_input))
            
            # Track agent reasoning process
            debug_info["agent_reasoning"].append(f"Processing user input: '{user_input}'")
            debug_info["agent_reasoning"].append(f"Current user: {self.username}")
            debug_info["agent_reasoning"].append(f"Available tools: {[tool.name for tool in self.tools]}")
            
            # Analyze user intent
            intent_analysis = self._analyze_user_intent(user_input)
            debug_info["decisions"].append({
                "decision": f"Intent identified as: {intent_analysis['intent']}",
                "reasoning": f"Based on keywords: {intent_analysis['keywords']}, confidence: {intent_analysis['confidence']}"
            })
            
            llm_start_time = time.time()
            
            # Execute agent
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history[:-1]
            })
            
            llm_end_time = time.time()
            
            response = result["output"]
            
            # Collect debug information
            if result.get("intermediate_steps"):
                debug_info["agent_executed_steps"] = len(result['intermediate_steps'])
                debug_info["agent_reasoning"].append(f"Agent executed {len(result['intermediate_steps'])} tool calls")
                
                tool_start_time = time.time()
                
                for i, step in enumerate(result["intermediate_steps"]):
                    step_info = {
                        "step": i+1,
                        "tool": step[0].tool,
                        "input": step[0].tool_input,
                        "output": step[1] if len(step) > 1 else None
                    }
                    debug_info["agent_steps"].append(step_info)
                    
                    # Add reasoning for each tool call
                    debug_info["agent_reasoning"].append(f"Step {i+1}: Calling tool '{step[0].tool}' with parameters: {step[0].tool_input}")
                    
                    # Record decision making
                    debug_info["decisions"].append({
                        "decision": f"Execute tool: {step[0].tool}",
                        "reasoning": f"Tool selected to handle user request based on identified intent and current conversation context"
                    })
                    
                    # If it's a booking API call tool, record detailed information
                    if "booking" in step[0].tool.lower() or "availability" in step[0].tool.lower():
                        api_response = step[1] if len(step) > 1 else "No response"
                        debug_info["api_calls"].append({
                            "tool": step[0].tool,
                            "parameters_sent": step[0].tool_input,
                            "response": api_response
                        })
                        debug_info["agent_reasoning"].append(f"External API call made to restaurant booking system")
                        
                    # If profile updated, regenerate system prompt
                    if step[0].tool == "update_user_profile_tool":
                        self._refresh_agent_prompt()
                        debug_info["agent_reasoning"].append("User profile updated, refreshing agent context")
                        
                tool_end_time = time.time()
                        
            else:
                debug_info["warning"] = "Agent did not execute any tool calls"
                debug_info["agent_reasoning"].append("No tools were called - agent responded directly")
                debug_info["decisions"].append({
                    "decision": "Direct response without tool execution",
                    "reasoning": "User input could be handled without external tool calls"
                })
                tool_start_time = tool_end_time = llm_end_time
            
            # Post-process response
            response = self._post_process_response(response)
            
            # Add AI response to history
            self.chat_history.append(AIMessage(content=response))
            
            # Save chat history
            self._save_chat_history()
            
            end_time = time.time()
            
            # Calculate performance metrics
            debug_info["performance"] = {
                "total_time": round((end_time - start_time) * 1000, 2),
                "llm_time": round((llm_end_time - llm_start_time) * 1000, 2),
                "tool_time": round((tool_end_time - tool_start_time) * 1000, 2),
                "tokens_used": "N/A"  # Could be enhanced with actual token counting
            }
            
            debug_info["agent_reasoning"].append(f"Response generated successfully in {debug_info['performance']['total_time']}ms")
            
            return response, debug_info
            
        except Exception as e:
            end_time = time.time()
            error_msg = f"Sorry, I encountered an error while processing your request: {str(e)}"
            
            debug_info["error"] = str(e)
            debug_info["agent_reasoning"].append(f"Error occurred: {str(e)}")
            debug_info["performance"] = {
                "total_time": round((end_time - start_time) * 1000, 2),
                "llm_time": 0,
                "tool_time": 0,
                "tokens_used": "N/A"
            }
            
            return error_msg, debug_info
    
    def _analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze user intent from input"""
        user_input_lower = user_input.lower()
        
        # Intent keywords mapping
        intent_keywords = {
            "check_availability": ["check", "available", "free", "open", "time", "when", "any", "query", "see", "availability", "slot"],
            "create_booking": ["book", "reserve", "table", "want", "need", "make", "order", "get"],
            "view_bookings": ["show", "view", "my", "bookings", "reservations", "check booking"],
            "modify_booking": ["change", "modify", "update", "edit", "move", "adjust", "switch"],
            "cancel_booking": ["cancel", "remove", "delete", "don't want", "revoke", "not going"]
        }
        
        # Calculate intent scores
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[primary_intent] / len(intent_keywords[primary_intent])
            matched_keywords = [kw for kw in intent_keywords[primary_intent] if kw in user_input_lower]
        else:
            primary_intent = "general_inquiry"
            confidence = 0.5
            matched_keywords = []
        
        return {
            "intent": primary_intent,
            "confidence": confidence,
            "keywords": matched_keywords,
            "all_scores": intent_scores
        }
    
    def _post_process_response(self, response: str) -> str:
        """Post-process agent response"""
        # Clean up any formatting issues
        response = response.strip()
        
        # Ensure proper greeting for first interaction
        if len(self.chat_history) <= 2:  # User message + AI response
            if not any(greeting in response.lower() for greeting in ["hello", "hi", "welcome", "good"]):
                response = f"Hello! {response}"
        
        return response
    
    def _refresh_agent_prompt(self):
        """Refresh agent prompt with updated user data"""
        self.user_data = storage.get_user(self.username)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_enhanced_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Recreate agent with new prompt
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            max_execution_time=60,
            return_intermediate_steps=True
        )
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = []
        storage.save_session(self.username, {"chat_history": []})
        
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return self.user_data.get("profile", {})
    
    def update_user_profile(self, profile: Dict[str, Any]):
        """Update user profile and re-initialize agent"""
        storage.update_user_profile(self.username, profile)
        self.user_data = storage.get_user(self.username)
        
        # Re-create agent to update user info in system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_enhanced_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            max_execution_time=60,
            return_intermediate_steps=True
        )
    
    def get_available_commands(self) -> List[str]:
        """Get available command list - for help function"""
        return [
            "Check availability: 'Check what time is available for tomorrow night'",
            "Create booking: 'I want to book a table for 7 PM tonight'", 
            "View bookings: 'View my bookings' or 'View booking ABC123'",
            "Modify booking: 'Modify booking ABC123 time'",
            "Cancel booking: 'Cancel booking ABC123'",
            "Switch user: Use /switch <username> command"
        ]