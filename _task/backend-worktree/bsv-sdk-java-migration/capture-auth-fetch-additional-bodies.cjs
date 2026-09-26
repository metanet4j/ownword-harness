// 固定 AuthFetch.additional 的 26 个请求体用例：记录方法实际消费的类型与内容。
const fs = require('node:fs')
const path = require('node:path')
const output = process.env.EVIDENCE_INPUTS_PATH
const runId = process.env.EVIDENCE_RUN_ID
if (!output || !runId || process.env.EVIDENCE_SIDE !== 'ts') throw new Error('缺少本轮 TS 采集环境')
const cases = new Map([
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=none for null body", "cc54ff37d4c6d394305520574c622f5d5f7aecb479d3ec9ebff06ac360071b76"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=none for undefined body", "400f7e00a860faecf5b7909176e6ea5950dfbfa2b9938d79410b5f49f1adea51"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=string with correct byteLength", "becb826ae04291f90921836c22c19de32502dd85ae21fbddc704094c6c7708b0"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=number[] for number array", "06a3294d5ceb17fd6d4886f6e946c2d88f76ee1d0a1b1f4d8c6362fc786dac82"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=array for non-number array", "23aba130d22692733cee5749e168296caad312dfccb8cc07395f7e585550f58f"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=ArrayBuffer for ArrayBuffer", "0bb7c9730b3dea96dc947c3217b994f8fdb2ef2851ab3fbe20e7da20ce27adb6"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns typed array name for Uint8Array", "6e5d19551dde267c9c7cb3f609a7a95cd33d42f4de32a8e18b37a54b9dd080f9"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=Blob for Blob", "60cacc89eb1546a8e9c134a5cee7a64e80ad2c80bf3978e46c1865cd07537cc2"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=URLSearchParams for URLSearchParams", "6c12d7e6e1f372f98a8095719db06cc055714ec014b679e5d51bb5fa4cff4417"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=FormData for FormData", "0ec30a0f5d674658592172d25dab826587f0fc57b335c5757ebecd2867538feb"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=object for a plain object", "9e0163c5f5a32ddefcd3296b792c76f3604a5d4d72608c05d8ce3fba50e2058b"],
  ["AuthFetch.describeRequestBodyForLogging (private) returns type=ReadableStream for ReadableStream", "a4ae0d0906091975ef3acfa2d37d72a6dc4501ca050923b77b45bdd6ede61e69"],
  ["AuthFetch.describeRequestBodyForLogging (private) falls back to typeof for an unrecognised type", "ccc068b784817ac417f20ba290c01069ad845741cf5f05b0dfa87d6be65b5bfc"],
  ["AuthFetch.normalizeBodyToNumberArray (private) returns [] for null", "59dd66ffc96ba1fa3c0059cb0d90df934f87f3aa1535c0d9cbd3d8b766e0f375"],
  ["AuthFetch.normalizeBodyToNumberArray (private) returns [] for undefined", "728473fb8607b2c892796a9e6849f6805ed57d119ee3bcfd12a8b312b6211df9"],
  ["AuthFetch.normalizeBodyToNumberArray (private) converts a string to a number array", "a678ff7816b9a6a4fd03baf52ebd35fd21e2f77d826a4c1ee9ac932ec4475be4"],
  ["AuthFetch.normalizeBodyToNumberArray (private) preserves a number[] as binary bytes", "c49482b9069a927080a45ef1902e2b5309a6befa2eaa44f54b4af030ca83abcc"],
  ["AuthFetch.normalizeBodyToNumberArray (private) preserves ArrayBuffer bytes", "ceebf8e4ed30c3174a65d77a5420307d91de6420f13ffdeb80cd9ae95e169620"],
  ["AuthFetch.normalizeBodyToNumberArray (private) preserves the selected Uint8Array view bytes", "d4d3df75a4057dec8a50ecd516f97a3e08020d39dea051d6eb38b89727a77ba7"],
  ["AuthFetch.normalizeBodyToNumberArray (private) preserves Blob bytes", "5e1536f61392d8daf99b2293d6297ba224cab9a46ce2e574f8841d0fd3dfcf70"],
  ["AuthFetch.normalizeBodyToNumberArray (private) normalizes FormData as URL-encoded bytes", "c5b064ea4c60d5d6e03477cccace391acdc1f66e74aa41493a2cec535cd012ce"],
  ["AuthFetch.normalizeBodyToNumberArray (private) normalizes FormData file entries by filename", "97e7274b8d7a10b46a861b06a1866425a97fa68604a58ce0d73247e94c5fb479"],
  ["AuthFetch.normalizeBodyToNumberArray (private) normalizes URLSearchParams bytes", "f91b141ce19d24acf91a7444caf18cfa4229545d26a7aff150919b0d41cff99c"],
  ["AuthFetch.normalizeBodyToNumberArray (private) rejects ReadableStream bodies that cannot be replayed", "4d45a5b04199890b79c9432c8fa6eba4ac4c377e904fa307ee622ff184afb44c"],
  ["AuthFetch.normalizeBodyToNumberArray (private) converts a plain object via JSON.stringify", "ae16d3c9eca2647b9980acf65a1f4b079fbc5cfa559c0fd6c57af21a099508f8"],
  ["AuthFetch.normalizeBodyToNumberArray (private) preserves nested wallet bytes in authenticated JSON request bodies", "ecafca9b9b19d6a6532ce357de24df9d883e367630edfc3520307777ad582238"]
])

