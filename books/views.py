from rest_framework import viewsets
from .models import Category, Tag, Kitob, Ebook, Reservation, Journals
from .serializers import (
    CategorySerializer, TagSerializer, KitobSerializer, EbookSerializer,
    ReservationSerializer, JournalsSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TagViewSet(viewsets.ModelViewSet):
    """API endpoint for tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class KitobViewSet(viewsets.ModelViewSet):
    """API endpoint for books (Kitob)."""
    queryset = Kitob.objects.all()
    serializer_class = KitobSerializer


class EbookViewSet(viewsets.ModelViewSet):
    """API endpoint for ebooks."""
    queryset = Ebook.objects.all()
    serializer_class = EbookSerializer


class JournalsViewSet(viewsets.ModelViewSet):
    """API endpoint for journals."""
    queryset = Journals.objects.all()
    serializer_class = JournalsSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    """API endpoint for reservations."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
