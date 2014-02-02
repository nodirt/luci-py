#!/usr/bin/env python
# Copyright 2013 The Swarming Authors. All rights reserved.
# Use of this source code is governed by the Apache v2.0 license that can be
# found in the LICENSE file.

# Disable 'Access to a protected member ...'. NDB uses '_' for other purposes.
# pylint: disable=W0212

import datetime
import sys
import unittest

import test_env
test_env.setup_test_env()

from google.appengine.ext import ndb

import test_case
from components import utils


class Rambling(ndb.Model):
  """Fake statistics."""
  a = ndb.IntegerProperty()
  b = ndb.FloatProperty()
  c = ndb.DateTimeProperty()
  d = ndb.DateProperty()


class SmartJsonEncoderTest(test_case.TestCase):
  def test_smart_json(self):
    r = Rambling(
        a=2,
        b=0.2,
        c=datetime.datetime(2012, 1, 2, 3, 4, 5, 6),
        d=datetime.date(2012, 1, 2))
    actual = utils.SmartJsonEncoder().encode([r])
    # Confirm that default is tight encoding and sorted keys.
    expected = (
        '[{"a":2,'
        '"b":0.2,'
        '"c":"2012-01-02 03:04:05",'
        '"d":"2012-01-02"'
        '}]')
    self.assertEqual(expected, actual)


