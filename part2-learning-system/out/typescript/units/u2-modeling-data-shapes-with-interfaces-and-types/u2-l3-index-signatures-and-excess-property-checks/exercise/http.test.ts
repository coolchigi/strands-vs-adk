import test from 'node:test';
import assert from 'node:assert/strict';
import type { HttpHeaders, RequestOptions } from './http.ts';
import { buildHeaders, sendWithIntermediate, createRequest } from './http.ts';

test('HttpHeaders allows arbitrary string keys with consistent types', () => {
  const headers: HttpHeaders = {
    contentType: 'application/json',
    'Authorization': 'Bearer 123',
    'X-Custom-Trace': 'trace-abc',
  };
  assert.equal(headers.contentType, 'application/json', 'contentType should be preserved');
  assert.equal(headers['Authorization'], 'Bearer 123', 'dynamic Authorization header should match');
});

test('buildHeaders merges default contentType with provided custom headers', () => {
  const headers = buildHeaders({ 'X-Client-Id': 'client-99' });
  assert.equal(headers.contentType, 'application/json', 'default contentType should be application/json');
  assert.equal(headers['X-Client-Id'], 'client-99', 'custom header should be present');
});

test('RequestOptions allows extra properties via index signature', () => {
  const options: RequestOptions = {
    url: 'https://example.com/api',
    method: 'POST',
    extraLoggingFlag: true,
    metaCount: 42,
  };
  assert.equal(options.url, 'https://example.com/api', 'url should match');
  assert.equal(options['extraLoggingFlag'], true, 'extraLoggingFlag should be accepted by index signature');
});

test('sendWithIntermediate bypasses excess property checks via intermediate variable', () => {
  const result = sendWithIntermediate({ url: 'https://example.com/api', debugToken: 'secret' });
  assert.deepEqual(result, { url: 'https://example.com/api', method: 'GET' }, 'should return created request details');
});
