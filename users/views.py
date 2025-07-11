from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models import User

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            return Response({
                'status': 'success',
                'message': 'Connexion réussie',
                'username': user.username
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur ou mot de passe incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
