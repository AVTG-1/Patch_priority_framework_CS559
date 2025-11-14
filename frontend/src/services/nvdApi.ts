import api from './api';

// Backend response from /api/vulnerabilities/nvd endpoint
export interface NVDBackendResponse {
  cve_id: string;
  description: string;
  cvss_impact: number;
  cvss_exploitability: number;
  cvss_base_score?: number;
  severity?: string;
  published_date?: string;
  affected_component?: string;
}

// Frontend display format
export interface NVDVulnerability {
  id: string;
  descriptions: Array<{
    lang: string;
    value: string;
  }>;
  published: string;
  cvss_impact: number;
  cvss_exploitability: number;
  cvss_base_score: number;
  severity: string;
  affected_component: string;
}

export const nvdAPI = {
  searchByCVE: async (cveId: string): Promise<NVDVulnerability | null> => {
    try {
      const response = await api.get<NVDBackendResponse>('/vulnerabilities/nvd', {
        params: {
          cve_id: cveId.trim(),
        },
      });

      // Transform backend response to frontend format
      const data = response.data;
      return {
        id: data.cve_id,
        descriptions: [{ lang: 'en', value: data.description }],
        published: data.published_date || new Date().toISOString(),
        cvss_impact: data.cvss_impact,
        cvss_exploitability: data.cvss_exploitability,
        cvss_base_score: data.cvss_base_score || (data.cvss_impact + data.cvss_exploitability) / 2,
        severity: data.severity || 'UNKNOWN',
        affected_component: data.affected_component || 'unknown',
      };
    } catch (error: any) {
      console.error('NVD API error:', error);
      if (error.response?.status === 404) {
        return null;
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch CVE from NVD');
    }
  },
};

// Helper to extract CVSS scores (simplified for backend response)
export const extractCVSSScores = (vuln: NVDVulnerability): {
  baseScore: number;
  impact: number;
  exploitability: number;
  severity: string;
} => {
  return {
    baseScore: vuln.cvss_base_score,
    impact: vuln.cvss_impact,
    exploitability: vuln.cvss_exploitability,
    severity: vuln.severity,
  };
};

// Helper to extract description
export const extractDescription = (vuln: NVDVulnerability): string => {
  const englishDesc = vuln.descriptions.find(d => d.lang === 'en');
  return englishDesc?.value || vuln.descriptions[0]?.value || 'No description available';
};

// Helper to extract affected components
export const extractAffectedComponent = (vuln: NVDVulnerability): string => {
  return vuln.affected_component || 'unknown';
};
