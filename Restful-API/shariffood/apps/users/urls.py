from rest_framework import routers
from .views import *

app_name = 'users'

router = routers.DefaultRouter()
router.include_root_view = False

router.register('register', RegisterView, basename='register')

urlpatterns = router.urls + [
    # add your urls here
]