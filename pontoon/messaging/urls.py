from django.urls import path

from . import views

urlpatterns = [
    # Email consent
    path(
        "email-consent/",
        views.email_consent,
        name="pontoon.messaging.email_consent",
    ),
    path(
        "dismiss-email-consent/",
        views.dismiss_email_consent,
        name="pontoon.messaging.dismiss_email_consent",
    ),
]
