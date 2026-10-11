# D1 登记草案：E1—E11 写入 `unit-coverage-exceptions.json`

> **状态**：**草案，未修改 `unit-coverage-exceptions.json`**。供您批准 D1 后**直接套用**。
> **格式依据**：现有文件的 `schemaVersion`／`decision`／`enforcement`／`modules.<artifactId>.entries[]` 结构，
> 与现有 `BUtils` 条目的字段集（`method`／`line`／`lineMissed`／`methodMissed`／`branchMissed`）。

## 1. 登记机制回顾（文件自述）

> `enforcement`：**`verify-unit.py` 严格模式双向核对**——**实测未覆盖方法集合必须与本清单逐项相等**；
> `jacoco:check` 通过各仓库属性 `jacoco.unit.check.excludes` 排除本清单类名
> （**check 用点号 Java 名，内部类写作 `Outer.Inner`；本文件 `class` 字段用 XML 报告的 `$` 名**）。
>
> `decision`：……**R3 新增 `metanet4j-base` 两处纯分支例外（行覆盖 100%、无未覆盖方法）**……

**⇒ 两点结论**：① **"纯分支例外"机制已存在**（E2—E11 适用）；② **登记后须同步 `pom.xml` 的 `excludes`**。

## 2. 拟新增的 `entries`（追加到 `modules["metanet4j-sdk"].entries`）

```json
[
  {
    "class": "com/metanet4j/sdk/script/ScriptExtend",
    "reason": "私有防实例化构造器（无调用点）——E1（migration-rules §94）",
    "missed": [
      { "method": "<init>", "line": 50, "lineMissed": 2, "methodMissed": 1, "branchMissed": 0 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/bap/BapBase",
    "reason": "分支由编译期常量 DEFAULT_ROOT_PATH 决定，假侧不可达——E2（§86）",
    "missed": [
      { "method": "getKeyBasePath", "line": 156, "lineMissed": 0, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/remote/RemoteOrdTransactionTemplate",
    "reason": "instanceof SigningKeyProvider 恒取 null 侧（实现者均不实现该接口）——E3（§83）",
    "missed": [
      { "method": "resolveKeyProvider", "line": 278, "lineMissed": 0, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/remote/RemoteOrdTransactionBuilder",
    "reason": "signInputs 只在 tx 为 null 时返回 false，对已构造的 builder 该抛错侧不可达——E4（§84）",
    "missed": [
      { "method": "signTx", "line": 81, "lineMissed": 1, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/sigma/Sigma",
    "reason": "toBoxed 的 data==null 守卫：六个调用点全传非 null——E5（§89）",
    "missed": [
      { "method": "toBoxed", "line": 380, "lineMissed": 1, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/remote/RemoteTransactionSigner",
    "reason": "Signature.fromDER 只构造基类，instanceof TransactionSignature 真侧不可达（§91，E6）；satoshisOf 的 null 兜底被更早的类型校验遮蔽（§109，E11）",
    "missed": [
      { "method": "signInputs", "line": 98, "lineMissed": 1, "methodMissed": 0, "branchMissed": 1 },
      { "method": "satoshisOf", "line": 124, "lineMissed": 1, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/transcation/TransactionBuilder",
    "reason": "outputSize 的 lockingScript==null 侧：唯一调用点传硬编码非 null（§99，E7）；sign() 三方向均容忍，catch 不可达（§108，E10）",
    "missed": [
      { "method": "outputSize", "line": 289, "lineMissed": 3, "methodMissed": 0, "branchMissed": 1 },
      { "method": "completeAndSignTx", "line": 227, "lineMissed": 1, "methodMissed": 0, "branchMissed": 0 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/script/ScriptExtend",
    "reason": "pushDataOpCode 的 length>=0 腿：唯一调用点传 sigBytes.length（数组长度恒非负）——E8（§105）",
    "missed": [
      { "method": "pushDataOpCode", "line": 222, "lineMissed": 0, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/PrivateKey",
    "reason": "payload.size()<33 不可达：51/52 字符经 base58 解码去校验和后必 ≥33（数学下界，§107，E9）；版本字节检查经 fromWIF 不可达（§226）",
    "missed": [
      { "method": "fromWIF", "line": 72, "lineMissed": 0, "methodMissed": 0, "branchMissed": 1 },
      { "method": "fromWIF", "line": 75, "lineMissed": 0, "methodMissed": 0, "branchMissed": 1 }
    ]
  },
  {
    "class": "com/metanet4j/sdk/signers/OrdinalsTransactionSigner",
    "reason": "satoshisOf 的 null 兜底被更早的类型校验遮蔽（§109，E11）；批量签名的外层 catch 实测不可达（§93／§272）",
    "missed": [
      { "method": "satoshisOf", "line": 116, "lineMissed": 1, "methodMissed": 0, "branchMissed": 1 },
      { "method": "signInputs", "line": 103, "lineMissed": 1, "methodMissed": 0, "branchMissed": 0 }
    ]
  }
]
```

**注**：`ScriptExtend` 出现两次（E1 与 E8）**应合并为一个 entry**——上表为便于对应 E 编号而分开列出，
落地时**合并为一个 `class` 条目、`missed` 含两项**。

## 3. 登记后须同步的两处

| # | 位置 | 动作 |
| --- | --- | --- |
| 1 | `metanet4j-sdk/pom.xml` 的 `jacoco.unit.check.excludes` | **追加**这些类的**点号名**：`com.metanet4j.sdk.bap.BapBase`、`…remote.RemoteOrdTransactionTemplate`、`…remote.RemoteOrdTransactionBuilder`、`…sigma.Sigma`、`…remote.RemoteTransactionSigner`、`…transcation.TransactionBuilder`、`…script.ScriptExtend`、`…PrivateKey`、`…signers.OrdinalsTransactionSigner` |
| 2 | `feature_list.json` 的 `bsv-r3-keys` | 记录 **D1 已批准并执行**，附实测复核结果（`gaps` 归零的证据） |

## 4. 执行后的验证（我会跑）

1. **`verify-unit.py` 严格模式** —— 实测未覆盖方法集合与清单**逐项相等**；
2. **`mvn -Punit-coverage clean test jacoco:report`** —— 复核行／分支数字与清单一致；
3. **`./init.sh`** —— 任务自检通过；
4. **提交**（sdk 仓 + 任务仓各一次）。

## 5. 边界

- **本文件是草案**，**`unit-coverage-exceptions.json` 与任何 `pom.xml` 均未被修改**。
- **`decision` 字段自述**："按仓库逐类逐方法登记实测不可达或无行为字节码的精确例外：metanet4j-sdk 12 行
  （**2026-09-28 用户批准**）" ——**即该文件的例外一律须经用户批准**；**本草案不构成批准**。
- 落地时**行号以当时的实测报告为准**（若期间有代码改动，需按 §192 的"说明对应关系"更新）。
