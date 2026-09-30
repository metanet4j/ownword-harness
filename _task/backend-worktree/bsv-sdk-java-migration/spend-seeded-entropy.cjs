// 固定原测试的熵输入，保留 SDK 的 Random、PrivateKey 与签名算法执行路径。
// Spend.additional.test.ts 的 checkSignatureEncoding / CHECKSIGVERIFY 用例用
// PrivateKey.fromRandom() 生成密钥，未固定熵时每次采集都会得到不同入口实参，
// 冻结计划因此不可重放；这里与 verifier-seeded-entropy.cjs 用同一口径固定熵。
const source = globalThis.crypto
const deterministic = Object.create(source)
Object.defineProperty(deterministic, 'getRandomValues', {
  value (array) {
    array.fill(0)
    array[array.length - 1] = 1
    return array
  }
})
Object.defineProperty(globalThis, 'crypto', { configurable: true, value: deterministic })
