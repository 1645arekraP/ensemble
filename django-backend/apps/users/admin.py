from django.contrib import admin
from django.contrib.auth import get_user_model

# Register your models here.
User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email',)
    list_filter = ('is_staff', 'is_active')
    ordering = ('-date_joined',)
    readonly_fields = ('id', 'date_joined')
    
    def has_add_permission(self, request):
        return False