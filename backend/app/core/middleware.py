from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import json

class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """
    Wraps all successful API responses in a standard envelope.
    Format: { "status": "success", "message": "...", "data": <original_response> }
    This ensures a consistent API contract for frontend consumption.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # We only wrap successful JSON responses
        if response.status_code < 400 and response.headers.get("content-type") == "application/json":
            body = [section async for section in response.body_iterator]
            response_body = b"".join(body)
            
            try:
                data = json.loads(response_body)
                # If it's already enveloped (e.g. from an exception handler), skip
                if isinstance(data, dict) and "status" in data and "data" in data:
                    enveloped_data = data
                else:
                    enveloped_data = {
                        "status": "success",
                        "message": "Request processed successfully.",
                        "data": data
                    }
                
                content = json.dumps(enveloped_data).encode("utf-8")
                
                # Create a new response with the wrapped content
                return Response(
                    content=content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )
            except json.JSONDecodeError:
                # If it wasn't valid JSON, just return the original response
                return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers))
                
        return response
