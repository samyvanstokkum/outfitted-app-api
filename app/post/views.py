from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Item, Post

from post import serializers


class BasePostAttributeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    """Base viewset for user owned post attributes"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')
    
    def perform_create(self, serializer):
        """Create a new tag"""
        serializer.save(user=self.request.user)


class TagViewSet(BasePostAttributeViewSet):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class ItemViewSet(BasePostAttributeViewSet):
    """Manage items in the database"""
    queryset = Item.objects.all()
    serializer_class = serializers.ItemSerializer


class PostViewSet(viewsets.ModelViewSet):
    """Manage posts in the database"""
    serializer_class = serializers.PostSerializer
    queryset = Post.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieve the posts for the authenticated user"""
        return self.queryset.filter(user=self.request.user)
