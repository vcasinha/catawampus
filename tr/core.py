#!/usr/bin/python
# Copyright 2011 Google Inc. All Rights Reserved.
#
# TR-069 has mandatory attribute names that don't comply with policy
#pylint: disable-msg=C6409
#
"""Base classes for TR-069 model objects.

The standard subclasses of these objects are auto-generated from the
tr-*.xml schema files and named tr???_*.py in this directory.  You can
also define nonstandard data models by extending those classes or
Exporter yourself.
"""

__author__ = 'apenwarr@google.com (Avery Pennarun)'


class NotAddableError(KeyError):
  """Raised when AddObject is not allowed on an object list."""
  pass


class SchemaError(Exception):
  """Raised when an object claims to implement a schema but doesn't."""
  pass


class AutoDict(object):
  """Class for simulating a dict that has dynamically-generated content.

  For example, a dict with a list of files in a given directory would be
  iterable (returning a list of filenames and objects corresponding to the
  filenames) and indexable (return an object given a filename) but there is
  no reason to actually cache the list of filenames; the kernel already has
  that list in real time.  So we provide a dict-like interface, and you
  can implement iteritems, getitem, setitem, etc separately.

  Use this class by either deriving from it or by just passing your own
  iteritems, getitems, etc to the constructor.  The choice depends on how
  you want to do your namespacing.
  """

  def __init__(self, name, iteritems=None,
               getitem=None, setitem=None, delitem=None):
    self.__name = name
    self.__iteritems = iteritems or self._Bad('iteritems')
    self.__getitem = getitem or self._Bad('getitem')
    self.__setitem = setitem or self._Bad('setitem')
    self.__delitem = delitem or self._Bad('delitem')

  def _Bad(self, funcname):

    #pylint: disable-msg=W0613
    def Fn(*args, **kwargs):
      raise NotImplementedError('%r must override %s'
                                % (self.__name, funcname))
    return Fn

  def iteritems(self):  #pylint: disable-msg=C6409
    return self.__iteritems()

  def __getitem__(self, key):
    return self.__getitem(key)

  def __setitem__(self, key, value):
    return self.__setitem(key)

  def __delitem__(self, key):
    return self.__delitem(key)

  def __contains__(self, key):
    try:
      self[key]
    except KeyError:
      return False
    return True

  def iterkeys(self):  #pylint: disable-msg=C6409
    for (k, v) in self.iteritems():  #pylint: disable-msg=W0612
      yield k

  def itervalues(self):  #pylint: disable-msg=C6409
    for (k, v) in self.iteritems():  #pylint: disable-msg=W0612
      yield v

  def __iter__(self):
    return self.iterkeys()

  def __len__(self):
    count = 0
    for i in self:  #pylint: disable-msg=W0612
      count += 1
    return count

  def keys(self):  #pylint: disable-msg=C6409
    return list(self.iterkeys())

  def values(self):  #pylint: disable-msg=C6409
    return list(self.itervalues())

  def items(self):  #pylint: disable-msg=C6409
    return list(self.iteritems())


