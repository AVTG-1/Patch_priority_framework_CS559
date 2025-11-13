"""
NVD Importer

Integrates with the National Vulnerability Database (NVD) API
to fetch CVE data and enrich vulnerability information.
"""

import time
import requests
from typing import List, Dict, Any, Optional
from .vulnerability import Vulnerability


class NVDImporter:
    """
    Fetches vulnerability data from the NVD API.
    
    API Documentation: https://nvd.nist.gov/developers/vulnerabilities
    """
    
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 6.0):
        """
        Initialize NVD importer.
        
        Args:
            api_key: Optional NVD API key for higher rate limits
            rate_limit_delay: Delay between requests (seconds)
                            6 seconds for no API key, 0.6 for API key
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay if not api_key else 0.6
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"apiKey": self.api_key})
    
    def import_from_nvd(self, cve_ids: List[str], 
                       subsystem_id: str = "unknown",
                       default_patch_cost: float = 10.0) -> List[Vulnerability]:
        """
        Import vulnerabilities from NVD by CVE IDs.
        
        Args:
            cve_ids: List of CVE identifiers to fetch
            subsystem_id: Default subsystem ID for vulnerabilities
            default_patch_cost: Default patch cost if not specified
        
        Returns:
            List of Vulnerability objects
        """
        vulnerabilities = []
        
        for cve_id in cve_ids:
            try:
                vuln = self.fetch_cve(cve_id, subsystem_id, default_patch_cost)
                if vuln:
                    vulnerabilities.append(vuln)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"Warning: Failed to fetch {cve_id}: {e}")
                continue
        
        return vulnerabilities
    
    def fetch_cve(self, cve_id: str, 
                 subsystem_id: str = "unknown",
                 default_patch_cost: float = 10.0) -> Optional[Vulnerability]:
        """
        Fetch a single CVE from NVD.
        
        Args:
            cve_id: CVE identifier
            subsystem_id: Subsystem ID for this vulnerability
            default_patch_cost: Default patch cost
        
        Returns:
            Vulnerability object if found, None otherwise
        """
        try:
            # Make API request
            params = {"cveId": cve_id}
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if CVE found
            if data.get("totalResults", 0) == 0:
                print(f"Warning: CVE {cve_id} not found in NVD")
                return None
            
            # Extract CVE data
            cve_item = data["vulnerabilities"][0]["cve"]
            
            # Extract description
            description = self._extract_description(cve_item)
            
            # Extract CVSS metrics
            cvss_impact, cvss_exploitability = self._extract_cvss_metrics(cve_item)
            
            # Check for known exploits (from references or KEV catalog)
            exploit_present = self._check_exploit_presence(cve_item)
            
            # Create vulnerability
            vulnerability = Vulnerability(
                cve_id=cve_id,
                description=description,
                cvss_impact=cvss_impact,
                cvss_exploitability=cvss_exploitability,
                exploit_present=exploit_present,
                patch_cost=default_patch_cost,
                subsystem_id=subsystem_id,
                dependencies=[],
                custom_extras=self._extract_extra_metadata(cve_item)
            )
            
            return vulnerability
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {cve_id}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing {cve_id}: {e}")
            return None
    
    def _extract_description(self, cve_item: Dict[str, Any]) -> str:
        """Extract description from CVE item."""
        try:
            descriptions = cve_item.get("descriptions", [])
            for desc in descriptions:
                if desc.get("lang") == "en":
                    return desc.get("value", "No description available")
            return "No description available"
        except Exception:
            return "No description available"
    
    def _extract_cvss_metrics(self, cve_item: Dict[str, Any]) -> tuple[float, float]:
        """
        Extract CVSS impact and exploitability scores.
        
        Returns:
            Tuple of (impact_score, exploitability_score)
        """
        try:
            # Try CVSS v3.x first (preferred)
            metrics = cve_item.get("metrics", {})
            
            # Try CVSS v3.1
            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                cvss_data = metrics["cvssMetricV31"][0]["cvssData"]
                # Use base score as approximation if detailed scores not available
                base_score = cvss_data.get("baseScore", 5.0)
                impact_score = base_score  # Simplified
                exploitability_score = base_score  # Simplified
                return impact_score, exploitability_score
            
            # Try CVSS v3.0
            if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                cvss_data = metrics["cvssMetricV30"][0]["cvssData"]
                base_score = cvss_data.get("baseScore", 5.0)
                return base_score, base_score
            
            # Try CVSS v2
            if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                cvss_data = metrics["cvssMetricV2"][0]["cvssData"]
                base_score = cvss_data.get("baseScore", 5.0)
                return base_score, base_score
            
            # No CVSS data found, use defaults
            return 5.0, 5.0
            
        except Exception as e:
            print(f"Warning: Error extracting CVSS metrics: {e}")
            return 5.0, 5.0
    
    def _check_exploit_presence(self, cve_item: Dict[str, Any]) -> bool:
        """
        Check if known exploits exist for this CVE.
        
        Returns:
            True if exploit references found
        """
        try:
            references = cve_item.get("references", [])
            
            # Look for exploit-related tags
            exploit_keywords = ["exploit", "poc", "metasploit", "exploit-db"]
            
            for ref in references:
                tags = ref.get("tags", [])
                for tag in tags:
                    if tag.lower() in exploit_keywords:
                        return True
                
                # Check URL for exploit keywords
                url = ref.get("url", "").lower()
                if any(keyword in url for keyword in exploit_keywords):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_extra_metadata(self, cve_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional metadata for custom_extras."""
        extras = {}
        
        try:
            # Published date
            if "published" in cve_item:
                extras["published_date"] = cve_item["published"]
            
            # Last modified date
            if "lastModified" in cve_item:
                extras["last_modified"] = cve_item["lastModified"]
            
            # Source identifier
            if "sourceIdentifier" in cve_item:
                extras["source"] = cve_item["sourceIdentifier"]
            
            # Vulnerability status
            if "vulnStatus" in cve_item:
                extras["status"] = cve_item["vulnStatus"]
            
            # CWE (weakness type)
            if "weaknesses" in cve_item and cve_item["weaknesses"]:
                weakness = cve_item["weaknesses"][0]
                if "description" in weakness and weakness["description"]:
                    cwe = weakness["description"][0].get("value", "")
                    if cwe:
                        extras["cwe"] = cwe
            
        except Exception as e:
            print(f"Warning: Error extracting extra metadata: {e}")
        
        return extras
    
    def bulk_import(self, cve_ids: List[str], 
                   subsystem_mapping: Dict[str, str],
                   default_patch_costs: Optional[Dict[str, float]] = None) -> List[Vulnerability]:
        """
        Import multiple CVEs with custom subsystem mappings.
        
        Args:
            cve_ids: List of CVE IDs to import
            subsystem_mapping: Dict mapping CVE ID to subsystem ID
            default_patch_costs: Optional dict mapping CVE ID to patch cost
        
        Returns:
            List of Vulnerability objects
        """
        vulnerabilities = []
        default_patch_costs = default_patch_costs or {}
        
        for cve_id in cve_ids:
            subsystem_id = subsystem_mapping.get(cve_id, "unknown")
            patch_cost = default_patch_costs.get(cve_id, 10.0)
            
            vuln = self.fetch_cve(cve_id, subsystem_id, patch_cost)
            if vuln:
                vulnerabilities.append(vuln)
            
            time.sleep(self.rate_limit_delay)
        
        return vulnerabilities
    
    def search_by_keyword(self, keyword: str, max_results: int = 20) -> List[str]:
        """
        Search for CVEs by keyword.
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results
        
        Returns:
            List of CVE IDs
        """
        try:
            params = {
                "keywordSearch": keyword,
                "resultsPerPage": min(max_results, 2000)
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            cve_ids = []
            for vuln in data.get("vulnerabilities", []):
                cve_id = vuln["cve"]["id"]
                cve_ids.append(cve_id)
                
                if len(cve_ids) >= max_results:
                    break
            
            return cve_ids
            
        except Exception as e:
            print(f"Error searching CVEs: {e}")
            return []
