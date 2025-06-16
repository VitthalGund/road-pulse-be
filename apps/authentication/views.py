from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            refresh.set_exp(lifetime=timedelta(days=160))

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: "Login successful", 401: "Invalid credentials"},
        operation_description="Authenticate user and return JWT tokens.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                request=request,
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
