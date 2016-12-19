# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import serializers

from shop.rest.serializers import ProductSummarySerializerBase
from stables_shop.models.product import Product


class ProductSummarySerializer(ProductSummarySerializerBase):
    media = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'product_name', 'product_url', 'product_model', 'price',
            'media', 'caption')

    def get_media(self, product):
        return self.render_html(product, 'media')
