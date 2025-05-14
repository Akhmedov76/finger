import os
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.permissions import IsSuperUser


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title='Cargo Logistic - System API',
        description='Cargo Logistic API',
        default_version="v1",
    ),
    public=True,
    generator_class=BothHttpAndHttpsSchemaGenerator,
    permission_classes=[IsSuperUser],
    authentication_classes=[JWTAuthentication, BasicAuthentication, SessionAuthentication],
    url=os.environ.get('SWAGGER_URL'),
)
