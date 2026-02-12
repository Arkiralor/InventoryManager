from django.db.models.signals import pre_delete, post_save
from requests import post
from auth_app.models import User, UserProfile
from auth_app import logger


class UserModelSignals:
    MODEL = User

    @classmethod
    def create(cls, sender, instance: User, created: bool, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)
            logger.info(f"User <{instance.email}> created successfully.")

    @classmethod
    def update(cls, sender, instance: User, created: bool, **kwargs):
        if not created:
            logger.info(f"User <{instance.email}> updated successfully.")

    @classmethod
    def deleted(cls, sender, instance: User, **kwargs):
        logger.info(f"User <{instance.email}> deleted successfully.")


post_save.connect(reciever=UserModelSignals.create, sender=UserModelSignals.MODEL)
post_save.connect(reciever=UserModelSignals.update, sender=UserModelSignals.MODEL)
pre_delete.connect(reciever=UserModelSignals.deleted, sender=UserModelSignals.MODEL)


class UserProfileModelSignals:
    MODEL = UserProfile

    @classmethod
    def create(cls, sender, instance: UserProfile, created: bool, **kwargs):
        if created:
            logger.info(
                f"UserProfile for user <{instance.user.email}> created successfully."
            )

    @classmethod
    def update(cls, sender, instance: UserProfile, created: bool, **kwargs):
        if not created:
            logger.info(
                f"UserProfile for user <{instance.user.email}> updated successfully."
            )

    @classmethod
    def deleted(cls, sender, instance: UserProfile, **kwargs):
        logger.info(
            f"UserProfile for user <{instance.user.email}> deleted successfully."
        )


post_save.connect(
    reciever=UserProfileModelSignals.create, sender=UserProfileModelSignals.MODEL
)
post_save.connect(
    reciever=UserProfileModelSignals.update, sender=UserProfileModelSignals.MODEL
)
pre_delete.connect(
    reciever=UserProfileModelSignals.deleted, sender=UserProfileModelSignals.MODEL
)