class Exporter(object):
  """An object containing named parameters that can be get/set.

  It can also contain sub-objects with their own parameters, and attributes
  that represent lists of sub-objects.
  """

  def __init__(self, defaults=None):
    """Initialize an Exporter.

    Args:
      defaults: (optional) a dictionary of attrs to set on the object.
    """
    self.__lastindex = -1
    self.export_params = set()
    self.export_objects = set()
    self.export_object_lists = set()
    if defaults:
      for (key, value) in defaults.iteritems():
        setattr(self, key, value)

  def Export(self, params=None, objects=None, lists=None):
    """Export some parameters, objects, or lists to make them visible.

    Once you export these, you still have to manually declare attributes
    named after the exported names.  The idea is that mostly auto-generated
    classes will call Export(), but manually-written subclasses will declare
    the actual attributes.  If you forget to declare an attribute (or you
    make a typo) then ValidateExports will fail.

    Args:
      params: a list of parameters in this object.
      objects: a list of sub-objects in this object.
      lists: a list of object-list names (lists containing objects) in this
        object.
    """
    if params:
      self.export_params.update(params)
    if objects:
      self.export_objects.update(objects)
    if lists:
      self.export_object_lists.update(lists)

  def ValidateExports(self, path=None):
    """Trace through this object's exports to make no attributes are missing.

    Also goes through child objects.

    Args:
      path: (optional) a list of object name elements for use when printing
        errors, so it's easier to see which one caused the problem.

    Raises:
      SchemaError: if schema validation fails.
    """
    if not path:
      path = ['root']

    def Exc(name, msg):
      fullname = '.'.join(path + [name])
      return SchemaError('%s%s %s' % (fullname, name, msg))

    for name in self.export_params:
      self.AssertValidExport(name, path=path)
      self._GetExport(name)
    for name in self.export_objects:
      self.AssertValidExport(name, path=path)
      obj = self._GetExport(name)
      if isinstance(obj, type):
        raise Exc(name, 'is a type; instantiate it')
      try:
        obj.Export()
      except AttributeError:
        raise Exc(name, 'is %r, must implement core.Exporter'
                  % type(obj))
      obj.ValidateExports(path+[name])
    for name in self.export_object_lists:
      self.AssertValidExport(name, path=path)
      l = self._GetExport(name)
      try:
        for (iname, obj) in l.iteritems():  #pylint: disable-msg=W0612
          pass
      except TypeError:
        raise Exc(name + 'List', 'is an objlist but failed to iteritems')
      for (iname, obj) in l.iteritems():
        if isinstance(obj, type):
          raise Exc('%s.%s' % (name, iname),
                    'is a type; instantiate it')
        try:
          obj.Export()
        except AttributeError:
          raise Exc(name, 'is %r, must implement core.Exporter'
                    % type(obj))
        obj.ValidateExports()

  def AssertValidExport(self, name, path=None):
    if (name not in self.export_params and
        name not in self.export_objects and
        name not in self.export_object_lists):
      raise KeyError(name)
    ename = self._GetExportName(name)
    if not hasattr(self, ename):
      if not path:
        path = ['root']
      fullname = '.'.join(path + [ename])
      raise SchemaError('%s is exported but does not exist' % fullname)

  def _GetExportName(self, name):
    if name in self.export_object_lists:
      return name + 'List'
    else:
      return name

  def _GetExport(self, name):
    return getattr(self, self._GetExportName(name))

  def GetExport(self, name):
    """Get a child of this object (a parameter or object).

    Args:
      name: a dot-separated sub-object name to retrieve.
    Returns:
      An Exporter instance or a parameter value.
    """
    o = self
    assert not name.endswith('.')
    for i in name.split('.'):
      if hasattr(o, '_GetExport'):
        o = o._GetExport(i)  #pylint: disable-msg=W0212
      else:
        o = o[i]
    return o

  def SetExportParam(self, name, value):
    """Set the value of a parameter of this object.

    Args:
      name: the parameter name to set (parameters only, not objects or lists).
      value: the value to set it to.
    Raises:
      KeyError: if the name is not an exported parameter.
    """
    if name not in self.export_params:
      raise KeyError(name)
    setattr(self, name, value)

  def AddExportObject(self, name, idx=None):
    """Create a new object of type 'name' in the list self.'name'List.

    Args:
      name: the name of the object class.  The list name is self.(name+'List').
      idx: the dictionary key to store it under.  Default is auto-generated.
    Returns:
      An tuple of (idx, obj), where idx is the key and obj is the new object.
    Raises:
      KeyError: if 'name' is not an exported sub-object type.
    """
    objlist = self._GetExport(name)
    if name not in self.export_object_lists:
      raise KeyError(name)
    try:
      constructor = getattr(self, name)
    except KeyError:
      raise NotAddableError(name)
    if idx is None:
      self.__lastindex += 1
      while self.__lastindex in objlist:
        self.__lastindex += 1
      idx = self.__lastindex
    idx = str(idx)
    assert '.' not in idx
    newobj = constructor()
    objlist[idx] = newobj
    return idx, newobj

  def DeleteExportObject(self, name, idx):
    """Delete the object with index idx in the list named name.

    Args:
      name: the sub-object list to delete from.
      idx: the index of the objet to delete.
    Raises:
      KeyError: if the given index is not in the dictionary.
    """
    idx = str(idx)
    objlist = self._GetExport(name)
    if idx not in objlist:
      raise KeyError((name, idx))
    del objlist[idx]

  def _ListExports(self, recursive=False):
    for name in self.export_params:
      yield name
    for name in self.export_objects:
      yield name + '.'
      if recursive:
        obj = self._GetExport(name)
        for i in obj._ListExports(recursive):  #pylint: disable-msg=W0212
          yield name + '.' + i
    for name in self.export_object_lists:
      yield name + '.'
      if recursive:
        objlist = self._GetExport(name)
        for (idx, obj) in objlist.iteritems():
          if obj is not None:
            for i in obj._ListExports(recursive):  #pylint: disable-msg=W0212
              yield '%s.%s.%s' % (name, idx, i)

  def ListExports(self, recursive=False):
    """Return a sorted list of sub-objects and parameters.

    Args:
      recursive: true if you want to include children of children.
    Returns:
      An iterable of strings that can be passed to GetExport().
    """
    # TODO(apenwarr): do sorting incrementally on each _ListExports.
    #   Sorting at the toplevel requires us to load the whole list into
    #   memory at once, which would otherwise be unnecessary.
    if recursive:
      self.ValidateExports()
    return sorted(self._ListExports(recursive=recursive))


