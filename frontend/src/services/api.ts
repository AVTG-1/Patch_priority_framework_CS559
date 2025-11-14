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

// Helper to parse backend system config to frontend format
const parseSystemConfig = (backendConfig: any): SystemConfig => {
  const configData = JSON.parse(backendConfig.config_json);
  return {
    id: backendConfig.id,
    owner_id: backendConfig.user_id,
    name: backendConfig.name,
    description: backendConfig.description,
    vulnerabilities: configData.vulnerabilities || [],
    subsystems: configData.subsystems,
    dependencies: configData.dependencies,
    created_at: backendConfig.created_at,
    updated_at: backendConfig.created_at, // Backend doesn't have updated_at
  };
};

// System Configuration API
export const systemsAPI = {
  getSystems: async (): Promise<SystemConfig[]> => {
    const response = await api.get<any[]>('/systems');
    return response.data.map(parseSystemConfig);
  },

  getSystem: async (systemId: number): Promise<SystemConfig> => {
    const response = await api.get<any>(`/systems/${systemId}`);
    return parseSystemConfig(response.data);
  },

  createSystem: async (systemData: SystemConfigCreate): Promise<SystemConfig> => {
    const response = await api.post<any>('/systems', systemData);
    return parseSystemConfig(response.data);
  },

  updateSystem: async (
    systemId: number,
    systemData: SystemConfigUpdate
  ): Promise<SystemConfig> => {
    const response = await api.put<any>(`/systems/${systemId}`, systemData);
    return parseSystemConfig(response.data);
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

// Helper to parse backend simulation response to frontend format
const parseSimulationResponse = (backendSim: any): any => {
  // Backend returns different field names than frontend expects
  const {
    simulation_id,
    system_config_id,
    parameters,
    results,
    ...rest
  } = backendSim;

  // Transform results structure to match frontend expectations
  let transformedResult = results;

  if (results && results.status !== 'pending' && results.status !== 'running' && results.status !== 'failed') {
    // Transform backend structure to frontend structure
    transformedResult = {
      // Transform per_round_details to rounds_data
      rounds_data: results.per_round_details?.map((round: any) => ({
        round: round.round,
        remaining_impact_score: round.remaining_ris || 0,
        defender_action: {
          patches: round.patched_groups || [],
          cost: 0, // Backend doesn't provide per-round cost
        },
        attacker_action: {
          exploits: round.attacked_vulnerabilities || [],
          impact: 0, // Backend doesn't provide per-round impact
        },
      })) || [],

      // Transform simulation_metrics to summary
      summary: results.simulation_metrics ? {
        total_rounds: results.simulation_metrics.total_rounds || parameters?.rounds || 0,
        patches_applied: results.simulation_metrics.total_vulnerabilities_patched || 0,
        vulnerabilities_exploited: results.simulation_metrics.total_vulnerabilities_exploited || 0,
        average_ris_per_round: results.ris_summary ?
          results.ris_summary.reduce((a: number, b: number) => a + b, 0) / results.ris_summary.length : 0,
      } : undefined,

      // Create final_scores from simulation_metrics
      final_scores: results.simulation_metrics ? {
        defender_score: results.simulation_metrics.final_ris || 0,
        attacker_score: 0, // Not provided by backend
      } : undefined,

      // Keep original data for reference
      patch_priority_list: results.patch_priority_list,
      equilibrium_report: results.equilibrium_report,
      system_info: results.system_info,
      simulation_metrics: results.simulation_metrics,
    };
  }

  return {
    id: simulation_id,
    system_id: system_config_id,
    // Extract parameters to top level if they exist
    rounds: parameters?.rounds,
    defender_budget: parameters?.defender_budget,
    attacker_budget: parameters?.attacker_budget,
    patch_grouping_method: parameters?.patch_grouping_method,
    // Handle results - backend returns {status, message} or actual results
    status: results?.status || 'completed',
    result: results?.status === 'pending' || results?.status === 'running' ? undefined : transformedResult,
    error_message: results?.message && results?.status === 'failed' ? results.message : undefined,
    ...rest,
  };
};

// Simulation API
export const simulationsAPI = {
  runSimulation: async (
    simulationData: SimulationRunCreate
  ): Promise<SimulationSummary> => {
    const response = await api.post<any>('/simulations', simulationData);
    return parseSimulationResponse(response.data);
  },

  getSimulations: async (): Promise<SimulationRun[]> => {
    const response = await api.get<any[]>('/simulations');
    return response.data.map(parseSimulationResponse);
  },

  getSimulation: async (simulationId: number): Promise<SimulationRun> => {
    const response = await api.get<any>(`/simulations/${simulationId}`);
    return parseSimulationResponse(response.data);
  },

  getSystemSimulations: async (systemId: number): Promise<SimulationRun[]> => {
    const response = await api.get<any[]>(`/simulations/system/${systemId}`);
    return response.data.map(parseSimulationResponse);
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
