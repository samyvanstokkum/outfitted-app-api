from rest_framework import serializers

from core.models import Tag, Item, Post


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)

class ItemSerializer(serializers.ModelSerializer):
    """Serializer for item objects"""

    class Meta:
        model = Item
        fields = ('id', 'name')
        read_only_fields = ('id',)


class PostSerializer(serializers.ModelSerializer):
    """Serializer for post objects"""
    items = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Item.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Post
        fields = ('id', 'title', 'items', 'tags')
        read_only_fields = ('id',)

class PostDetailSerializer(PostSerializer):
    """Serialze a post detail"""
    items = ItemSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)