#!/usr/bin/env python3
"""从锁定 JS schema 生成等价 proto3，保留嵌套枚举及原字段编号。"""
import json
from pathlib import Path

task = Path(__file__).resolve().parent
schema = json.loads((task / 'fixtures/client.proto.json').read_text())
definitions = schema['nested']['centrifugal']['nested']['centrifuge']['nested']['protocol']['nested']
lines = ['syntax = "proto3";', 'package centrifugal.centrifuge.protocol;',
         'option java_package = "com.metanet4j.junglebus.proto";', 'option java_outer_classname = "Centrifugal";']

def emit(name, item, depth=0):
    indent = '  ' * depth
    if 'values' in item:
        lines.append(indent + 'enum ' + name + ' {')
        for key, value in item['values'].items():
            lines.append(f'{indent}  {key} = {value};')
    else:
        lines.append(indent + 'message ' + name + ' {')
        for child_name, child in item.get('nested', {}).items():
            emit(child_name, child, depth + 1)
        for key, field in item.get('fields', {}).items():
            kind = 'map<' + field['keyType'] + ', ' + field['type'] + '>' if 'keyType' in field else field['type']
            rule = 'repeated ' if field.get('rule') == 'repeated' else ''
            lines.append(f"{indent}  {rule}{kind} {key} = {field['id']};")
    lines.append(indent + '}')

for name, definition in definitions.items():
    emit(name, definition)
(task / 'metanet4j-junglebus/src/main/protobuf/centrifugal.proto').write_text('\n'.join(lines) + '\n')
