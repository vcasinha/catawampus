#!/usr/bin/python
# Copyright 2011 Google Inc. All Rights Reserved.
#
"""Base classes for TR-069 model objects.

The standard subclasses of these objects are auto-generated from the
tr-*.xml schema files and named tr???_*.py in this directory.  You can
also define nonstandard data models by extending those classes or
Exporter yourself.
"""

__author__ = 'apenwarr@google.com (Avery Pennarun)'


_lastindex = -1


class NotAddableError(KeyError):
    pass


class SchemaError(Exception):
    pass


class AutoDict(object):
  def __init__(self, name, iteritems=None,
               getitem=None, setitem=None, delitem=None):
    self.__name = name
    self.__iteritems = iteritems or self._Bad('iteritems')
    self.__getitem = getitem or self._Bad('getitem')
    self.__setitem = setitem or self._Bad('setitem')
    self.__delitem = delitem or self._Bad('delitem')

  def _Bad(self, funcname):
    def Fn(*args, **kwargs):
      raise NotImplementedError('%r must override %s'
                                % (self.__name, funcname))
    return Fn

  def iteritems(self):
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

  def iterkeys(self):
    for k,v in self.iteritems():
      yield k

  def itervalues(self):
    for k,v in self.iteritems():
      yield v

  def __iter__(self):
    return self.iterkeys()

  def __len__(self):
    count = 0
    for i in self:
      count += 1
    return count

  def keys(self):
    return list(self.iterkeys())

  def values(self):
    return list(self.itervalues())

  def items(self):
    return list(self.iteritems())


class Exporter(object):
  """An object containing named parameters that can be get/set.

  It can also contain sub-objects with their own parameters, and attributes
  that represent lists of sub-objects.
  """

  def __init__(self, defaults=None):
    self.export_params = set()
    self.export_objects = set()
    self.export_object_lists = set()
    if defaults:
        for key,value in defaults.iteritems():
            setattr(self, key, value)

  def Export(self, params=None, objects=None, lists=None):
    if params:
        self.export_params.update(params)
    if objects:
        self.export_objects.update(objects)
    if lists:
        self.export_object_lists.update(lists)

  def ValidateExports(self, path=None):
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
            for iname,obj in l.iteritems():
                pass
        except TypeError:
            raise Exc(name + 'List', 'is an objlist but failed to iteritems')
        for iname,obj in l.iteritems():
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
      o = self
      assert(not name.endswith('.'))
      for i in name.split('.'):
          if hasattr(o, '_GetExport'):
              o = o._GetExport(i)
          else:
              o = o[i]
      return o

  def SetExportParam(self, name, value):
    if name not in self.export_params:
        raise KeyError(name)
    setattr(self, name, value)

  def AddExportObject(self, name, idx=None):
    objlist = self._GetExport(name)
    if name not in self.export_object_lists:
        raise KeyError(name)
    try:
        constructor = getattr(self, name)
    except KeyError:
        raise NotAddableError(name)
    if idx is None:
        global _lastindex
        _lastindex += 1
        while _lastindex in objlist:
            _lastindex += 1
        idx = _lastindex
    idx = str(idx)
    assert '.' not in idx
    newobj = constructor()
    objlist[idx] = newobj
    return idx,newobj

  def DeleteExportObject(self, name, idx):
    idx = str(idx)
    objlist = self._GetExport(name)
    if idx not in objlist:
        raise KeyError((name,idx))
    del objlist[idx]

  def _ListExports(self, recursive=False):
    for name in self.export_params:
        yield name
    for name in self.export_objects:
        yield name + '.'
        if recursive:
            obj = self._GetExport(name)
            for i in obj._ListExports(recursive):
                yield name + '.' + i
    for name in self.export_object_lists:
        yield name + '.'
        if recursive:
            objlist = self._GetExport(name)
            for idx,obj in objlist.iteritems():
                if obj is not None:
                    for i in obj._ListExports(recursive):
                        yield '%s.%s.%s' % (name, idx, i)

  def ListExports(self, recursive=False):
    if recursive:
        self.ValidateExports()
    return list(sorted(self._ListExports(recursive=recursive)))


class TODO(Exporter):
    def __init__(self):
        Exporter.__init__(self)
        self.Export(params=['TODO'])
        self.TODO = 'CLASS NOT IMPLEMENTED YET'


def Dump(root):
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
    out = []
    if isinstance(root, type):
        root = root()
    _DumpSchema(root, out, [root.__class__.__name__])
    return '\n'.join(sorted(out))
