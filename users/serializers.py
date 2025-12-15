from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Includes logic for creating and updating users with hashed passwords.
    """
    # The is_banned property is included as a read-only field.
    is_banned = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'is_banned', 'ban_expires_at'
        )
        # Make the password write-only so it's not sent back in API responses.
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def create(self, validated_data):
        """
        Create and return a new `User` instance, given the validated data.
        """
        # Use the custom User model's create_user method to handle password hashing.
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        # Handle password update separately if it exists in the validated data.
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user