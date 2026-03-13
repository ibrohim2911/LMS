from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import AdminPermission, SuperAdminPermission
from drf_spectacular.utils import extend_schema
@extend_schema(
    methods=['get'], responses={200: UserSerializer, 401: 'Unauthorized'},
    description="Get the current authenticated user's information.",
)
class getme(APIView):
    """API endpoint to get the current authenticated user's information."""
    permission_classes = [IsAuthenticated]
    def get(self, request):
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
    permission_classes = [AdminPermission|SuperAdminPermission]
