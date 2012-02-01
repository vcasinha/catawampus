#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# unittest requires method names starting in 'test'
#pylint: disable-msg=C6409

"""Unit tests for dm_root.py."""

__author__ = 'dgentry@google.com (Denton Gentry)'

import unittest
import _fix_path  #pylint: disable-msg=W0611
import dm_root
import tr.tr098_v1_2
import tr.tr181_v2_2


BASE181 = tr.tr181_v2_2.Device_v2_2.Device


class MockTr181(BASE181):
  pass


BASE98 = tr.tr098_v1_2.InternetGatewayDevice_v1_4.InternetGatewayDevice


class MockTr98(BASE98):
  pass


class MockManagement(object):
  def __init__(self):
    self.EnableCWMP = False


class DeviceModelRootTest(unittest.TestCase):
  def testAddManagementServer(self):
    root = dm_root.DeviceModelRoot(loop=None, platform=None)
    mgmt = MockManagement()
    root.add_management_server(mgmt)  # should do nothing.

    root.Device = MockTr181()
    root.InternetGatewayDevice = MockTr98()
    root.Export(objects=['Device', 'InternetGatewayDevice'])
    self.assertFalse(isinstance(root.InternetGatewayDevice.ManagementServer,
                                BASE98.ManagementServer))
    self.assertFalse(isinstance(root.Device.ManagementServer,
                                BASE181.ManagementServer))
    root.add_management_server(mgmt)  # should do nothing.
    self.assertTrue(isinstance(root.InternetGatewayDevice.ManagementServer,
                               BASE98.ManagementServer))
    self.assertTrue(isinstance(root.Device.ManagementServer,
                               BASE181.ManagementServer))


if __name__ == '__main__':
  unittest.main()
