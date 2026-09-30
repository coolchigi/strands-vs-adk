export interface SimpleRequestOptions {
  url: string;
  method?: string;
}

export interface HttpHeaders {
  contentType?: string;
  [headerName: string]: string | undefined;
}

export interface RequestOptions {
  url: string;
  method?: string;
  headers?: HttpHeaders;
  [extra: string]: unknown;
}

export function createRequest(options: SimpleRequestOptions): { url: string; method: string } {
  return {
    url: options.url,
    method: options.method ?? 'GET',
  };
}

export function buildHeaders(customHeaders: Record<string, string>): HttpHeaders {
  return {
    contentType: 'application/json',
    ...customHeaders,
  };
}

export function sendWithIntermediate(options: { url: string; debugToken: string }): { url: string; method: string } {
  const req = options;
  return createRequest(req);
}
