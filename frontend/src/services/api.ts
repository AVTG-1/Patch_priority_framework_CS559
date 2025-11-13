import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
  SystemConfig,
  SystemConfigCreate,
  SystemConfigUpdate,
  VulnerabilityQueryParams,
  VulnerabilityQueryResult,
  CommunityVulnerability,
  CommunityVulnerabilityCreate,
  SimulationRun,
  SimulationRunCreate,
  SimulationSummary,
  UserListResponse,
  AdminStatsResponse,
  APIError,
} from '../types';

// Create Axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIError>) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await api.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Store token and user data
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  },

  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

// System Configuration API
export const systemsAPI = {
  getSystems: async (): Promise<SystemConfig[]> => {
    const response = await api.get<SystemConfig[]>('/systems');
    return response.data;
  },

  getSystem: async (systemId: number): Promise<SystemConfig> => {
    const response = await api.get<SystemConfig>(`/systems/${systemId}`);
    return response.data;
  },

  createSystem: async (systemData: SystemConfigCreate): Promise<SystemConfig> => {
    const response = await api.post<SystemConfig>('/systems', systemData);
    return response.data;
  },

  updateSystem: async (
    systemId: number,
    systemData: SystemConfigUpdate
  ): Promise<SystemConfig> => {
    const response = await api.put<SystemConfig>(`/systems/${systemId}`, systemData);
    return response.data;
  },

  deleteSystem: async (systemId: number): Promise<void> => {
    await api.delete(`/systems/${systemId}`);
  },
};

// Vulnerability Query API
export const vulnerabilitiesAPI = {
  queryVulnerabilities: async (
    params: VulnerabilityQueryParams
  ): Promise<VulnerabilityQueryResult[]> => {
    const response = await api.get<VulnerabilityQueryResult[]>('/vulnerabilities/query', {
      params,
    });
    return response.data;
  },

  getCommunityVulnerabilities: async (): Promise<CommunityVulnerability[]> => {
    const response = await api.get<CommunityVulnerability[]>('/vulnerabilities/community');
    return response.data;
  },

  submitCommunityVulnerability: async (
    vulnerabilityData: CommunityVulnerabilityCreate
  ): Promise<CommunityVulnerability> => {
    const response = await api.post<CommunityVulnerability>(
      '/vulnerabilities/community',
      vulnerabilityData
    );
    return response.data;
  },

  verifyCommunityVulnerability: async (
    communityId: number
  ): Promise<CommunityVulnerability> => {
    const response = await api.put<CommunityVulnerability>(
      `/vulnerabilities/community/${communityId}/verify`
    );
    return response.data;
  },

  deleteCommunityVulnerability: async (communityId: number): Promise<void> => {
    await api.delete(`/vulnerabilities/community/${communityId}`);
  },
};

// Simulation API
export const simulationsAPI = {
  runSimulation: async (
    simulationData: SimulationRunCreate
  ): Promise<SimulationSummary> => {
    const response = await api.post<SimulationSummary>('/simulations', simulationData);
    return response.data;
  },

  getSimulations: async (): Promise<SimulationRun[]> => {
    const response = await api.get<SimulationRun[]>('/simulations');
    return response.data;
  },

  getSimulation: async (simulationId: number): Promise<SimulationRun> => {
    const response = await api.get<SimulationRun>(`/simulations/${simulationId}`);
    return response.data;
  },

  getSystemSimulations: async (systemId: number): Promise<SimulationRun[]> => {
    const response = await api.get<SimulationRun[]>(`/simulations/system/${systemId}`);
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getUsers: async (page: number = 1, pageSize: number = 20): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/admin/users', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  toggleAdminStatus: async (userId: number, isAdmin: boolean): Promise<User> => {
    const response = await api.put<User>(`/admin/users/${userId}/admin`, null, {
      params: { is_admin: isAdmin },
    });
    return response.data;
  },

  getAdminStats: async (): Promise<AdminStatsResponse> => {
    const response = await api.get<AdminStatsResponse>('/admin/stats');
    return response.data;
  },
};

// Export the axios instance for custom requests
export default api;
