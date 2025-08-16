"""
Shared OAuth callback response templates.

Provides reusable HTML response templates for OAuth authentication flows
to eliminate duplication between server.py and oauth_callback_server.py.
"""

from fastapi.responses import HTMLResponse
from typing import Optional


def create_error_response(error_message: str, status_code: int = 400) -> HTMLResponse:
    """
    Create a standardized error response for OAuth failures.

    Args:
        error_message: The error message to display
        status_code: HTTP status code (default 400)

    Returns:
        HTMLResponse with error page
    """
    content = f"""
        <html>
        <head><title>Authentication Error</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; text-align: center;">
            <h2 style="color: #d32f2f;">Authentication Error</h2>
            <p>{error_message}</p>
            <p>Please ensure you grant the requested permissions. You can close this window and try again.</p>
            <script>setTimeout(function() {{ window.close(); }}, 10000);</script>
        </body>
        </html>
    """
    return HTMLResponse(content=content, status_code=status_code)


def create_success_response(verified_user_id: Optional[str] = None) -> HTMLResponse:
    """
    Create a standardized success response that redirects to frontend.

    Args:
        verified_user_id: The authenticated user's email (optional)

    Returns:
        HTMLResponse that redirects to frontend oauth success page
    """
    import uuid
    import os
    
    # Generate a temporary authentication token for the frontend to exchange
    temp_token = str(uuid.uuid4())
    user_email = verified_user_id or "authenticated_user"
    
    # Store the temp token mapping (in production, use Redis or database)
    # For now, we'll use a simple file-based approach
    temp_tokens_dir = os.path.join(os.path.dirname(__file__), '..', '.temp_tokens')
    os.makedirs(temp_tokens_dir, exist_ok=True)
    
    temp_token_file = os.path.join(temp_tokens_dir, f"{temp_token}.txt")
    with open(temp_token_file, 'w') as f:
        f.write(user_email)
    
    # Set expiration for temp token (5 minutes)
    import time
    import threading
    def cleanup_token():
        time.sleep(300)  # 5 minutes
        try:
            if os.path.exists(temp_token_file):
                os.remove(temp_token_file)
        except:
            pass
    
    threading.Thread(target=cleanup_token, daemon=True).start()
    
    content = f"""<html>
<head>
    <title>Authentication Successful</title>
    <script>
        // Redirect to frontend OAuth success page with temporary token
        // instead of the OAuth code (which has already been consumed)
        window.location.href = 'http://localhost:3000/oauth-success?temp_token={temp_token}&user=' + encodeURIComponent('{user_email}');
    </script>
</head>
<body>
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px;">
        <h2>Authentication Successful!</h2>
        <p>Redirecting to your dashboard...</p>
        <p style="color: #666; font-size: 0.9em;">MCP server has authenticated with all your Google services.</p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=content)


def create_server_error_response(error_detail: str) -> HTMLResponse:
    """
    Create a standardized server error response for OAuth processing failures.

    Args:
        error_detail: The detailed error message

    Returns:
        HTMLResponse with server error page
    """
    content = f"""
        <html>
        <head><title>Authentication Processing Error</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; text-align: center;">
            <h2 style="color: #d32f2f;">Authentication Processing Error</h2>
            <p>An unexpected error occurred while processing your authentication: {error_detail}</p>
            <p>Please try again. You can close this window.</p>
            <script>setTimeout(function() {{ window.close(); }}, 10000);</script>
        </body>
        </html>
    """
    return HTMLResponse(content=content, status_code=500)