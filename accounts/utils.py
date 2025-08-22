from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

def get_user_id_by_token(token):
    """Extract user ID from JWT token"""
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return user_id
    except Exception:
        return None

def check_authentication(token):
    """Validate JWT token and return user"""
    try:
        user_id = get_user_id_by_token(token)
        if not user_id:
            raise AuthenticationFailed('Invalid token')
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationFailed('User not found')
            
        return user
    except Exception as e:
        raise AuthenticationFailed(str(e))

def token_required(allowed_user_types=None):
    """Decorator for views that require token authentication"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            try:
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return Response({'error': 'Bearer token required'}, status=status.HTTP_401_UNAUTHORIZED)
                
                token = auth_header.split(' ')[1]
                user = check_authentication(token)
                
                if allowed_user_types and user.user_type not in allowed_user_types:
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
                
                request.user = user
                return view_func(request, *args, **kwargs)
            except AuthenticationFailed as e:
                return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return wrapped_view
    return decorator
