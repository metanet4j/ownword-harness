// 固定 validationHelpers.test.ts：在公开导出入口记录 Jest 真正传入的参数。
const fs = require('node:fs')
const path = require('node:path')

const output = process.env.MIGRATION_VALIDATION_TS_INPUTS
if (!output) throw new Error('缺少 ValidationHelpers 输入采集路径')
const file = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/wallet/validationHelpers.ts')
const source = 'src/wallet/__tests/validationHelpers.test.ts'
const names = new Set([
  'parseWalletOutpoint', 'validateSatoshis', 'validateOptionalInteger', 'validateInteger',
  'validatePositiveIntegerOrZero', 'validateStringLength', 'validateBase64String', 'isHexString',
  'validateCreateActionInput', 'validateCreateActionOutput', 'validateCreateActionOptions',
  'validateCreateActionArgs', 'validateSignActionOptions', 'validateSignActionArgs',
  'validateAbortActionArgs', 'validateWalletPayment', 'validateBasketInsertion',
  'validateInternalizeOutput', 'validateOriginator', 'validateOptionalOutpointString',
  'validateOutpointString', 'validateRelinquishOutputArgs', 'validateRelinquishCertificateArgs',
  'validateListCertificatesArgs', 'validateAcquireIssuanceCertificateArgs',
  'validateAcquireDirectCertificateArgs', 'validateProveCertificateArgs',
  'validateDiscoverByIdentityKeyArgs', 'validateDiscoverByAttributesArgs',
  'validateListOutputsArgs', 'validateListActionsArgs'
])

function tagged(value) {
  if (value === undefined) return { type: 'undefined' }
  if (value === null) return { type: 'null' }
  if (typeof value === 'boolean') return { type: 'boolean', value }
  if (typeof value === 'string') return { type: 'string', value }
  if (typeof value === 'number') return { type: 'number', value: String(value) }
  if (Array.isArray(value)) return { type: 'array', value: value.map(tagged) }
  if (typeof value === 'object') return { type: 'map', value: Object.fromEntries(Object.entries(value).map(([key, item]) => [key, tagged(item)])) }
  throw new Error('ValidationHelpers 出现未支持的输入类型：' + typeof value)
}

jest.doMock(file, () => {
  const actual = jest.requireActual(file)
  const wrapped = { ...actual }
  for (const name of names) {
    if (typeof actual[name] !== 'function') throw new Error('固定导出不存在：' + name)
    wrapped[name] = (...args) => {
      const test = expect.getState().currentTestName
      const location = new Error().stack.match(/validationHelpers\.test\.ts:(\d+):\d+/)
      if (!test || !location) throw new Error('ValidationHelpers 原测试调用位置缺失：' + name)
      fs.appendFileSync(output, JSON.stringify({ test, source, line: Number(location[1]), method: name,
        args: args.map(tagged) }) + '\n')
      return Reflect.apply(actual[name], actual, args)
    }
  }
  return wrapped
})

beforeEach(() => {
  if (expect.getState().currentTestName === 'specOpThrowReviewActions is a non-empty string constant') {
    fs.appendFileSync(output, JSON.stringify({
      test: expect.getState().currentTestName, source, line: 1242,
      method: 'specOpThrowReviewActions', args: [],
      constantValue: tagged(jest.requireActual(file).specOpThrowReviewActions)
    }) + '\n')
  }
})
