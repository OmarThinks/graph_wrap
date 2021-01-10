from graphene_django.views import GraphQLView
from rest_framework.decorators import api_view


@api_view(['POST'])
def graphql_view(request):
    from graph_wrap import django_rest_schema
    schema = django_rest_schema()
    view = GraphQLView.as_view(schema=schema)
    return view(request)

