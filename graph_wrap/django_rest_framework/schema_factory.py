from __future__ import unicode_literals

import graphene
from graphene_django.settings import perform_import

from .field_resolvers import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import transform_api


class SchemaFactory(object):
    """Factory class for creating a graphene Schema object.

    Given a list of DRF view sets, this object
    has the functionality to produce a graphene Schema object.
    This is achieved by collecting, for each viewset,
    the graphene ObjectType produced by transforming that view set
    and also the relevant root Query data for that ObjectType
    (mounted field and field resolver). This data is then used
    to dynamically build a graphene Query class, which is
    passed into a Schema as usual.

    Note: currently only resources which inherit from
    rest_framework.viewsets.ModelViewSet can be used. Any
    resource which does not satisfy this condition will
    be silently filtered.
    """
    resource_class_to_schema = dict()

    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls, api):
        """
        Create a schema from the DRF viewset instance.

        Can pass either the full python path of the API
        instance or an Api instance itself.
        """
        api = perform_import(api, '')
        resources = api._registry.values()
        return cls(resources).create()

    def create(self):
        query_class_attrs = dict()
        for resource in self._usable_resources():
            query_attributes = QueryAttributes(resource)
            query_class_attrs.update(**query_attributes.to_dict())
            self.resource_class_to_schema[resource.__class__] = (
                query_attributes.graphene_type)
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        return graphene.Schema(query=Query)

    def _usable_resources(self):
        return []


class QueryAttributes(object):
    """Create the graphene Query class attributes relevant to a resource."""

    def __init__(self, api):
        self._resource = api
        self.graphene_type = transform_api(api)
        self._single_item_field_name = api._meta.resource_name
        self._all_items_field_name = 'all_{}s'.format(
            self._single_item_field_name)
        self._single_item_resolver_name = 'resolve_{}'.format(
            self._single_item_field_name)
        self._all_items_resolver_name = 'resolve_{}'.format(
            self._all_items_field_name)

    def to_dict(self):
        return {
            self._single_item_field_name: self._single_item_query_field(),
            self._all_items_field_name: self._all_items_query_field(),
            self._single_item_resolver_name: self._single_item_query_resolver(),
            self._all_items_resolver_name: self._all_items_query_resolver(),
        }

    def _all_items_query_field(self):
        return graphene.List(
            self.graphene_type,
            orm_filters=graphene.String(name='orm_filters'),
            name=self._all_items_field_name,
        )

    def _all_items_query_resolver(self):
        return AllItemsQueryResolver(
            field_name=self._all_items_field_name,
            resource=self._resource,
        )

    def _single_item_query_field(self):
        return graphene.Field(
            self.graphene_type,
            id=graphene.Int(required=True),
            name=self._single_item_field_name,
        )

    def _single_item_query_resolver(self):
        return SingleItemQueryResolver(
            field_name=self._single_item_field_name,
            resource=self._resource,
        )

