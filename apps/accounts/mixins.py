from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class PanitiaRequiredMixin(LoginRequiredMixin):
    """
    Mixin untuk membatasi akses hanya panitia / staff
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.is_panitia():
            raise PermissionDenied("Anda tidak memiliki akses ke halaman ini")

        return super().dispatch(request, *args, **kwargs)
