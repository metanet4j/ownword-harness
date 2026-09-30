// 固定原测试的熵输入，保留 SDK 的 Random、PrivateKey 与签名算法执行路径。
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
