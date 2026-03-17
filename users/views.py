from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import User, ActiveRefreshToken, Notification
from .serializers import UserSerializer, LogoutSerializer, NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import AdminPermission, SuperAdminPermission
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users only see their own notifications
        return Notification.objects.filter(user=self.request.user)

    # Custom action to mark a specific notification as read
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    # Custom action to mark ALL as read
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh_token = data.get('refresh')
        if refresh_token:
            ActiveRefreshToken.objects.get_or_create(user=self.user, token=str(refresh_token))
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = attrs.get('refresh')
        if not ActiveRefreshToken.objects.filter(token=refresh).exists():
            raise InvalidToken('Token has been logged out')

        try:
            token_obj = RefreshToken(refresh)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        user_id = token_obj.get('user_id')
        user = User.objects.filter(pk=user_id).first()

        data = super().validate(attrs)

        # If a new refresh token is issued (rotation), update the active list.
        new_refresh = data.get('refresh')
        if new_refresh and new_refresh != refresh:
            ActiveRefreshToken.objects.filter(token=refresh).delete()
            if user is not None:
                ActiveRefreshToken.objects.get_or_create(user=user, token=str(new_refresh))

        return data


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class CustomTokenVerifySerializer(TokenVerifySerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        token = attrs.get('token')
        try:
            decoded = UntypedToken(token)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        if getattr(decoded, 'token_type', None) == 'refresh':
            if not ActiveRefreshToken.objects.filter(token=token).exists():
                raise InvalidToken('Token has been logged out')

        return data


class CustomTokenVerifyView(TokenVerifyView):
    serializer_class = CustomTokenVerifySerializer


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
    

@extend_schema(
    request=LogoutSerializer,
    responses={200: {'message': 'Successfully logged out'}, 400: {'error': 'Error message'}},
    description="Logout the current user by deleting the refresh token from the active-token list.",
)
class LogoutView(APIView):
    """API endpoint to logout the current user by deleting the refresh token."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        refresh_token = serializer.validated_data['refresh']
        deleted_count, _ = ActiveRefreshToken.objects.filter(token=refresh_token).delete()
        if deleted_count == 0:
            return Response({'error': 'Token not found or already logged out'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Successfully logged out'})


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [AdminPermission|SuperAdminPermission]
