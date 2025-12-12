from core.celery import app


@app.task
def background_verify_user(user_id):
    from account.v1.services.profile import KYCService

    kyc_service = KYCService(None)
    _ = kyc_service.fetch_verification_data_from_service(user_id)
