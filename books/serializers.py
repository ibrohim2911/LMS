from rest_framework import serializers
from .models import Category, Tag, Kitob, Comment, Reservation, Journals, Rating, Bookmark, Author, subCategory
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


class subCategorySerializer(serializers.ModelSerializer):
    """Serizalizer for sub category model"""
    class Meta:
        model = subCategory
        fields = '__all__'
class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author"""
    class Meta:
        model = Author
        fields = ("name",)
class RatingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Rating model.
    """
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Rating
        fields = ('id', 'user', 'score', 'comment', 'c_at')
        read_only_fields = ('c_at',)

class KitobSerializer(serializers.ModelSerializer):
    # For read operations, show the full nested object.
    has_audio = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)
    subcategory = subCategorySerializer(read_only=True)
    author = AuthorSerializer(many=True, read_only=True)
    # For write operations (create/update), accept the ID for the foreign key/many-to-many fields.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False
    )
    
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=subCategory.objects.all(), source='subcategory', write_only=True 
    )
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source='author', write_only=True
    )
    def get_average_rating(self, obj):
        """Calculate and return the average rating for the book."""
        return obj.get_average_rating()

    class Meta:
        model = Kitob
        fields = (
            'id', 'name', 'description', 'author', 'isbn', 'rating', 'is_available','is_frequent', 
            'quantity','img', 'c_at', 'u_at', 'published_date', 'pdf', 'audio', 'is_physical','pages',
            'category', 'tags','subcategory',  'ratings', 'average_rating','has_audio', 'has_pdf',  # Read-only nested fields
            'category_id', 'tag_ids', 'subcategory_id', 'author_ids'  # Write-only ID fields
        )
    def get_has_audio(self, obj):
        return bool(obj.audio)

    def get_has_pdf(self, obj):
        return bool(obj.pdf)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # If the user is NOT logged in, we "mask" the actual file URLs
        if request and not request.user.is_authenticated:
            representation['audio'] = None
            representation['pdf'] = None
            
        return representation



class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Reservation model.
    """
    # Using StringRelatedField to show a human-readable representation of related objects.
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.StringRelatedField(read_only=True)
    author = serializers.SerializerMethodField()
    img = serializers.ImageField(source='book.img', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    def get_author(self, obj):
        return ", ".join([str(author) for author in obj.book.author.all()])

    class Meta:
        model = Reservation
        fields = ('id', 'user', 'book', 'author', 'img', 'first_name', 'last_name', 'status', 
                  'place', 'c_at', 'reserved_from', 'reserved_until', 'approved_at', 'returned_at')
                  
        # Make fields read-only if they should be set by the system, not the user directly.
        read_only_fields = ('status', 'c_at')

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for the Comment model."""
    user  = UserSerializer(read_only=True)
    book = KitobSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = '__all__'
class BookmarkSerializer(serializers.ModelSerializer):
    """Serializer for the Bookmark model."""
    user = UserSerializer(read_only=True)
    book = KitobSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ('id', 'user', 'book', 'c_at')
        read_only_fields = ('c_at',)
