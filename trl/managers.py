from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, guid, password, **extra_fields):
        if not guid:
            raise ValueError(('The GUID must be set'))
        guid = guid
        user = self.model(guid=guid, **extra_fields)
        user.save()
        return user

    def create_superuser(self, guid, password, **extra_fields):
        extra_fields.setdefault('full_name', "NULL")
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('Superuser must have is_superuser=True.'))
            
        guid = guid
        user = self.model(guid=guid, **extra_fields)
        user.set_password(password)
        user.save()
        return user