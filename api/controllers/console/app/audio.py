import logging

from flask import request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import InternalServerError

import services
from controllers.console import api
from controllers.console.app import _get_app
from controllers.console.app.error import (
    AppUnavailableError,
    AudioTooLargeError,
    CompletionRequestError,
    NoAudioUploadedError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderNotSupportSpeechToTextError,
    ProviderQuotaExceededError,
    UnsupportedAudioTypeError,
)
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.model_runtime.errors.invoke import InvokeError
from libs.login import login_required
from services.audio_service import AudioService
from services.errors.audio import (
    AudioTooLargeServiceError,
    NoAudioUploadedServiceError,
    ProviderNotSupportSpeechToTextServiceError,
    UnsupportedAudioTypeServiceError,
)


class ChatMessageAudioApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, app_id):
        app_id = str(app_id)
        app_model = _get_app(app_id, 'chat')

        file = request.files['file']

        try:
            response = AudioService.transcript_asr(
                tenant_id=app_model.tenant_id,
                file=file,
                end_user=None,
                promot=app_model.app_model_config.pre_prompt
            )

            return response
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
        except NoAudioUploadedServiceError:
            raise NoAudioUploadedError()
        except AudioTooLargeServiceError as e:
            raise AudioTooLargeError(str(e))
        except UnsupportedAudioTypeServiceError:
            raise UnsupportedAudioTypeError()
        except ProviderNotSupportSpeechToTextServiceError:
            raise ProviderNotSupportSpeechToTextError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception(f"internal server error, {str(e)}.")
            raise InternalServerError()


class ChatMessageTextApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, app_id):
        app_id = str(app_id)
        app_model = _get_app(app_id, None)

        try:
            response = AudioService.transcript_tts(
                tenant_id=app_model.tenant_id,
                text=request.form['text'],
                voice=app_model.app_model_config.text_to_speech_dict.get('voice'),
                streaming=False
            )

            return {'data': response.data.decode('latin1')}
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
        except NoAudioUploadedServiceError:
            raise NoAudioUploadedError()
        except AudioTooLargeServiceError as e:
            raise AudioTooLargeError(str(e))
        except UnsupportedAudioTypeServiceError:
            raise UnsupportedAudioTypeError()
        except ProviderNotSupportSpeechToTextServiceError:
            raise ProviderNotSupportSpeechToTextError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception(f"internal server error, {str(e)}.")
            raise InternalServerError()


class TextModesApi(Resource):
    def get(self, app_id: str):
        app_model = _get_app(str(app_id))

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('language', type=str, required=True, location='args')
            args = parser.parse_args()

            response = AudioService.transcript_tts_voices(
                tenant_id=app_model.tenant_id,
                language=args['language'],
            )

            return response
        except services.errors.audio.ProviderNotSupportTextToSpeechLanageServiceError:
            raise AppUnavailableError("Text to audio voices language parameter loss.")
        except NoAudioUploadedServiceError:
            raise NoAudioUploadedError()
        except AudioTooLargeServiceError as e:
            raise AudioTooLargeError(str(e))
        except UnsupportedAudioTypeServiceError:
            raise UnsupportedAudioTypeError()
        except ProviderNotSupportSpeechToTextServiceError:
            raise ProviderNotSupportSpeechToTextError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception(f"internal server error, {str(e)}.")
            raise InternalServerError()


api.add_resource(ChatMessageAudioApi, '/apps/<uuid:app_id>/audio-to-text')
api.add_resource(ChatMessageTextApi, '/apps/<uuid:app_id>/text-to-audio')
api.add_resource(TextModesApi, '/apps/<uuid:app_id>/text-to-audio/voices')
