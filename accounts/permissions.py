from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permission class to check if user has admin role.
    Allows access only to users with 'admin' role.
    """
    
    def has_permission(self, request, view):
        """
        Check if the authenticated user has admin role.
        """
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
            and request.user.is_staff
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Permission class that allows read-only access to all authenticated users
    but write access only to admin users.
    """
    
    def has_permission(self, request, view):
        """
        Allow read permissions for authenticated users,
        write permissions only for admin users.
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Read permissions for all authenticated users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        # Write permissions only for admin users
        return request.user.is_superuser and request.user.is_staff