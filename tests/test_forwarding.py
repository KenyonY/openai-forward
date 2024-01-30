import importlib
from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from openai_forward.forward.core import GenericForward


@pytest.fixture(
    params=[
        {
            "FWD_KEY": {'fk0': 0, 'fk1': 1, 'fk2': 2},
            "OPENAI_API_KEY": {'sk1': [0, 1], 'sk2': [1], 'sk3': [2], 'sk4': [0]},
            "LEVEL_MODELS": {
                1: ['gpt-3.5-turbo', 'text-embedding-3-small'],
                2: ['tts-1'],
                3: ['dall-e-3'],
            },
        },
    ]
)
def openai_forward(request):
    from openai_forward import settings

    settings.FWD_KEY = request.param['FWD_KEY']
    settings.OPENAI_API_KEY = request.param['OPENAI_API_KEY']
    settings.LEVEL_MODELS = request.param['LEVEL_MODELS']

    # reload OpenaiForward
    import openai_forward

    importlib.reload(openai_forward.forward.core)

    openai_forward = openai_forward.forward.core.OpenaiForward(
        'http://test.com', '/test'
    )
    yield openai_forward


def test_generic_forward_prepares_client_correctly():
    generic_forward = GenericForward('http://test.com', '/test')
    request = Mock(spec=Request)
    request.headers = {'content-type': 'application/json'}
    request.scope = {'root_path': '', 'path': '/test/123'}
    request.url.query = ''
    client_config = generic_forward.prepare_client(request, return_origin_header=True)
    assert client_config['url'] == 'http://test.com/123'
    assert client_config['route_path'] == '/123'


def test_openai_forward_prepares_client_correctly(openai_forward):
    request = Mock(spec=Request)
    request.headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer test',
    }
    request.scope = {'root_path': '', 'path': '/test/123'}
    request.url.query = ''
    client_config = openai_forward.prepare_client(request, return_origin_header=False)
    assert client_config['url'] == 'http://test.com/123'
    assert client_config['route_path'] == '/123'
    assert client_config['auth'] == 'Bearer test'


def test_openai_forward_fk_to_sk(openai_forward):

    sk, level = openai_forward.fk_to_sk('fk1')
    assert level == 1
    assert sk in ('sk1', 'sk2')
    sk, level = openai_forward.fk_to_sk('fk2')
    assert level == 2
    assert sk in ('sk3',)

    sk, level = openai_forward.fk_to_sk('fk0')
    assert level == 0
    assert sk in ('sk1', 'sk4')

    sk, level = openai_forward.fk_to_sk('fk0')
    assert level == 0
    assert sk in ('sk1', 'sk4')


def test_openai_forward_auth_handle(openai_forward):
    request = Mock(spec=Request)
    fk = 'fk0'
    request.headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {fk}',
    }
    request.scope = {'root_path': '', 'path': '/test/123'}
    request.url.query = ''

    client_config = openai_forward.prepare_client(request)
    auth, model_set = openai_forward.handle_authorization(client_config)
    assert 'gpt-4' in model_set
    assert 'gpt-3.5-turbo' in model_set

    fk = 'fk1'
    request.headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {fk}',
    }
    client_config = openai_forward.prepare_client(request)
    auth, model_set = openai_forward.handle_authorization(client_config)
    assert 'gpt-3.5-turbo' in model_set
    assert 'gpt-4' not in model_set
