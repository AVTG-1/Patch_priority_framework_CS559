import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, Eye, Calendar, TrendingDown } from 'lucide-react';
import { simulationsAPI, systemsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';

export default function Simulations() {
  const navigate = useNavigate();
  const [filterSystemId, setFilterSystemId] = useState<number | null>(null);

  const {
    data: simulations,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['simulations'],
    queryFn: simulationsAPI.getSimulations,
  });

  const {
    data: systems,
    isLoading: systemsLoading,
  } = useQuery({
    queryKey: ['systems'],
    queryFn: systemsAPI.getSystems,
  });

  if (isLoading || systemsLoading) {
    return <LoadingSpinner size="lg" text="Loading simulations..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load simulations"
        message="There was an error loading your simulations. Please try again."
        onRetry={refetch}
      />
    );
  }

  const filteredSimulations = simulations?.filter((sim) =>
    filterSystemId ? sim.system_id === filterSystemId : true
  );

  const getSystemName = (systemId: number) => {
    const system = systems?.find((s) => s.id === systemId);
    return system?.name || `System #${systemId}`;
  };

  const getRISReduction = (simulation: any) => {
    if (!simulation.result?.final_scores) return null;
    const initial = simulation.result.summary?.average_ris_per_round || 0;
    const final = simulation.result.final_scores.defender_score;
    if (initial === 0) return null;
    return (((initial - final) / initial) * 100).toFixed(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Simulations</h1>
          <p className="mt-1 text-sm text-gray-600">
            View all your simulation runs and results
          </p>
        </div>
        <Button onClick={() => navigate('/simulations/setup')}>
          <PlayCircle className="h-4 w-4 mr-2" />
          Run New Simulation
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Filter by system:</label>
          <select
            value={filterSystemId || ''}
            onChange={(e) =>
              setFilterSystemId(e.target.value ? parseInt(e.target.value) : null)
            }
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Systems</option>
            {systems?.map((system) => (
              <option key={system.id} value={system.id}>
                {system.name}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Simulations List */}
      {!filteredSimulations || filteredSimulations.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">No simulations yet</p>
            <Button onClick={() => navigate('/simulations/setup')}>
              <PlayCircle className="h-4 w-4 mr-2" />
              Run Your First Simulation
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredSimulations.map((simulation) => {
            const risReduction = getRISReduction(simulation);

            return (
              <div
                key={simulation.id}
                onClick={() => navigate(`/simulations/${simulation.id}`)}
                className="cursor-pointer"
              >
                <Card hover>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Simulation #{simulation.id}
                      </h3>
                      <Badge
                        variant={
                          simulation.status === 'completed'
                            ? 'success'
                            : simulation.status === 'failed'
                            ? 'danger'
                            : simulation.status === 'running'
                            ? 'info'
                            : 'warning'
                        }
                      >
                        {simulation.status}
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-600 mb-3">
                      System: {getSystemName(simulation.system_id)}
                    </p>

                    <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {new Date(simulation.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      <span>Rounds: {simulation.rounds}</span>
                      {simulation.status === 'completed' && risReduction && (
                        <span className="flex items-center gap-1 text-green-600 font-medium">
                          <TrendingDown className="h-4 w-4" />
                          {risReduction}% RIS Reduction
                        </span>
                      )}
                    </div>

                    {simulation.error_message && (
                      <div className="mt-2 text-sm text-red-600">
                        Error: {simulation.error_message}
                      </div>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/simulations/${simulation.id}`);
                    }}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                </div>
              </Card>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
