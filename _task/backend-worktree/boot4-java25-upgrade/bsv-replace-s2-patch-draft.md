# 批量签名结果语义

用户已授权实施，修复已提交：本地批量签名器与远程签名器统一采用下列语义。

- `null` 交易返回 `false`。
- 零输入无需签名，返回 `true`。
- 有输入但全部跳过，返回 `false`。
- 部分输入成功签名，返回 `true`；整笔交易的有效性由脚本验证决定。

远程构建器在没有任何输入完成签名回填时抛出 `SignErrorException`。本地与远程失败、部分成功及真实脚本验证均有回归测试。

当前规则与逐方法执行依据见 `bsv-replace-test-map.json`、`unit-test-inventory.json` 和 `feature_list.json`；不保留另一个待批准方案。
