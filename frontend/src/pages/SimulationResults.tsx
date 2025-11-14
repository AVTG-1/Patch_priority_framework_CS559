import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Download,
  TrendingDown,
  Target,
  Zap,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { simulationsAPI, systemsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import Badge from '../components/Badge';
import Button from '../components/Button';

export default function SimulationResults() {
  const { id } = useParams<{ id: string }>();
  const simulationId = parseInt(id!);
  const navigate = useNavigate();

  const [expandedRounds, setExpandedRounds] = useState<Set<number>>(
    new Set([0, 1, 2])
  );

  const {
    data: simulation,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['simulation', simulationId],
    queryFn: () => simulationsAPI.getSimulation(simulationId),
    // Poll every 2 seconds if simulation is pending or running
    refetchInterval: (data) => {
      if (data?.status === 'pending' || data?.status === 'running') {
        return 2000; // 2 seconds
      }
      return false; // Don't poll if completed/failed
    },
  });

  const {
    data: system,
    isLoading: systemLoading,
  } = useQuery({
    queryKey: ['system', simulation?.system_id],
    queryFn: () => systemsAPI.getSystem(simulation!.system_id),
    enabled: !!simulation?.system_id,
  });

  const toggleRound = (round: number) => {
    const newExpanded = new Set(expandedRounds);
    if (newExpanded.has(round)) {
      newExpanded.delete(round);
    } else {
      newExpanded.add(round);
    }
    setExpandedRounds(newExpanded);
  };

  const toggleAllRounds = () => {
    if (simulation?.result?.rounds_data) {
      if (expandedRounds.size === simulation.result.rounds_data.length) {
        setExpandedRounds(new Set());
      } else {
        setExpandedRounds(
          new Set(simulation.result.rounds_data.map((_, idx) => idx))
        );
      }
    }
  };

  const downloadJSON = () => {
    if (!simulation) return;
    const dataStr = JSON.stringify(simulation, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    const link = document.createElement('a');
    link.href = dataUri;
    link.download = `simulation-${simulationId}-results.json`;
    link.click();
  };

  if (isLoading || systemLoading) {
    return <LoadingSpinner size="lg" text="Loading simulation results..." />;
  }

  if (error || !simulation) {
    return (
      <ErrorMessage
        title="Failed to load simulation"
        message="The simulation results could not be loaded. Please try again."
        onRetry={refetch}
      />
    );
  }

  if (simulation.status === 'pending' || simulation.status === 'running') {
    return (
      <Card>
        <div className="text-center py-12">
          <LoadingSpinner size="lg" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">
            Simulation {simulation.status === 'running' ? 'Running' : 'Pending'}
          </h2>
          <p className="mt-2 text-gray-600">
            This simulation is currently {simulation.status}.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Auto-refreshing every 2 seconds...
          </p>
          <Button className="mt-4" onClick={() => navigate('/simulations')}>
            Back to Simulations
          </Button>
        </div>
      </Card>
    );
  }

  if (simulation.status === 'failed') {
    return (
      <Card>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-red-600">Simulation Failed</h2>
          <p className="mt-2 text-gray-600">{simulation.error_message}</p>
          <Button className="mt-4" onClick={() => navigate('/simulations')}>
            Back to Simulations
          </Button>
        </div>
      </Card>
    );
  }

  const result = simulation.result;
  if (!result) {
    return (
      <ErrorMessage
        title="No results available"
        message="This simulation completed but has no results data."
      />
    );
  }

  // Debug logging
  console.log('Simulation result:', result);
  console.log('Rounds data length:', result.rounds_data?.length);
  console.log('Rounds data:', result.rounds_data);

  const initialRIS = result.rounds_data?.[0]?.remaining_impact_score || 0;
  const finalRIS = result.final_scores?.defender_score || 0;
  const risReduction = initialRIS > 0 ? (((initialRIS - finalRIS) / initialRIS) * 100) : 0;

  // Prepare chart data
  const chartData = result.rounds_data?.map((round) => ({
    round: round.round,
    ris: round.remaining_impact_score,
  })) || [];

  console.log('Chart data length:', chartData.length);
  console.log('Chart data:', chartData);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex text-sm text-gray-500">
        <Link to="/dashboard" className="hover:text-gray-700">
          Dashboard
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <Link to="/simulations" className="hover:text-gray-700">
          Simulations
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <span className="text-gray-900">Simulation #{simulationId}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Simulation Results #{simulationId}
          </h1>
          {system && (
            <p className="mt-1 text-sm text-gray-600">
              System:{' '}
              <Link
                to={`/systems/${system.id}`}
                className="text-indigo-600 hover:text-indigo-800"
              >
                {system.name}
              </Link>
            </p>
          )}
          <p className="text-xs text-gray-500">
            {new Date(simulation.created_at).toLocaleString()}
          </p>
        </div>
        <Button variant="outline" onClick={downloadJSON}>
          <Download className="h-4 w-4 mr-2" />
          Export JSON
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Initial RIS"
          value={initialRIS.toFixed(2)}
          icon={Target}
          description="Starting risk level"
          color="red"
        />
        <StatCard
          title="Final RIS"
          value={finalRIS.toFixed(2)}
          icon={Target}
          description="Ending risk level"
          color={finalRIS < initialRIS ? 'green' : 'red'}
        />
        <StatCard
          title="RIS Reduction"
          value={`${risReduction.toFixed(1)}%`}
          icon={TrendingDown}
          description="Risk reduced"
          color={risReduction > 50 ? 'green' : risReduction > 25 ? 'orange' : 'red'}
        />
        <StatCard
          title="Rounds Completed"
          value={result.summary?.total_rounds || simulation.rounds}
          icon={Zap}
          description={`${result.summary?.patches_applied || 0} patches applied`}
          color="blue"
        />
      </div>

      {/* RIS Trajectory Chart */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Risk Impact Score Over Time
        </h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="round"
                label={{ value: 'Round', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                label={{ value: 'RIS', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="ris"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={{ fill: '#4f46e5' }}
                name="Remaining Impact Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Summary Statistics */}
      {result.summary && (
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary Statistics</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-600">Total Rounds</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {result.summary.total_rounds}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Patches Applied</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {result.summary.patches_applied}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Vulnerabilities Exploited</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {result.summary.vulnerabilities_exploited}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-600">Avg RIS per Round</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {result.summary.average_ris_per_round?.toFixed(2) || 'N/A'}
              </dd>
            </div>
          </dl>
        </Card>
      )}

      {/* Round-by-Round Details */}
      {result.rounds_data && result.rounds_data.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Detailed Round Analysis
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Showing {result.rounds_data.length} round{result.rounds_data.length !== 1 ? 's' : ''}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={toggleAllRounds}>
              {expandedRounds.size === result.rounds_data.length
                ? 'Collapse All'
                : 'Expand All'}
            </Button>
          </div>

          <div className="space-y-2">
            {result.rounds_data.map((round, index) => {
              const isExpanded = expandedRounds.has(index);

              return (
                <div key={index} className="border border-gray-200 rounded-md">
                  <button
                    onClick={() => toggleRound(index)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      {isExpanded ? (
                        <ChevronUp className="h-5 w-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-gray-400" />
                      )}
                      <div className="text-left">
                        <h3 className="font-medium text-gray-900">
                          Round {round.round}
                        </h3>
                        <p className="text-sm text-gray-600">
                          RIS: {round.remaining_impact_score.toFixed(2)} | Patches:{' '}
                          {round.defender_action?.patches?.length || 0} | Attacks:{' '}
                          {round.attacker_action?.exploits?.length || 0}
                        </p>
                      </div>
                    </div>
                    <Badge variant="info">RIS: {round.remaining_impact_score.toFixed(2)}</Badge>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900 mb-2">
                            Defender Strategy
                          </h4>
                          <dl className="space-y-1 text-sm">
                            <div>
                              <dt className="text-gray-600">Patches Applied:</dt>
                              <dd className="text-gray-900 font-mono text-xs">
                                {round.defender_action?.patches?.join(', ') || 'None'}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-gray-600">Patch Cost:</dt>
                              <dd className="text-gray-900">
                                {round.defender_action?.cost !== undefined
                                  ? round.defender_action.cost.toFixed(2)
                                  : '0.00'}
                              </dd>
                            </div>
                          </dl>
                        </div>

                        <div>
                          <h4 className="text-sm font-semibold text-gray-900 mb-2">
                            Attacker Strategy
                          </h4>
                          <dl className="space-y-1 text-sm">
                            <div>
                              <dt className="text-gray-600">Exploits Attempted:</dt>
                              <dd className="text-gray-900 font-mono text-xs">
                                {round.attacker_action?.exploits?.join(', ') || 'None'}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-gray-600">Exploit Impact:</dt>
                              <dd className="text-gray-900">
                                {round.attacker_action?.impact !== undefined
                                  ? round.attacker_action.impact.toFixed(2)
                                  : '0.00'}
                              </dd>
                            </div>
                          </dl>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}
