# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: faro/proto/geometry.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x19\x66\x61ro/proto/geometry.proto\";\n\x04Rect\x12\t\n\x01x\x18\x01 \x01(\x02\x12\t\n\x01y\x18\x02 \x01(\x02\x12\r\n\x05width\x18\x03 \x01(\x02\x12\x0e\n\x06height\x18\x04 \x01(\x02\"\x1f\n\x07Point2D\x12\t\n\x01x\x18\x01 \x01(\x02\x12\t\n\x01y\x18\x02 \x01(\x02\"\x1a\n\x06Vector\x12\x10\n\x04\x64\x61ta\x18\x01 \x03(\x02\x42\x02\x10\x01\"\x1f\n\x06Matrix\x12\x15\n\x04rows\x18\x01 \x03(\x0b\x32\x07.VectorB\r\xaa\x02\nFaro.Protob\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'faro.proto.geometry_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\252\002\nFaro.Proto'
  _globals['_VECTOR'].fields_by_name['data']._loaded_options = None
  _globals['_VECTOR'].fields_by_name['data']._serialized_options = b'\020\001'
  _globals['_RECT']._serialized_start=29
  _globals['_RECT']._serialized_end=88
  _globals['_POINT2D']._serialized_start=90
  _globals['_POINT2D']._serialized_end=121
  _globals['_VECTOR']._serialized_start=123
  _globals['_VECTOR']._serialized_end=149
  _globals['_MATRIX']._serialized_start=151
  _globals['_MATRIX']._serialized_end=182
# @@protoc_insertion_point(module_scope)