function record(caseId, method, body) {
  fs.appendFileSync(output, JSON.stringify({ runId, side: 'ts', caseId, sampleId: 'body-0',
    value: { kind: 'AuthFetch.bodyInput', method, body } }) + '\n')
}
function plain(value) {
  if (ArrayBuffer.isView(value)) return Array.from(new Uint8Array(value.buffer, value.byteOffset, value.byteLength))
  if (Array.isArray(value)) return value.map(plain)
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, plain(v)]))
  return value
}
function snapshot(body, method) {
  if (body === null) return { type: 'null' }
  if (body === undefined) return { type: 'undefined' }
  if (typeof body === 'string') return { type: 'string', value: body }
  if (Array.isArray(body)) return { type: body.every(x => typeof x === 'number') ? 'number[]' : 'array', value: plain(body) }
  if (body instanceof ArrayBuffer) return { type: 'ArrayBuffer', bytesHex: Buffer.from(body).toString('hex') }
  if (ArrayBuffer.isView(body)) return { type: body.constructor.name,
    bytesHex: Buffer.from(body.buffer, body.byteOffset, body.byteLength).toString('hex') }
  if (body instanceof Blob) return method === 'normalizeBodyToNumberArray'
    ? body.arrayBuffer().then(bytes => ({ type: 'Blob', bytesHex: Buffer.from(bytes).toString('hex') }))
    : { type: 'Blob', size: body.size }
  if (body instanceof FormData) return { type: 'FormData', entries: Array.from(body.entries())
    .map(([key, value]) => [key, typeof value === 'string' ? value : value.name]) }
  if (body instanceof URLSearchParams) return { type: 'URLSearchParams', serialized: body.toString() }
  if (body instanceof ReadableStream) return { type: 'ReadableStream' }
  if (typeof body === 'symbol') return { type: 'symbol' }
  return { type: 'object', value: plain(body) }
}
const modulePath = path.resolve(__dirname, '../../../reference/ts-stack/packages/sdk/src/auth/clients/AuthFetch.ts')
jest.doMock(modulePath, () => {
  const actual = jest.requireActual(modulePath)
  const Fetch = actual.AuthFetch
  const describe = Fetch.prototype.describeRequestBodyForLogging
  const normalize = Fetch.prototype.normalizeBodyToNumberArray
  Fetch.prototype.describeRequestBodyForLogging = function (body) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'describeRequestBodyForLogging', snapshot(body, 'describeRequestBodyForLogging'))
    return Reflect.apply(describe, this, [body])
  }
  Fetch.prototype.normalizeBodyToNumberArray = async function (body) {
    const caseId = cases.get(expect.getState().currentTestName)
    if (caseId) record(caseId, 'normalizeBodyToNumberArray', await snapshot(body, 'normalizeBodyToNumberArray'))
    return Reflect.apply(normalize, this, [body])
  }
  return actual
})
