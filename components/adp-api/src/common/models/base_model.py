"""
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
FireO BaseModel to be inherited by all other objects in ORM
"""

import fireo
from fireo.models import Model


# pylint: disable = too-few-public-methods
class BaseModel(Model):
  """BaseModel to add common helper methods to all FireO objects

    An interface, intended to be subclassed.

    """
  class Meta:
    # TODO: uncomment when bug is fixed
    # ignore_none_field seems not to inherit
    # will need to set on all end Models
    # https://github.com/octabytes/FireO/issues/106
    # ignore_none_field = False
    # commenting until it does something
    abstract = True

  @classmethod
  def find_by_id(cls, doc_id):
    """Looks up in the Database and returns an object of this type by id
       (not key)

        An interface, intended to be subclassed.

        Args:
            doc_id (string): the document id without collection_name
            (i.e. not the key)

        Returns:
            [any]: an instance of object returned by the database, type is
            the subclassed Model
        """
    key = fireo.utils.utils.generateKeyFromId(cls, doc_id)
    return cls.collection.get(key)

  @classmethod
  def delete_by_id(cls, doc_id):
    """Deletes from the Database the object of this type by id (not key)

        Args:
            doc_id (string): the document id without collection_name
            (i.e. not the key)

        Returns:
            None
        """
    key = fireo.utils.utils.generateKeyFromId(cls, doc_id)
    return cls.collection.delete(key)
