from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, exceptions, status
from .models import Profile, Token
from django.contrib.auth import user_logged_in
from rest_framework.decorators import action
from .serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response
from .auth import TokenAuth
from django.db import transaction


def get_verify_number():
    import random
    s = ''
    for _ in range(10):
        s += str(random.randint(1, 10))
    return s


class RegisterView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Profile.objects.none()
    serializer_class = UserSerializer

    def authenticate_user(self, token):

        with transaction.atomic():
            user, created = TokenAuth().authenticate_credentials(token=token)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = User.objects.create(
                username=serializer.data['username'],
            )
            Profile.objects.create(user=user)
            auth_token, token = Token.objects.create(user=user)
            from django.core.mail import EmailMessage
            vc = get_verify_number()
            user.profile.cart['verify'] = vc
            user.profile.save()
            mail = EmailMessage('verify code', f'Your verify code is {vc}', [request.user.email])
            mail.send()
            return Response({'token': token, 'auth': auth_token}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=False, permission_classes=[IsAuthenticated])
    def verify(self, request):
        code = request.data.get('code', None)
        if not code:
            raise exceptions.NotAcceptable
        else:
            if code != request.user.profile.cart.get('verify', ''):
                raise exceptions.NotAcceptable
            else:
                return Response(dict(), status.HTTP_200_OK)