class TODO(Exporter):
  """Use this class to fake out an Exporter instance.

  Useful when you're implementing a big TR-069 Model hierarchy and you don't
  want to implement every single class right now.  As a bonus, it'll show up
  when you grep for TODO in the source code.
  """

  def __init__(self):
    Exporter.__init__(self)
    self.Export(params=['TODO'])
    self.TODO = 'CLASS NOT IMPLEMENTED YET'


def Dump(root):
  """Return a string representing the contents of an object.

  This function works only if root.ValidateExports() would pass.

  Args:
    root: the object to dump.
  Returns:
    A big string containing lines of the format:
      Object.SubObject.
      Object.SubObject.ParameterName = %r
  """
  out = []
  for i in root.ListExports(recursive=True):
    if i.endswith('.'):
      out.append('  %s' % (i,))
    else:
      out.append('  %s = %r' % (i, root.GetExport(i)))
  return '\n'.join(out)


def _DumpSchema(root, out, path):
  if isinstance(root, type):
    root = root()
  for i in root.export_params:
    out.append('.'.join(path + [i]))
  for i in root.export_objects:
    out.append('.'.join(path + [i, '']))
    _DumpSchema(getattr(root, i), out, path + [i])
  for i in root.export_object_lists:
    out.append('.'.join(path + [i, '']))
    out.append('.'.join(path + [i, '{i}']))
    _DumpSchema(getattr(root, i), out, path + [i, '{i}'])


def DumpSchema(root):
  """Return a string representing the object model implemented by the object.

  You can use this to show which objects, sub-objects, and parameters *should*
  be implemented by an object, even if that object isn't fully implemented
  yet by adding the right attrs in a subclass.  This is useful for figuring
  out which attrs you *need* to add in a subclass.  Auto-generated tr*.py
  files run this automatically when you execute them from the command line.

  This function works even if root.ValidateExports() would fail.

  Args:
    root: the object or type to dump.  If a type, instantiates it.
  Returns:
    A big string of the format:
      Object.SubObject.
      Object.SubObject.ParameterName
  """
  out = []
  if isinstance(root, type):
    root = root()
  _DumpSchema(root, out, [root.__class__.__name__])
  return '\n'.join(sorted(out))