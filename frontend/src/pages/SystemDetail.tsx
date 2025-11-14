import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronRight,
  Edit,
  Trash2,
  PlayCircle,
  Shield,
  AlertTriangle,
  Calendar,
} from 'lucide-react';
import { systemsAPI, simulationsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Button from '../components/Button';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import Badge, { getCVSSBadgeVariant, getCVSSSeverityLabel } from '../components/Badge';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

export default function SystemDetail() {
  const { id } = useParams<{ id: string }>();
  const systemId = parseInt(id!);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sortField, setSortField] = useState<'cvss' | 'id'>('cvss');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const {
    data: system,
    isLoading: systemLoading,
    error: systemError,
    refetch: refetchSystem,
  } = useQuery({
    queryKey: ['system', systemId],
    queryFn: () => systemsAPI.getSystem(systemId),
  });

  const {
    data: simulations,
    isLoading: simulationsLoading,
  } = useQuery({
    queryKey: ['simulations', 'system', systemId],
    queryFn: () => simulationsAPI.getSystemSimulations(systemId),
  });

  const deleteMutation = useMutation({
    mutationFn: systemsAPI.deleteSystem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systems'] });
      toast.success('System deleted successfully');
      navigate('/systems');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete system');
    },
  });

  const handleDeleteConfirm = () => {
    deleteMutation.mutate(systemId);
  };

  if (systemLoading) {
    return <LoadingSpinner size="lg" text="Loading system..." />;
  }

  if (systemError || !system) {
    return (
      <ErrorMessage
        title="Failed to load system"
        message="The system could not be loaded. Please try again."
        onRetry={refetchSystem}
      />
    );
  }

  const sortedVulnerabilities = [...system.vulnerabilities].sort((a, b) => {
    const modifier = sortOrder === 'asc' ? 1 : -1;
    if (sortField === 'cvss') {
      return (a.cvss_score - b.cvss_score) * modifier;
    }
    return a.vuln_id.localeCompare(b.vuln_id) * modifier;
  });

  const criticalCount = system.vulnerabilities.filter((v) => v.cvss_score >= 9.0).length;
  const highCount = system.vulnerabilities.filter(
    (v) => v.cvss_score >= 7.0 && v.cvss_score < 9.0
  ).length;
  const mediumCount = system.vulnerabilities.filter(
    (v) => v.cvss_score >= 4.0 && v.cvss_score < 7.0
  ).length;
  const lowCount = system.vulnerabilities.filter((v) => v.cvss_score < 4.0).length;

  const toggleSort = (field: 'cvss' | 'id') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const recentSimulations = simulations?.slice(0, 3) || [];

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex text-sm text-gray-500">
        <Link to="/dashboard" className="hover:text-gray-700">
          Dashboard
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <Link to="/systems" className="hover:text-gray-700">
          Systems
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <span className="text-gray-900">{system.name}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{system.name}</h1>
          {system.description && (
            <p className="mt-1 text-sm text-gray-600">{system.description}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Created {new Date(system.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate(`/systems/${systemId}/edit`)}>
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="danger" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
          <Button onClick={() => navigate(`/simulations/setup/${systemId}`)}>
            <PlayCircle className="h-4 w-4 mr-2" />
            Run Simulation
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Vulnerabilities"
          value={system.vulnerabilities.length}
          icon={Shield}
          color="blue"
        />
        <StatCard
          title="Critical Severity"
          value={criticalCount}
          icon={AlertTriangle}
          description="CVSS ≥ 9.0"
          color="red"
        />
        <StatCard
          title="High Severity"
          value={highCount}
          icon={AlertTriangle}
          description="CVSS 7.0-8.9"
          color="orange"
        />
        <StatCard
          title="Medium/Low"
          value={mediumCount + lowCount}
          icon={Shield}
          description="CVSS < 7.0"
          color="green"
        />
      </div>

      {/* Vulnerabilities Table */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Vulnerabilities</h2>
          <div className="flex gap-2">
            <Badge variant="critical">{criticalCount} Critical</Badge>
            <Badge variant="high">{highCount} High</Badge>
            <Badge variant="medium">{mediumCount} Medium</Badge>
            <Badge variant="low">{lowCount} Low</Badge>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSort('id')}
                >
                  ID {sortField === 'id' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSort('cvss')}
                >
                  CVSS Score {sortField === 'cvss' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Affected Component
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedVulnerabilities.map((vuln, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {vuln.vuln_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {vuln.cvss_score.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant={getCVSSBadgeVariant(vuln.cvss_score)}>
                      {getCVSSSeverityLabel(vuln.cvss_score)}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {vuln.affected_component}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {vuln.description || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Simulations */}
      {!simulationsLoading && recentSimulations.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Simulations</h2>
            <Link
              to="/simulations"
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              View all
            </Link>
          </div>

          <div className="space-y-3">
            {recentSimulations.map((sim) => (
              <div
                key={sim.id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/simulations/${sim.id}`)}
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Simulation #{sim.id}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(sim.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                  </div>
                </div>
                <Badge
                  variant={
                    sim.status === 'completed'
                      ? 'success'
                      : sim.status === 'failed'
                      ? 'danger'
                      : 'warning'
                  }
                >
                  {sim.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete System"
        message="Are you sure you want to delete this system? This action cannot be undone and will also delete all associated simulations."
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
