import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Shield, CheckCircle, AlertTriangle } from 'lucide-react';
import { vulnerabilitiesAPI } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import Tabs, { Tab } from '../components/Tabs';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { useToast } from '../components/Toast';
import type { CommunityVulnerabilityCreate } from '../types';

export default function Vulnerabilities() {
  const [activeTab, setActiveTab] = useState('community');
  const { user } = useAuthStore();
  const toast = useToast();
  const queryClient = useQueryClient();

  // Community vulnerabilities state
  const [statusFilter, setStatusFilter] = useState<'all' | 'verified' | 'unverified'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // NVD search state
  const [cveId, setCveId] = useState('');

  // Submit form state
  const [submitForm, setSubmitForm] = useState<CommunityVulnerabilityCreate>({
    vuln_id: '',
    cvss_impact: 5.0,
    cvss_exploitability: 5.0,
    affected_component: '',
    description: '',
  });

  const {
    data: communityVulns,
    isLoading: communityLoading,
    error: communityError,
    refetch: refetchCommunity,
  } = useQuery({
    queryKey: ['communityVulnerabilities'],
    queryFn: vulnerabilitiesAPI.getCommunityVulnerabilities,
  });

  const submitMutation = useMutation({
    mutationFn: vulnerabilitiesAPI.submitCommunityVulnerability,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['communityVulnerabilities'] });
      toast.success(`Vulnerability submitted successfully! ID: ${data.vuln_id}`);
      setSubmitForm({
        vuln_id: '',
        cvss_impact: 5.0,
        cvss_exploitability: 5.0,
        affected_component: '',
        description: '',
      });
      setActiveTab('community');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit vulnerability');
    },
  });

  const verifyMutation = useMutation({
    mutationFn: vulnerabilitiesAPI.verifyCommunityVulnerability,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communityVulnerabilities'] });
      toast.success('Vulnerability verified successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to verify vulnerability');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: vulnerabilitiesAPI.deleteCommunityVulnerability,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communityVulnerabilities'] });
      toast.success('Vulnerability deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete vulnerability');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!submitForm.description || submitForm.description.length < 10) {
      toast.error('Description must be at least 10 characters');
      return;
    }

    if (submitForm.description.length > 500) {
      toast.error('Description must be under 500 characters');
      return;
    }

    if (submitForm.cvss_impact < 0 || submitForm.cvss_impact > 10) {
      toast.error('CVSS Impact must be between 0 and 10');
      return;
    }

    if (submitForm.cvss_exploitability < 0 || submitForm.cvss_exploitability > 10) {
      toast.error('CVSS Exploitability must be between 0 and 10');
      return;
    }

    submitMutation.mutate(submitForm);
  };

  const filteredVulns = communityVulns
    ?.filter((v) => {
      if (statusFilter === 'verified') return v.verified;
      if (statusFilter === 'unverified') return !v.verified;
      return true;
    })
    .filter((v) => {
      if (!searchTerm) return true;
      return (
        v.vuln_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        v.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    });

  const tabs: Tab[] = [
    {
      id: 'nvd',
      label: 'NVD Search',
      icon: <Search className="h-4 w-4" />,
      content: (
        <Card>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CVE ID
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={cveId}
                  onChange={(e) => setCveId(e.target.value)}
                  placeholder="CVE-2024-1234"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <Button disabled>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    NVD Integration Coming Soon
                  </h3>
                  <p className="mt-1 text-sm text-blue-700">
                    Direct NVD database search is not yet implemented. You can manually enter
                    vulnerability information in the "Submit New" tab or browse community-submitted
                    vulnerabilities.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      ),
    },
    {
      id: 'community',
      label: 'Community Vulnerabilities',
      icon: <Shield className="h-4 w-4" />,
      content: (
        <div className="space-y-4">
          {/* Filters */}
          <Card>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search by ID or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-4 py-2 rounded-md text-sm font-medium ${
                    statusFilter === 'all'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setStatusFilter('verified')}
                  className={`px-4 py-2 rounded-md text-sm font-medium ${
                    statusFilter === 'verified'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Verified
                </button>
                <button
                  onClick={() => setStatusFilter('unverified')}
                  className={`px-4 py-2 rounded-md text-sm font-medium ${
                    statusFilter === 'unverified'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Unverified
                </button>
              </div>
            </div>
          </Card>

          {/* Vulnerabilities List */}
          {communityLoading ? (
            <LoadingSpinner text="Loading community vulnerabilities..." />
          ) : communityError ? (
            <ErrorMessage
              message="Failed to load community vulnerabilities"
              onRetry={refetchCommunity}
            />
          ) : !filteredVulns || filteredVulns.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <p className="text-gray-500">No vulnerabilities found</p>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredVulns.map((vuln) => (
                <Card key={vuln.id} hover>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {vuln.vuln_id}
                        </h3>
                        <Badge variant={vuln.verified ? 'success' : 'warning'}>
                          {vuln.verified ? (
                            <>
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Verified
                            </>
                          ) : (
                            'Unverified'
                          )}
                        </Badge>
                      </div>

                      <p className="text-sm text-gray-600 mb-3">{vuln.description}</p>

                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <span>
                          <strong>CVSS Score:</strong> {vuln.cvss_score.toFixed(1)}
                        </span>
                        <span>
                          <strong>Component:</strong> {vuln.affected_component}
                        </span>
                        <span>
                          <strong>Submitted:</strong>{' '}
                          {new Date(vuln.submitted_at).toLocaleDateString()}
                        </span>
                      </div>

                      {user?.is_admin && (
                        <div className="mt-3 flex gap-2">
                          {!vuln.verified && (
                            <Button
                              size="sm"
                              onClick={() => verifyMutation.mutate(vuln.id)}
                              loading={verifyMutation.isPending}
                            >
                              Verify
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => deleteMutation.mutate(vuln.id)}
                            loading={deleteMutation.isPending}
                          >
                            Delete
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      id: 'submit',
      label: 'Submit New',
      content: (
        <Card>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vulnerability ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={submitForm.vuln_id}
                onChange={(e) => setSubmitForm({ ...submitForm, vuln_id: e.target.value })}
                placeholder="COMM-2024-0001"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Use format: COMM-YYYY-NNNN (will be auto-generated by backend)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={submitForm.description}
                onChange={(e) => setSubmitForm({ ...submitForm, description: e.target.value })}
                rows={4}
                maxLength={500}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Describe the vulnerability..."
              />
              <p className="mt-1 text-xs text-gray-500">
                {submitForm.description?.length || 0} / 500 characters (minimum 10 required)
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CVSS Impact Score <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={submitForm.cvss_impact}
                  onChange={(e) =>
                    setSubmitForm({ ...submitForm, cvss_impact: parseFloat(e.target.value) })
                  }
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Impact on confidentiality, integrity, and availability (0-10)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CVSS Exploitability Score <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={submitForm.cvss_exploitability}
                  onChange={(e) =>
                    setSubmitForm({ ...submitForm, cvss_exploitability: parseFloat(e.target.value) })
                  }
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Ease of exploiting the vulnerability (0-10)
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Affected Component <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={submitForm.affected_component}
                onChange={(e) =>
                  setSubmitForm({ ...submitForm, affected_component: e.target.value })
                }
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., web-server, database"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setSubmitForm({
                    vuln_id: '',
                    cvss_impact: 5.0,
                    cvss_exploitability: 5.0,
                    affected_component: '',
                    description: '',
                  });
                }}
              >
                Clear
              </Button>
              <Button type="submit" loading={submitMutation.isPending}>
                Submit Vulnerability
              </Button>
            </div>
          </form>
        </Card>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Vulnerabilities</h1>
        <p className="mt-1 text-sm text-gray-600">
          Browse and submit vulnerability information
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
    </div>
  );
}
