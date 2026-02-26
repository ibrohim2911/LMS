from rest_framework import serializers
from .models import Category, Tag, Kitob, Ebook, Reservation, Journals, Rating
from users.serializers import UserSerializer
from users.models import User



class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""
    class Meta:
        model = Category
        fields = ('id', 'name')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model."""
    class Meta:
        model = Tag
        fields = ('id', 'name')


class JournalsSerializer(serializers.ModelSerializer):
    """Serializer for the Journals model."""
    class Meta:
        model = Journals
        fields = '__all__'


class EbookSerializer(serializers.ModelSerializer):
    """Serializer for the Ebook model."""
    class Meta:
        model = Ebook
        fields = '__all__'


class KitobSerializer(serializers.ModelSerializer):
    # For read operations, show the full nested object.
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reader = UserSerializer(read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)

    # For write operations (create/update), accept the ID for the foreign key/many-to-many fields.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False
    )
    reader_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='reader', write_only=True, allow_null=True, required=False
    )
    
    def get_average_rating(self, obj):
        """Calculate and return the average rating for the book."""
        return obj.get_average_rating()

    class Meta:
        model = Kitob
        fields = (
            'id', 'name', 'description', 'author', 'isbn', 'rating', 'is_available','is_frequent', 'quantity','img', 'c_at', 'u_at',
            'category', 'tags', 'reader', 'ratings', 'average_rating',  # Read-only nested fields
            'category_id', 'tag_ids', 'reader_id'  # Write-only ID fields
        )


class RatingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Rating model.
    """
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Rating
        fields = ('id', 'user', 'score', 'comment', 'c_at')
        read_only_fields = ('c_at',)


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Reservation model.
    """
    # Using StringRelatedField to show a human-readable representation of related objects.
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Reservation
        fields = ('id', 'user', 'book', 'status', 'place', 'c_at')
        # Make fields read-only if they should be set by the system, not the user directly.
        read_only_fields = ('status', 'c_at')