from django.contrib import admin
from django.contrib.auth import get_user_model


User = get_user_model()


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'username')


admin.site.register(User, CustomUserAdmin)
