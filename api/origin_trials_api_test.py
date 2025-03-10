# Copyright 2024 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import mock

import flask
import requests
import werkzeug.exceptions  # Flask HTTP stuff.

import testing_config  # Must be imported before the module under test.
from api import origin_trials_api
from chromestatus_openapi.models import GetOriginTrialsResponse
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals.user_models import AppUser

test_app = flask.Flask(__name__)


class OriginTrialsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1,
        owner_emails=['owner@example.com'])
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ot_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=150,
        origin_trial_id='-1234567890')
    self.ot_stage_1.put()

    self.extension_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=151,
        ot_stage_id=self.ot_stage_1.key.integer_id(),
        milestones=MilestoneSet(desktop_last=153),
        intent_thread_url='https://example.com/intent')
    self.extension_stage_1.put()
    self.extension_gate_1 = Gate(feature_id=self.feature_1_id,
                stage_id=self.extension_stage_1.key.integer_id(),
                gate_type=3, state=Vote.APPROVED)
    self.extension_gate_1.put()

    self.feature_2 = FeatureEntry(
        feature_type=1, name='feature two', summary='sum', category=1)
    self.feature_2.put()
    self.ot_stage_2 = Stage(
        feature_id=self.feature_2.key.integer_id(), stage_type=150,
        origin_trial_id='9876543210')
    self.ot_stage_2.put()
    self.handler = origin_trials_api.OriginTrialsAPI()
    self.request_path = (
        '/api/v0/origintrials/'
        f'{self.feature_1_id}/{self.extension_stage_1.key.integer_id()}/extend')

    self.google_user = AppUser(email='feature_owner@google.com')
    self.google_user.put()


    self.mock_trials_list = [
      {
        'id': '-5269211564023480319',
        'display_name': 'Example Trial',
        'description': 'A description.',
        'origin_trial_feature_name': 'ExampleTrial',
        'status': 'ACTIVE',
        'enabled': True,
        'chromestatus_url': 'https://example.com/chromestatus',
        'start_milestone': '123',
        'end_milestone': '456',
        'original_end_milestone': '450',
        'feedback_url': 'https://example.com/feedback',
        'documentation_url': 'https://example.com/docs',
        'intent_to_experiment_url': 'https://example.com/intent',
        'trial_extensions': [{}],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': True,
        'end_time': '2025-01-01T00:00:00Z',
      },
    ]

    self.mock_web_usecounters_file = """
enum WebFeature {
  kSomeFeature = 1,
  kValidFeature = 2,
  kNoThirdParty = 3
  kSample = 4,
  kNoCriticalTrial = 5,
};
"""

    self.mock_webdx_usecounters_file = """
enum WebDXFeature {
  kSomeFeature = 1,
  kValidFeature = 2,
  kNoThirdParty = 3,
  kSample = 4,
  kNoCriticalTrial = 5,
  kValidTrial = 6,
};
"""

    self.mock_css_property_id_usecounters_file = """
enum CSSSampleId {
  kSomeFeature = 1,
  kValidFeature = 2,
  kNoThirdParty = 3,
  kSample = 4,
  kNoCriticalTrial = 5,
  kValidTrial = 6,
};
"""

    self.mock_features_file = """
{
  "data": [
    {
      "name": "ValidFeaturePart1",
      "origin_trial_feature_name": "ValidFeature",
      "origin_trial_allows_third_party": true
    },
    {
      "name": "ValidFeaturePart2",
      "origin_trial_feature_name": "ValidFeature",
      "origin_trial_allows_third_party": true
    },
    {
      "name": "InvalidFeaturePart1",
      "origin_trial_feature_name": "InvalidFeature"
    },
    {
      "name": "NoThirdParty",
      "origin_trial_feature_name": "NoThirdParty"
    },
    {
      "name": "NoCriticalTrialEntry",
      "origin_trial_feature_name": "NoCriticalTrial"
    }
  ]
}
"""

    self.mock_grace_period_file = """
bool FeatureHasExpiryGracePeriod(blink::mojom::OriginTrialFeature feature) {
  static blink::mojom::OriginTrialFeature const kHasExpiryGracePeriod[] = {
      // Production grace period trials start here:
      blink::mojom::OriginTrialFeature::kSomeFeature,
      blink::mojom::OriginTrialFeature::kValidFeature,
      blink::mojom::OriginTrialFeature::kInvalidFeature,
  };
  return base::Contains(kHasExpiryGracePeriod, feature);
}
"""

    self.existing_origin_trials = [
      {
        'origin_trial_feature_name': 'ExistingFeature',
      }
    ]
    self.mock_chromium_files_dict = {
      'webfeature_file': self.mock_web_usecounters_file,
      'webdxfeature_file': self.mock_webdx_usecounters_file,
      'css_property_id_file': self.mock_css_property_id_usecounters_file,
      'enabled_features_text': self.mock_features_file,
      'grace_period_file': self.mock_grace_period_file,
    }
  def tearDown(self):
    for kind in [AppUser, FeatureEntry, Gate, Stage]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_get__valid(self, mock_get_trials_list):
    """A list of public trials is returned."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_get_trials_list.return_value = [
        {'id': '123', 'display_name': 'Example Trial'}]
    with test_app.test_request_context(
        self.request_path, method='GET', json={}):
      result = self.handler.do_get()
    self.assertEqual(GetOriginTrialsResponse.from_dict({
      'origin_trials': [
        {'id': '123', 'display_name': 'Example Trial'}
      ]
    }), result)

  @mock.patch('logging.exception')
  @mock.patch('logging.error')
  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_get__invalid(
      self, mock_get_trials_list, mock_log_error, mock_log_exception):
    """A request error from the origin trials API raises the correct exception."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_get_trials_list.side_effect = requests.exceptions.RequestException
    with test_app.test_request_context(
        self.request_path, method='GET', json={}):
      with self.assertRaises(werkzeug.exceptions.InternalServerError):
        self.handler.do_get()

  def test_check_post_permissions__anon(self):
    """Anon users cannot request origin trials."""
    testing_config.sign_out()
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.check_post_permissions(self.feature_1_id)

  def test_check_post_permissions__rando(self):
    """Random users cannot request origin trials."""
    testing_config.sign_in('user@example.com', 1234567890)
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.check_post_permissions(self.feature_1_id)

  def test_check_post_permissions__googler_chromie(self):
    """Googlers and chromies can request origin trials."""
    testing_config.sign_in('user@google.com', 1234567890)
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      result = self.handler.check_post_permissions(self.feature_1_id)
    self.assertEqual({}, result)

    testing_config.sign_in('user@chromium.org', 1234567890)
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      result = self.handler.check_post_permissions(self.feature_1_id)
    self.assertEqual({}, result)

  def test_check_post_permissions__feature_owner(self):
    """Feature owners may request an OT."""
    testing_config.sign_in('owner@example.com', 1234567890)
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      result = self.handler.check_post_permissions(self.feature_1_id)
    self.assertEqual({}, result)

  def test_do_post__feature_not_found(self):
    """Give a 404 if the no such feature exists."""
    kwargs = {'feature_id': '999'}
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
       self.handler.do_post(**kwargs)

  def test_do_post__stage_not_found(self):
    """Give a 404 if the no such stage exists."""
    kwargs = {
        'feature_id': str(self.feature_1_id),
        'stage_id': '999'}
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
       self.handler.do_post(**kwargs)

  def test_do_post__anon(self):
    """Anon users cannot request origin trials."""
    testing_config.sign_out()
    kwargs = {
        'feature_id': str(self.feature_1_id),
        'stage_id': str(self.ot_stage_1.key.integer_id())}
    with test_app.test_request_context(
        self.request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(**kwargs)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__valid_webfeature(
      self, mock_get_trials_list):
    """No error messages should be returned if all args are valid using a
    WebFeature use counter."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kValidFeature',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': True,
      },
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__valid_deprecation_trial(
      self, mock_get_trials_list):
    """No error messages should be returned if all args are valid for a
    deprecation trial."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': None,
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': True,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': True,
      },
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__valid_webdxfeature(
      self, mock_get_trials_list):
    """No error messages should be returned if all args are valid using a
    WebDXFeature use counter."""
    mock_get_trials_list.return_value = self.mock_trials_list

    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'WebDXFeature::kValidFeature',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': True,
      },
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__valid_css_property_id(
      self, mock_get_trials_list):
    """No error messages should be returned if all args are valid using a
    CSSSampleId use counter."""
    mock_get_trials_list.return_value = self.mock_trials_list

    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'CSSSampleId::kValidFeature',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': True,
      },
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__invalid_webfeature_use_counter(
      self, mock_get_trials_list):
    """Error message returned if UseCounter not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kBadUseCounter',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {
      'ot_webfeature_use_counter': 'UseCounter not landed in web_feature.mojom'}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__invalid_webdxfeature_use_counter(
      self, mock_get_trials_list):
    """Error message returned if WebDXFeature UseCounter not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'WebDXFeature::kBadUseCounter'
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {
      'ot_webfeature_use_counter': 'UseCounter not landed in webdx_feature.mojom'}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__missing_webdxfeature_use_counter(
      self, mock_get_trials_list):
    """Error message returned if WebDXFeature UseCounter not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'WebDXFeature::'
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {
      'ot_webfeature_use_counter': 'No WebDXFeature use counter provided.'}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__missing_webfeature_use_counter(
      self, mock_get_trials_list):
    """Error message returned if both UseCounter types are missing for a
    non-deprecation trial."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_webfeature_use_counter': None,
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    # A validation error should exist for both use counter fields.
    expected = {
      'ot_webfeature_use_counter': (
          'No UseCounter specified for non-deprecation trial.')
    }
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__missing_webfeature_use_counter_deprecation(
      self, mock_get_trials_list):
    """No error message returned for missing UseCounter if deprecation trial."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidFeature',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_webfeature_use_counter': None,
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': True,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__invalid_chromium_trial_name(self, mock_get_trials_list):
    """Error message returned if Chromium trial name not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'NonexistantFeature',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kValidFeature',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {'ot_chromium_trial_name': (
        'Origin trial feature name not found in file')}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__missing_chromium_trial_name(
      self, mock_get_trials_list):
    """Error message returned if Chromium trial is missing from request."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kValidFeature',
      },
      'ot_chromium_trial_name': None,
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_creation_args(
            body, self.mock_chromium_files_dict)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__invalid_third_party_trial(
      self, mock_get_trials_list):
    """Error message returned if third party support not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'NoThirdParty',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kNoThirdParty',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': False,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': True,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {'ot_has_third_party_support': (
        'One or more features do not have third party '
        'support set in runtime_enabled_features.json5. '
        'Feature name: NoThirdParty')}
    self.assertEqual(expected, result)

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_validate_creation_args__invalid_critical_trial(
      self, mock_get_trials_list):
    """Error message returned if critical trial name not found in file."""
    mock_get_trials_list.return_value = self.mock_trials_list
    body = {
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'NoCriticalTrial',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'kNoCriticalTrial',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    with test_app.test_request_context(self.request_path):
      result = self.handler._validate_creation_args(
          body, self.mock_chromium_files_dict)
    expected = {'ot_is_critical_trial': (
        'Use counter has not landed in grace period array for critical trial')}
    self.assertEqual(expected, result)

  def test_validate_extension_args__valid(self):
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      self.handler._validate_extension_args(
          self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_ot_id(self):
    self.ot_stage_1.origin_trial_id = None
    self.ot_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_end_milestone(self):
    self.extension_stage_1.milestones.desktop_last = None
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__invalid_intent_url(self):
    self.extension_stage_1.intent_thread_url = 'This can\'t be right.'
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_intent_url(self):
    self.extension_stage_1.intent_thread_url = None
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__na(self):
    """N/A state should be counted as approved."""
    self.extension_gate_1.state = Vote.NA
    self.extension_gate_1.put()
    with test_app.test_request_context(self.request_path):
      self.handler._validate_extension_args(
          self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__not_approved(self):
    """Non-approved extensions should not be processed."""
    self.extension_gate_1.state = Vote.DENIED
    self.extension_gate_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  @mock.patch('api.origin_trials_api.OriginTrialsAPI._validate_creation_args')
  @mock.patch('api.origin_trials_api.get_chromium_files_for_validation')
  def test_post__valid(self, mock_get_chromium_files, mock_validate_func):
    """A valid OT creation request is processed and marked for creation."""
    mock_get_chromium_files.return_value = self.mock_chromium_files_dict
    mock_validate_func.return_value = {}
    testing_config.sign_in('feature_owner@google.com', 1234567890)
    body = {
      'ot_display_name': {
        'form_field_name': 'ot_display_name',
        'value': 'example trial',
      },
      'ot_description': {
        'form_field_name': 'ot_description',
        'value': 'a short description',
      },
      'ot_owner_email': {
        'form_field_name': 'ot_owner_email',
        'value': 'user@google.com',
      },
      'ot_emails': {
        'form_field_name': 'ot_emails',
        'value': 'contact1@example.com,contact2@example.com',
      },
      'desktop_first': {
        'form_field_name': 'ot_milestone_desktop_start',
        'value': 100,
      },
      'desktop_last': {
        'form_field_name': 'ot_milestone_desktop_end',
        'value': 106,
      },
      'intent_thread_url': {
        'form_field_name': 'ot_creation__intent_to_experiment_url',
        'value': 'https://example.com/intent',
      },
      'ot_documentation_url': {
        'form_field_name': 'ot_documentation_url',
        'value': 'https://example.com/docs',
      },
      'ot_feedback_submission_url': {
        'form_field_name': 'ot_feedback_submission_url',
        'value': 'https://example.com/feedback',
      },
      'ot_require_approvals': {
        'form_field_name': 'ot_require_approvals',
        'value': True,
      },
      'ot_approval_buganizer_component': {
        'form_field_name': 'ot_approval_buganizer_component',
        'value': '123456',
      },
      'ot_approval_buganizer_custom_field_id': {
        'form_field_name': 'ot_approval_buganizer_custom_field_id',
        'value': '111111',
      },
      'ot_approval_group_email': {
        'form_field_name': 'ot_approval_group_email',
        'value': 'users@google.com',
      },
      'ot_approval_criteria_url': {
        'form_field_name': 'ot_approval_criteria_url',
        'value': 'https://example.com/criteria',
      },
      'ot_chromium_trial_name': {
        'form_field_name': 'ot_chromium_trial_name',
        'value': 'ValidTrial',
      },
      'ot_webfeature_use_counter': {
        'form_field_name': 'ot_webfeature_use_counter',
        'value': 'WebDXFeature::kValidTrial',
      },
      'ot_is_critical_trial': {
        'form_field_name': 'ot_is_critical_trial',
        'value': True,
      },
      'ot_is_deprecation_trial': {
        'form_field_name': 'ot_is_deprecation_trial',
        'value': False,
      },
      'ot_has_third_party_support': {
        'form_field_name': 'ot_has_third_party_support',
        'value': False,
      },
    }
    request_path = (
        f'{self.feature_1_id}/{self.ot_stage_1.key.integer_id()}/create')
    with test_app.test_request_context(request_path, json=body):
      response = self.handler.do_post(feature_id=self.feature_1_id,
                                      stage_id=self.ot_stage_1.key.integer_id())
    self.assertEqual(response,
                     {'message': 'Origin trial creation request submitted.'})

    # Verify fields have been updated.
    for field, field_info in body.items():
      value = field_info['value']
      # Handle string of emails as a list.
      if field == 'ot_emails':
        value = field_info['value'].split(',')
      elif (field == 'ot_approval_buganizer_component' or
            field == 'ot_approval_buganizer_custom_field_id'):
        value = int(value)
      # Check milestone fields
      elif field == 'desktop_first' or field == 'desktop_last':
        self.assertEqual(getattr(self.ot_stage_1.milestones, field), value)
        continue
      self.assertEqual(getattr(self.ot_stage_1, field), value)
    # Use counter bucket number should be updated.
    self.assertEqual(self.ot_stage_1.ot_use_counter_bucket_number, 6)
    # Stage should be marked as "Ready for creation"
    self.assertEqual(self.ot_stage_1.ot_setup_status, 2)
