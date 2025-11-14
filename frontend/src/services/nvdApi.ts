import axios from 'axios';

const NVD_API_KEY = '693feb1f-c792-4ddf-9c6a-46cdce5fa0bd';
const NVD_BASE_URL = 'https://services.nvd.nist.gov/rest/json/cves/2.0';

export interface NVDVulnerability {
  id: string;
  sourceIdentifier: string;
  published: string;
  lastModified: string;
  vulnStatus: string;
  descriptions: Array<{
    lang: string;
    value: string;
  }>;
  metrics?: {
    cvssMetricV31?: Array<{
      cvssData: {
        baseScore: number;
        baseSeverity: string;
        vectorString: string;
        impactScore?: number;
        exploitabilityScore?: number;
      };
    }>;
    cvssMetricV2?: Array<{
      cvssData: {
        baseScore: number;
        vectorString: string;
        impactScore?: number;
        exploitabilityScore?: number;
      };
    }>;
  };
  configurations?: Array<{
    nodes: Array<{
      cpeMatch: Array<{
        criteria: string;
        vulnerable: boolean;
      }>;
    }>;
  }>;
}

export interface NVDSearchResult {
  vulnerabilities: Array<{
    cve: NVDVulnerability;
  }>;
  resultsPerPage: number;
  startIndex: number;
  totalResults: number;
}

const nvdApi = axios.create({
  baseURL: NVD_BASE_URL,
  headers: {
    'apiKey': NVD_API_KEY,
  },
});

export const nvdAPI = {
  searchByCVE: async (cveId: string): Promise<NVDVulnerability | null> => {
    try {
      const response = await nvdApi.get<NVDSearchResult>('', {
        params: {
          cveId: cveId.trim(),
        },
      });

      if (response.data.vulnerabilities.length > 0) {
        return response.data.vulnerabilities[0].cve;
      }
      return null;
    } catch (error) {
      console.error('NVD API error:', error);
      throw new Error('Failed to fetch CVE from NVD');
    }
  },

  searchByKeyword: async (keyword: string, startIndex: number = 0): Promise<NVDSearchResult> => {
    try {
      const response = await nvdApi.get<NVDSearchResult>('', {
        params: {
          keywordSearch: keyword,
          resultsPerPage: 20,
          startIndex,
        },
      });
      return response.data;
    } catch (error) {
      console.error('NVD API error:', error);
      throw new Error('Failed to search NVD');
    }
  },
};

// Helper to extract CVSS scores
export const extractCVSSScores = (vuln: NVDVulnerability): {
  baseScore: number;
  impact: number;
  exploitability: number;
  severity: string;
} => {
  // Prefer CVSS v3.1 over v2
  const v31 = vuln.metrics?.cvssMetricV31?.[0]?.cvssData;
  if (v31) {
    return {
      baseScore: v31.baseScore,
      impact: v31.impactScore || v31.baseScore * 0.6,
      exploitability: v31.exploitabilityScore || v31.baseScore * 0.4,
      severity: v31.baseSeverity,
    };
  }

  const v2 = vuln.metrics?.cvssMetricV2?.[0]?.cvssData;
  if (v2) {
    return {
      baseScore: v2.baseScore,
      impact: v2.impactScore || v2.baseScore * 0.6,
      exploitability: v2.exploitabilityScore || v2.baseScore * 0.4,
      severity: v2.baseScore >= 7 ? 'HIGH' : v2.baseScore >= 4 ? 'MEDIUM' : 'LOW',
    };
  }

  return {
    baseScore: 5.0,
    impact: 5.0,
    exploitability: 5.0,
    severity: 'UNKNOWN',
  };
};

// Helper to extract description
export const extractDescription = (vuln: NVDVulnerability): string => {
  const englishDesc = vuln.descriptions.find(d => d.lang === 'en');
  return englishDesc?.value || vuln.descriptions[0]?.value || 'No description available';
};

// Helper to extract affected components
export const extractAffectedComponent = (vuln: NVDVulnerability): string => {
  const cpeMatch = vuln.configurations?.[0]?.nodes?.[0]?.cpeMatch?.[0];
  if (cpeMatch) {
    const parts = cpeMatch.criteria.split(':');
    if (parts.length > 4) {
      return `${parts[3]}-${parts[4]}`; // vendor-product
    }
  }
  return 'unknown';
};
