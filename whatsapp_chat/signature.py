import hashlib
import hmac

from django.conf import settings


def is_valid_signature(request) -> bool:
    """Confere o cabeçalho X-Hub-Signature-256 que a Meta envia em todo
    POST do webhook. É a única forma de garantir que o payload realmente
    veio da Meta e não de qualquer pessoa que descubra a URL — por isso o
    webhook é @csrf_exempt (não é um formulário de navegador) mas nunca
    processa um POST sem essa verificação passar."""

    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        return False

    received_signature = signature_header.removeprefix("sha256=")
    expected_signature = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=request.body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(received_signature, expected_signature)
