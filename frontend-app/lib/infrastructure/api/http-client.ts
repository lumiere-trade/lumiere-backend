/**
 * Base HTTP Client.
 * Pure HTTP operations, NO business logic, NO side effects.
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { API_CONFIG } from '@/config/constants';
import {
  ApiError,
  NetworkError,
  ServerError,
  ValidationError,
} from '@/lib/domain/errors/api.errors';

export interface HttpClientConfig {
  baseURL?: string;
  timeout?: number;
  onUnauthorized?: () => void;
}

export class HttpClient {
  private client: AxiosInstance;
  private onUnauthorized?: () => void;

  constructor(config: HttpClientConfig = {}) {
    this.onUnauthorized = config.onUnauthorized;

    this.client = axios.create({
      baseURL: config.baseURL || API_CONFIG.BASE_URL,
      timeout: config.timeout || API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401 && this.onUnauthorized) {
          this.onUnauthorized();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): ApiError {
    if (!error.response) {
      return new NetworkError('Network error occurred');
    }

    const { status, data } = error.response;
    const message = (data as any)?.detail || error.message;

    if (status >= 500) {
      return new ServerError(message, status);
    }

    if (status === 400) {
      const field = (data as any)?.field;
      return new ValidationError(message, field);
    }

    return new ApiError(message, status);
  }

  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}
