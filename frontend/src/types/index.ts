// Authentication Types
export interface User {
  id: number;
  email: string;
  username: string;
  is_admin: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// System Configuration Types
export interface Vulnerability {
  vuln_id: string;
  cvss_score: number;
  affected_component: string;
  description?: string;
  dependencies?: string[];
}

// Backend response format (config_json is a JSON string)
export interface SystemConfigResponse {
  id: number;
  user_id: number;
  name: string;
  config_json: string;
  created_at: string;
}

// Parsed configuration object
export interface SystemConfigData {
  vulnerabilities: Vulnerability[];
  subsystems?: Array<{
    name: string;
    importance: number;
  }>;
  dependencies?: Record<string, string[]>;
}

// Frontend-friendly format (parsed from backend)
export interface SystemConfig {
  id: number;
  owner_id: number;
  name: string;
  description?: string;
  vulnerabilities: Vulnerability[];
  created_at: string;
  updated_at: string;
}

// What we send to backend for creation
export interface SystemConfigCreate {
  name: string;
  config_json: string; // JSON string
}

// What we send to backend for update
export interface SystemConfigUpdate {
  name?: string;
  config_json?: string; // JSON string
}

// Vulnerability Query Types
export interface VulnerabilityQueryParams {
  min_cvss?: number;
  max_cvss?: number;
  affected_component?: string;
  limit?: number;
  offset?: number;
}

export interface VulnerabilityQueryResult {
  system_id: number;
  system_name: string;
  vulnerability: Vulnerability;
}

// Community Vulnerability Types
export interface CommunityVulnerability {
  id: number;
  vuln_id: string;
  cvss_score: number;
  affected_component: string;
  description?: string;
  submitted_by: number;
  submitted_at: string;
  verified: boolean;
  verified_by?: number;
  verified_at?: string;
}

export interface CommunityVulnerabilityCreate {
  vuln_id: string;
  cvss_score: number;
  affected_component: string;
  description?: string;
}

// Simulation Types
export interface SimulationRun {
  id: number;
  system_id: number;
  owner_id: number;
  rounds: number;
  defender_budget?: number;
  attacker_budget?: number;
  patch_grouping_method: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: SimulationResult;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface SimulationResult {
  final_scores: {
    defender_score: number;
    attacker_score: number;
  };
  rounds_data: RoundData[];
  summary: {
    total_rounds: number;
    patches_applied: number;
    vulnerabilities_exploited: number;
    average_ris_per_round: number;
  };
}

export interface RoundData {
  round: number;
  defender_action: {
    patches: string[];
    cost: number;
  };
  attacker_action: {
    exploits: string[];
    impact: number;
  };
  remaining_impact_score: number;
}

export interface SimulationRunCreate {
  system_id: number;
  rounds?: number;
  defender_budget?: number;
  attacker_budget?: number;
  patch_grouping_method?: string;
}

export interface SimulationSummary {
  id: number;
  system_id: number;
  status: string;
  created_at: string;
  completed_at?: string;
}

// Admin Types
export interface UserListItem {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface UserListResponse {
  users: UserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminStatsResponse {
  timestamp: string;
  total_counts: {
    total_users: number;
    total_systems: number;
    total_simulations: number;
    total_community_vulnerabilities: number;
  };
  user_distribution: {
    admin_users: number;
    regular_users: number;
  };
  vulnerability_status: {
    verified: number;
    unverified: number;
  };
  recent_activity_7d: {
    new_users: number;
    new_systems: number;
    simulations_run: number;
    vulnerabilities_submitted: number;
  };
  recent_activity_30d: {
    new_users: number;
    new_systems: number;
    simulations_run: number;
    vulnerabilities_submitted: number;
  };
}

// API Error Types
export interface APIError {
  detail: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ValidationErrorResponse {
  detail: ValidationError[];
}

// Pagination Types
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// Chart Data Types (for dashboard visualizations)
export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface SimulationChartData {
  round: number;
  ris: number;
  defenderCost: number;
  attackerImpact: number;
}
