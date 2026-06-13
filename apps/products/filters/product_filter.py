import django_filters
from apps.products.models import Product
from django.db import models

class ProductFilter(django_filters.FilterSet):
    """
    Enterprise declarative filter layout using django-filter.
    Automatically parses types and structures safe SQL statements.
    """
    # 1. Supports passing a raw category UUID string (?category=...)
    category = django_filters.UUIDFilter(field_name="category_id")
    
    # 2. Supports passing an SEO-friendly category slug (?category_slug=smartphones)
    category_slug = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    
    # 3. Dedicated text search keyword across name and description (?search=iphone)
    search = django_filters.CharFilter(method="filter_by_keyword")

    class Meta:
        model = Product
        # Strips out any soft-deleted or hidden records automatically
        fields = ['category', 'category_slug', 'search']

    def filter_by_keyword(self, queryset, name, value):
        """Custom logic for the text search parameter to span multiple columns."""
        if not value:
            return queryset
        return queryset.filter(
            models.Q(name__icontains=value) | models.Q(description__icontains=value)
        )