class SerializableModelTest(test_case.TestCase):
  """Tests for utils.SerializableModelMixin and related property converters."""

  def test_simple_properties(self):
    """Simple properties are unmodified in to_serializable_dict()."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      blob_prop = ndb.BlobProperty()
      bool_prop = ndb.BooleanProperty()
      float_prop = ndb.FloatProperty()
      int_prop = ndb.IntegerProperty()
      json_prop = ndb.JsonProperty()
      pickle_prop = ndb.PickleProperty()
      str_prop = ndb.StringProperty()
      text_prop = ndb.TextProperty()

    # Test data in simple dict form.
    as_serializable_dict = {
      'blob_prop': 'blob',
      'bool_prop': True,
      'float_prop': 3.14,
      'int_prop': 42,
      'json_prop': ['a list', 'why', 'not?'],
      'pickle_prop': {'some': 'dict'},
      'str_prop': 'blah-blah',
      'text_prop': 'longer blah-blah',
    }

    # Same data but in entity form. Constructing entity directly from
    # |as_serializable_dict| works only if it contains only simple properties
    # (that look the same in serializable dict and entity form).
    as_entity = Entity(**as_serializable_dict)

    # Ensure all simple properties (from SIMPLE_PROPERTIES) are covered.
    self.assertEqual(
        set(utils.SIMPLE_PROPERTIES),
        set(prop.__class__ for prop in Entity._properties.itervalues()))

    # Check entity -> serializable dict conversion.
    self.assertEqual(
        as_serializable_dict,
        as_entity.to_serializable_dict())

    # Check serializable dict -> Entity conversion.
    self.assertEqual(
        as_entity,
        Entity.from_serializable_dict(as_serializable_dict))

  def test_serializable_properties(self):
    """Check that |serializable_properties| works as expected."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      serializable_properties = {
        'prop_rw': utils.READABLE | utils.WRITABLE,
        'prop_r': utils.READABLE,
        'prop_w': utils.WRITABLE,
        'prop_hidden_1': 0,
      }
      prop_r = ndb.IntegerProperty(default=0)
      prop_w = ndb.IntegerProperty(default=0)
      prop_rw = ndb.IntegerProperty(default=0)
      prop_hidden_1 = ndb.IntegerProperty(default=0)
      prop_hidden_2 = ndb.IntegerProperty(default=0)

    entity = Entity()

    # Only fields with READABLE flag set show up in to_serializable_dict().
    self.assertEqual(
        {'prop_r': 0, 'prop_rw': 0},
        entity.to_serializable_dict())

    # Fields with WRITABLE flag can be used in convert_serializable_dict.
    self.assertEqual(
        {'prop_rw': 1, 'prop_w': 2},
        Entity.convert_serializable_dict({'prop_rw': 1, 'prop_w': 2}))

    # Writable fields are optional.
    self.assertEqual(
        {'prop_rw': 1},
        Entity.convert_serializable_dict({'prop_rw': 1}))

    # convert_serializable_dict ignores read only, hidden and unrecognized keys.
    all_props = {
      'prop_r': 0,
      'prop_rw': 1,
      'prop_w': 2,
      'prop_hidden_1': 3,
      'prop_hidden_2': 4,
      'unknown_prop': 5,
    }
    self.assertEqual(
        {'prop_rw': 1, 'prop_w': 2},
        Entity.convert_serializable_dict(all_props))

  def test_entity_id(self):
    """Test that 'with_id_as' argument in to_serializable_dict is respected."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      pass
    self.assertEqual(
        {'my_id': 'abc'},
        Entity(id='abc').to_serializable_dict(with_id_as='my_id'))

  def test_datetime_properties(self):
    """Test handling of DateTimeProperty."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      dt = ndb.DateTimeProperty()

    # Same point in time as datetime and as timestamp.
    dt = datetime.datetime(2012, 1, 2, 3, 4, 5)
    ts = 1325473445000000

    # Datetime is serialized to a number of milliseconds since epoch.
    self.assertEqual({'dt': ts}, Entity(dt=dt).to_serializable_dict())
    # Reverse operation also works.
    self.assertEqual({'dt': dt}, Entity.convert_serializable_dict({'dt': ts}))

  def test_repeated_properties(self):
    """Test that properties with repeated=True are handled."""
    class IntsEntity(ndb.Model, utils.SerializableModelMixin):
      ints = ndb.IntegerProperty(repeated=True)
    class DatesEntity(ndb.Model, utils.SerializableModelMixin):
      dates = ndb.DateTimeProperty(repeated=True)

    # Same point in time as datetime and as timestamp.
    dt = datetime.datetime(2012, 1, 2, 3, 4, 5)
    ts = 1325473445000000

    # Repeated properties that are not set are converted to empty lists.
    self.assertEqual({'ints': []}, IntsEntity().to_serializable_dict())
    self.assertEqual({'dates': []}, DatesEntity().to_serializable_dict())

    # List of ints works (as an example of simple repeated property).
    self.assertEqual(
        {'ints': [1, 2]},
        IntsEntity(ints=[1, 2]).to_serializable_dict())
    self.assertEqual(
        {'ints': [1, 2]},
        IntsEntity.convert_serializable_dict({'ints': [1, 2]}))

    # List of datetimes works (as an example of not-so-simple property).
    self.assertEqual(
        {'dates': [ts, ts]},
        DatesEntity(dates=[dt, dt]).to_serializable_dict())
    self.assertEqual(
        {'dates': [dt, dt]},
        DatesEntity.convert_serializable_dict({'dates': [ts, ts]}))

  def _test_structured_properties_class(self, structured_cls):
    """Common testing for StructuredProperty and LocalStructuredProperty."""
    # Plain ndb.Model.
    class InnerSimple(ndb.Model):
      a = ndb.IntegerProperty()

    # With SerializableModelMixin.
    class InnerSmart(ndb.Model, utils.SerializableModelMixin):
      serializable_properties = {'a': utils.READABLE | utils.WRITABLE}
      a = ndb.IntegerProperty()
      b = ndb.IntegerProperty()

    class Outter(ndb.Model, utils.SerializableModelMixin):
      simple = structured_cls(InnerSimple)
      smart = structured_cls(InnerSmart)

    # InnerSimple gets serialized entirely, while only readable fields
    # on InnerSmart are serialized.
    entity = Outter()
    entity.simple = InnerSimple(a=1)
    entity.smart = InnerSmart(a=2, b=3)
    self.assertEqual(
        {'simple': {'a': 1}, 'smart': {'a': 2}},
        entity.to_serializable_dict())

    # Works backwards as well. Note that 'convert_serializable_dict' returns
    # a dictionary that can be fed to entity's 'populate' or constructor. Entity
    # by itself is smart enough to transform subdicts into structured
    # properties.
    self.assertEqual(
        Outter(simple=InnerSimple(a=1), smart=InnerSmart(a=2)),
        Outter.from_serializable_dict({'simple': {'a': 1}, 'smart': {'a': 2}}))

  def _test_repeated_structured_properties_class(self, structured_cls):
    """Common testing for StructuredProperty and LocalStructuredProperty."""
    class Inner(ndb.Model):
      a = ndb.IntegerProperty()

    class Outter(ndb.Model, utils.SerializableModelMixin):
      inner = structured_cls(Inner, repeated=True)

    # Repeated structured property -> list of dicts.
    entity = Outter()
    entity.inner.extend([Inner(a=1), Inner(a=2)])
    self.assertEqual(
        {'inner': [{'a': 1}, {'a': 2}]},
        entity.to_serializable_dict())

    # Reverse also works.
    self.assertEqual(
        entity,
        Outter.from_serializable_dict({'inner': [{'a': 1}, {'a': 2}]}))

  def test_structured_properties(self):
    """Test handling of StructuredProperty."""
    self._test_structured_properties_class(ndb.StructuredProperty)

  def test_local_structured_properties(self):
    """Test handling of LocalStructuredProperty."""
    self._test_structured_properties_class(ndb.LocalStructuredProperty)

  def test_repeated_structured_properties(self):
    """Test handling of StructuredProperty(repeated=True)."""
    self._test_repeated_structured_properties_class(ndb.StructuredProperty)

  def test_repeated_local_structured_properties(self):
    """Test handling of LocalStructuredProperty(repeated=True)."""
    self._test_repeated_structured_properties_class(ndb.LocalStructuredProperty)


