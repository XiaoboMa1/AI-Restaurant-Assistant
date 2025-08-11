"""
Restaurant Booking AI Agent - Main Application Entry Point
Supports FastAPI interface and command line interface
"""
import os
import sys
import argparse
import secrets
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.storage.manager import storage
from src.agent.booking_agent import BookingAgent


# FastAPI application
app = FastAPI(title="Restaurant Booking AI Agent", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# API models
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    profile: Optional[Dict[str, Any]] = None


class ChangePasswordRequest(BaseModel):
    username: str
    current_password: str
    new_password: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    debug_info: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    username: str
    session_id: str


class ProfileUpdateRequest(BaseModel):
    username: str
    profile: Dict[str, Any]


class PasswordResetRequest(BaseModel):
    username: str
    email: str


class ResetPasswordRequest(BaseModel):
    username: str
    reset_code: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    username: str
    password: str


# User session storage
active_sessions = {}  # session_id -> {"username": str, "agent": BookingAgent}


def generate_session_id() -> str:
    """Generate secure session ID"""
    return secrets.token_urlsafe(32)


def get_agent_for_session(session_id: str) -> BookingAgent:
    """Get Agent for session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid session ID")
    return active_sessions[session_id]["agent"]


# Web interface routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Return main page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page file not found")


# API routes
@app.post("/register")
async def register_user(request: RegisterRequest):
    """User registration"""
    try:
        user_id = storage.create_user(request.username, request.password, request.profile)
        return {"message": "Registration successful", "user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/login", response_model=UserResponse)
async def login_user(request: LoginRequest):
    """User login"""
    try:
        # Verify username and password
        if not storage.verify_user(request.username, request.password):
            raise HTTPException(status_code=401, detail="Username or password incorrect")
        
        # Create session
        session_id = generate_session_id()
        
        # Initialize Agent
        agent = BookingAgent(request.username)
        
        # Save session
        active_sessions[session_id] = {
            "username": request.username,
            "agent": agent
        }
        
        return UserResponse(username=request.username, session_id=session_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.post("/logout")
async def logout_user(session_id: str):
    """User logout"""
    if session_id in active_sessions:
        del active_sessions[session_id]
    return {"message": "Logout successful"}


@app.post("/change-password")
async def change_password(request: ChangePasswordRequest):
    """Change user password"""
    try:
        # Verify current password
        if not storage.verify_user(request.username, request.current_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Update password
        storage.update_user_password(request.username, request.new_password)
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")


@app.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset"""
    try:
        # Get user information
        user_info = storage.get_user(request.username)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify email matches profile
        user_email = user_info.get("profile", {}).get("Email", "")
        if not user_email or user_email.lower() != request.email.lower():
            raise HTTPException(status_code=400, detail="Email does not match user profile")
        
        # Generate reset code (in real app, this would be sent via email)
        reset_code = secrets.token_urlsafe(8)
        
        # Store reset code temporarily (in real app, store in database with expiration)
        if not hasattr(app.state, 'reset_codes'):
            app.state.reset_codes = {}
        app.state.reset_codes[request.username] = reset_code
        
        return {
            "message": "Password reset code generated",
            "reset_code": reset_code,  # In real app, this would be sent via email
            "note": "In production, this code would be sent to your email"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process password reset: {str(e)}")


@app.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with code"""
    try:
        # Verify reset code
        if not hasattr(app.state, 'reset_codes'):
            raise HTTPException(status_code=400, detail="No active reset codes")
        
        stored_code = app.state.reset_codes.get(request.username)
        if not stored_code or stored_code != request.reset_code:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        
        # Update password
        storage.update_user_password(request.username, request.new_password)
        
        # Remove used reset code
        del app.state.reset_codes[request.username]
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")


@app.post("/delete-account")
async def delete_account(request: DeleteAccountRequest):
    """Delete user account"""
    try:
        # Verify password before deletion
        if not storage.verify_user(request.username, request.password):
            raise HTTPException(status_code=401, detail="Password is incorrect")
        
        # Delete user account
        success = storage.delete_user(request.username)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


@app.post("/update-profile")
async def update_profile(request: ProfileUpdateRequest):
    """Update user profile"""
    try:
        # Update user profile
        storage.update_user_profile(request.username, request.profile)
        return {"message": "Profile updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat interface - Enhanced version with API debug information"""
    try:
        agent = get_agent_for_session(request.session_id)
        response, debug_info = agent.chat_with_debug(request.message)
        
        return ChatResponse(
            response=response, 
            success=True,
            debug_info=debug_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, an error occurred while processing your request: {str(e)}", 
            success=False
        )


@app.get("/user/{username}")
async def get_user_info(username: str):
    """Get user information"""
    try:
        user_info = storage.get_user(username)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove sensitive information
        user_info.pop('id', None)
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")


@app.put("/user/{username}/profile")
async def update_user_profile(username: str, request: ProfileUpdateRequest):
    """Update user profile"""
    try:
        storage.update_user_profile(username, request.profile)
        return {"message": "Profile updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.get("/users")
async def list_users():
    """List all users"""
    try:
        users = storage.list_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")



# Command line interface
class CommandLineInterface:
    """Command line interface"""
    
    def __init__(self):
        self.current_agent: Optional[BookingAgent] = None
        self.current_username: Optional[str] = None

    def run(self):
        """Main entry point"""
        print("=== Restaurant Booking AI Agent ===")
        print("Welcome to the TheHungryUnicorn Restaurant Booking System")
        print()
        
        while True:
            try:
                if not self.current_agent:
                    self._show_main_menu()
                else:
                    self._chat_loop()
            except KeyboardInterrupt:
                print("\n\nThank you for using the Restaurant Booking AI Agent!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
    
    def _show_main_menu(self):
        """Show main menu"""
        print("\n" + "="*50)
        print("Main Menu")
        print("="*50)
        print("1. Login existing user")
        print("2. Create new user")
        print("3. Exit")
        print()
        
        choice = input("Please select an option (1-3): ").strip()
        
        if choice == "1":
            self._login_user()
        elif choice == "2":
            self._create_user()
        elif choice == "3":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice, please try again")
    
    def _login_user(self):
        """User login"""
        username = input("👤 Please enter username: ").strip()
        
        if not username:
            print("❌ Username cannot be empty")
            return
        
        password = input("🔒 Please enter password: ").strip()
        
        if not password:
            print("❌ Password cannot be empty")
            return
        
        # Verify user
        if not storage.verify_user(username, password):
            print("❌ Username or password incorrect")
            return
        
        # Try to switch user, if failed don't continue
        if self._switch_user(username):
            print(f"✅ Successfully logged in user: {username}")
        else:
            print(f"❌ User login failed, please check system configuration")
    
    def _create_user(self):
        """Create new user"""
        print("\n--- Create New User ---")
        username = input("👤 Username: ").strip()
        
        if not username:
            print("❌ Username cannot be empty")
            return
        
        password = input("🔒 Password: ").strip()
        
        if not password:
            print("❌ Password cannot be empty")
            return
        
        # Collect optional profile information
        print("\n📋 Optional Profile Information (press Enter to skip):")
        profile = {}
        
        first_name = input("First Name: ").strip()
        if first_name:
            profile["FirstName"] = first_name
            
        surname = input("Surname: ").strip()
        if surname:
            profile["Surname"] = surname
            
        email = input("Email: ").strip()
        if email:
            profile["Email"] = email
            
        mobile = input("Mobile: ").strip()
        if mobile:
            profile["Mobile"] = mobile
        
        # Create user
        try:
            user_id = storage.create_user(username, password, profile)
            print(f"✅ User created successfully! User ID: {user_id}")
            print("You can now log in with the username and password.")
            input("Press Enter to continue...")
        except ValueError as e:
            print(f"❌ Creation failed: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")
    
    def _switch_user(self, username: str):
        """Switch to specified user"""
        try:
            # Create agent instance
            agent = BookingAgent(username)
            self.current_agent = agent
            self.current_username = username
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            self.current_agent = None
            self.current_username = None
            return False
    
    def _chat_loop(self):
        """Chat loop"""
        print(f"\n💬 Chatting with {self.current_username}...")
        print("Special Commands:")
        print("  /quit    - Return to main menu")
        print("  /help    - Show help information")
        print("  /clear   - Clear chat history")
        print("  /switch <username> - Switch user")
        print("-" * 50)
        
        while True:
            try:
                user_input = input(f"\n{self.current_username}> ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input == "/quit":
                    self.current_agent = None
                    self.current_username = None
                    break
                elif user_input == "/help":
                    self._show_help()
                    continue
                elif user_input == "/clear":
                    self._clear_history()
                    continue
                elif user_input.startswith("/switch "):
                    new_username = user_input[8:].strip()
                    if new_username:
                        self._switch_user(new_username)
                    else:
                        print("❌ Please specify the username to switch to, e.g.: /switch john")
                    continue
                
                # Call Agent for processing
                print("\n🤖 Assistant: ", end="", flush=True)
                try:
                    response = self.current_agent.chat(user_input)
                    print(response)
                except Exception as e:
                    print(f"Sorry, there was a problem processing your request: {e}")
                    
            except KeyboardInterrupt:
                print("\n")
                choice = input("Are you sure you want to exit? (y/N): ").strip().lower()
                if choice == 'y':
                    break
            except Exception as e:
                print(f"❌ An error occurred during chat: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("\n" + "="*50)
        print("Restaurant Booking Assistant Help")
        print("="*50)
        print("I can help you with:")
        print("1. 🔍 Check Available Times")
        print("   - 'Check availability for tomorrow evening'")
        print("   - 'What times are available for 4 people on Friday?'")
        print()
        print("2. 📅 Create Reservations")
        print("   - 'I want to book a table for 2 people'")
        print("   - 'Book for tonight at 7pm, party of 4'")
        print()
        print("3. 👀 View Bookings")
        print("   - 'Show my bookings'")
        print("   - 'Check my reservation for tomorrow'")
        print()
        print("4. ✏️ Modify Bookings")
        print("   - 'Change my booking time'")
        print("   - 'Update party size to 6 people'")
        print()
        print("5. ❌ Cancel Bookings")
        print("   - 'Cancel my reservation'")
        print("   - 'I need to cancel my booking for Friday'")
        print()
        print("Tips:")
        print("- Be as specific as possible with dates and times")
        print("- I'll guide you through the process step by step")
        print("- You can interrupt any process and start a new request")
        print("="*50)
    
    def _clear_history(self):
        """Clear chat history"""
        if hasattr(self.current_agent, 'chat_history'):
            self.current_agent.chat_history = []
            print("✅ Chat history cleared")
        else:
            print("❌ Unable to clear history")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Restaurant Booking AI Agent')
    parser.add_argument('--mode', choices=['api', 'cli'], default='cli',
                       help='Run mode: api (web server) or cli (command line)')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--port', type=int, default=8000, help='API server port')
    
    args = parser.parse_args()
    
    if args.mode == 'api':
        print(f"Starting web server on {args.host}:{args.port}")
        print(f"Access the application at: http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        cli = CommandLineInterface()
        cli.run()


if __name__ == "__main__":
    main() 