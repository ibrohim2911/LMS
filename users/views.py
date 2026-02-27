from rest_framework.response import Response
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer

def getme(request):
    """API endpoint to get the current authenticated user's information."""
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    else:
        return Response({'detail': 'Authentication credentials were not provided.'}, status=401)
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    # Add permission classes if you want to restrict access, e.g., only admins can list all users.
