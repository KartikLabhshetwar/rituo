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
    # Create a simple redirect page that sends auth code to frontend
    content = f"""<html>
<head>
    <title>Authentication Successful</title>
    <script>
        // Redirect to frontend OAuth success page with the current URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (code) {{
            window.location.href = `http://localhost:3000/oauth-success?code=${{code}}&state=${{state || ''}}`;
        }} else {{
            // Fallback if no code
            window.location.href = 'http://localhost:3000/login?error=no_code';
        }}
    </script>
</head>
<body>
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px;">
        <h2>Redirecting...</h2>
        <p>Please wait while we complete your authentication.</p>
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