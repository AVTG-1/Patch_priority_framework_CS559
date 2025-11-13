import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../stores/authStore';
import { systemsAPI, simulationsAPI, adminAPI } from '../services/api';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import {
  Database,
  PlayCircle,
  Users,
  Shield,
  AlertTriangle,
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuthStore();

  // Fetch user's systems
  const {
    data: systems,
    isLoading: systemsLoading,
    error: systemsError,
    refetch: refetchSystems,
  } = useQuery({
    queryKey: ['systems'],
    queryFn: systemsAPI.getSystems,
  });

  // Fetch user's simulations
  const {
    data: simulations,
    isLoading: simulationsLoading,
    error: simulationsError,
    refetch: refetchSimulations,
  } = useQuery({
    queryKey: ['simulations'],
    queryFn: simulationsAPI.getSimulations,
  });

  // Fetch admin stats if user is admin
  const {
    data: adminStats,
    isLoading: adminStatsLoading,
    error: adminStatsError,
    refetch: refetchAdminStats,
  } = useQuery({
    queryKey: ['adminStats'],
    queryFn: adminAPI.getAdminStats,
    enabled: user?.is_admin === true,
  });

  const isLoading = systemsLoading || simulationsLoading || (user?.is_admin && adminStatsLoading);
  const hasError = systemsError || simulationsError || (user?.is_admin && adminStatsError);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  if (hasError) {
    return (
      <ErrorMessage
        title="Failed to load dashboard"
        message="There was an error loading your dashboard data. Please try again."
        onRetry={() => {
          refetchSystems();
          refetchSimulations();
          if (user?.is_admin) refetchAdminStats();
        }}
      />
    );
  }

  // Calculate statistics
  const totalSystems = systems?.length || 0;
  const totalSimulations = simulations?.length || 0;
  const completedSimulations =
    simulations?.filter((sim) => sim.status === 'completed').length || 0;
  const runningSimulations =
    simulations?.filter((sim) => sim.status === 'running' || sim.status === 'pending').length || 0;

  // Calculate total vulnerabilities across all systems
  const totalVulnerabilities =
    systems?.reduce((acc, system) => acc + system.vulnerabilities.length, 0) || 0;

  // Calculate high severity vulnerabilities (CVSS >= 7.0)
  const highSeverityVulnerabilities =
    systems?.reduce(
      (acc, system) =>
        acc + system.vulnerabilities.filter((vuln) => vuln.cvss_score >= 7.0).length,
      0
    ) || 0;

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.username}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here's an overview of your patch prioritization systems and simulations.
        </p>
      </div>

      {/* User Statistics */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Your Overview</h2>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Total Systems"
            value={totalSystems}
            icon={Database}
            description="Configured vulnerability systems"
            color="blue"
          />
          <StatCard
            title="Total Simulations"
            value={totalSimulations}
            icon={PlayCircle}
            description={`${completedSimulations} completed, ${runningSimulations} in progress`}
            color="green"
          />
          <StatCard
            title="Total Vulnerabilities"
            value={totalVulnerabilities}
            icon={Shield}
            description={`${highSeverityVulnerabilities} high severity (CVSS ≥ 7.0)`}
            color="purple"
          />
        </div>
      </div>

      {/* High Severity Alert */}
      {highSeverityVulnerabilities > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                You have{' '}
                <span className="font-medium">{highSeverityVulnerabilities}</span> high
                severity vulnerabilities that require immediate attention.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Admin Statistics */}
      {user?.is_admin && adminStats && (
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Platform Overview (Admin)</h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Users"
              value={adminStats.total_counts.total_users}
              icon={Users}
              description={`${adminStats.user_distribution.admin_users} admins`}
              color="blue"
            />
            <StatCard
              title="Total Systems"
              value={adminStats.total_counts.total_systems}
              icon={Database}
              description="Across all users"
              color="green"
            />
            <StatCard
              title="Total Simulations"
              value={adminStats.total_counts.total_simulations}
              icon={PlayCircle}
              description="All-time simulations run"
              color="purple"
            />
            <StatCard
              title="Community Vulnerabilities"
              value={adminStats.total_counts.total_community_vulnerabilities}
              icon={Shield}
              description={`${adminStats.vulnerability_status.verified} verified`}
              color="orange"
            />
          </div>

          {/* Recent Activity */}
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-base font-medium text-gray-900 mb-4">
                Last 7 Days Activity
              </h3>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">New Users</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_7d.new_users}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">New Systems</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_7d.new_systems}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">Simulations Run</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_7d.simulations_run}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">Vulnerabilities Submitted</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_7d.vulnerabilities_submitted}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-base font-medium text-gray-900 mb-4">
                Last 30 Days Activity
              </h3>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">New Users</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_30d.new_users}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">New Systems</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_30d.new_systems}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">Simulations Run</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_30d.simulations_run}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">Vulnerabilities Submitted</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {adminStats.recent_activity_30d.vulnerabilities_submitted}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <a
            href="/systems"
            className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <Database className="h-5 w-5 mr-2" />
            Manage Systems
          </a>
          <a
            href="/simulations"
            className="flex items-center justify-center px-4 py-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <PlayCircle className="h-5 w-5 mr-2" />
            Run Simulation
          </a>
          {user?.is_admin && (
            <a
              href="/admin"
              className="flex items-center justify-center px-4 py-3 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Users className="h-5 w-5 mr-2" />
              Admin Panel
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