class BytesSerializableObject(utils.BytesSerializable):
  def __init__(self, payload):  # pylint: disable=W0231
    self.payload = payload

  def to_bytes(self):
    return 'prefix:' + self.payload

  @classmethod
  def from_bytes(cls, byte_buf):
    return cls(byte_buf[len('prefix:'):])


class BytesSerializableObjectProperty(utils.BytesSerializableProperty):
  _value_type = BytesSerializableObject


class BytesSerializableTest(test_case.TestCase):
  """Test BytesSerializable and its integration with SerializableModel."""

  def test_bytes_serializable(self):
    """Test to_serializable_dict and convert_serializable_dict."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      bytes_prop = BytesSerializableObjectProperty()

    # Ensure to_serializable_dict uses to_bytes.
    self.assertEqual(
        {'bytes_prop': 'prefix:hi'},
        Entity(bytes_prop=BytesSerializableObject('hi')).to_serializable_dict())

    # Ensure convert_serializable_dict uses from_bytes.
    entity = Entity.from_serializable_dict({'bytes_prop': 'prefix:hi'})
    self.assertEqual('hi', entity.bytes_prop.payload)


class JsonSerializableObject(utils.JsonSerializable):
  def __init__(self, payload):  # pylint: disable=W0231
    self.payload = payload

  def to_jsonish(self):
    return {'payload': self.payload}

  @classmethod
  def from_jsonish(cls, obj):
    return cls(obj['payload'])


class JsonSerializableObjectProperty(utils.JsonSerializableProperty):
  _value_type = JsonSerializableObject


class JsonSerializableTest(test_case.TestCase):
  """Test JsonSerializable and its integration with SerializableModel."""

  def test_json_serializable(self):
    """Test to_serializable_dict and convert_serializable_dict."""
    class Entity(ndb.Model, utils.SerializableModelMixin):
      json_prop = JsonSerializableObjectProperty()

    # Ensure to_serializable_dict uses to_jsonish.
    self.assertEqual(
        {'json_prop': {'payload': [1, 2]}},
        Entity(json_prop=JsonSerializableObject([1, 2])).to_serializable_dict())

    # Ensure convert_serializable_dict uses from_jsonish.
    entity = Entity.from_serializable_dict(
        {'json_prop': {'payload': [1, 2]}})
    self.assertEqual([1, 2], entity.json_prop.payload)


if __name__ == '__main__':
  if '-v' in sys.argv:
    unittest.TestCase.maxDiff = None
  unittest.main()