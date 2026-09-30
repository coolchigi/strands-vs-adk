export interface SimpleRequestOptions {
  url: string;
  method?: string;
}

// TODO: Define HttpHeaders with contentType?: string and a string index signature returning string | undefined
export interface HttpHeaders {
  contentType?: string;
}

// TODO: Define RequestOptions with url: string, method?: string, headers?: HttpHeaders, and a string index signature returning unknown
export interface RequestOptions {
  url: string;
  method?: string;
  headers?: HttpHeaders;
}

export function createRequest(options: SimpleRequestOptions): { url: string; method: string } {
  return {
    url: options.url,
    method: options.method ?? 'GET',
  };
}

// TODO: Merge { contentType: 'application/json' } with customHeaders and return HttpHeaders
export function buildHeaders(customHeaders: Record<string, string>): HttpHeaders {
  return customHeaders as unknown as HttpHeaders;
}

// TODO: Accept options with url and debugToken, store in an intermediate variable, pass to createRequest, and return the result
export function sendWithIntermediate(options: { url: string; debugToken: string }): { url: string; method: string } {
  return { url: '', method: '' };
}
