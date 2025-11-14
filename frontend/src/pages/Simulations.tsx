import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, Eye, Calendar, TrendingDown, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { simulationsAPI, systemsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';

export default function Simulations() {
  const navigate = useNavigate();
  const [filterSystemId, setFilterSystemId] = useState<number | null>(null);
  const [explanationOpen, setExplanationOpen] = useState(false);

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

      {/* How It Works Explanation */}
      <Card>
        <button
          onClick={() => setExplanationOpen(!explanationOpen)}
          className="w-full flex items-center justify-between p-2 hover:bg-gray-50 rounded"
        >
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              How Simulations Work - Calculation Details
            </h2>
          </div>
          {explanationOpen ? (
            <ChevronUp className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-500" />
          )}
        </button>

        {explanationOpen && (
          <div className="mt-4 pt-4 border-t border-gray-200 space-y-6 text-sm text-gray-700">
            {/* RIS Calculation */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                📊 Remaining Impact Score (RIS)
              </h3>
              <p className="mb-2">
                RIS represents the <strong>total remaining risk</strong> in your system:
              </p>
              <div className="bg-gray-50 p-3 rounded font-mono text-xs mb-2">
                RIS = Σ (CVSS Impact × Subsystem Importance × Exploit Multiplier)
              </div>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>CVSS Impact:</strong> Severity of vulnerability (0-10)</li>
                <li><strong>Subsystem Importance:</strong> Calculated using PageRank-like algorithm based on dependencies (0-1)</li>
                <li><strong>Exploit Multiplier:</strong> 1.5 if public exploit exists, 1.0 otherwise</li>
              </ul>
              <p className="mt-2 italic">
                Higher RIS = More risk. Goal: Reduce RIS by patching high-impact vulnerabilities.
              </p>
            </div>

            {/* Subsystem Importance */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                🔗 Subsystem Importance Calculation
              </h3>
              <p className="mb-2">
                Uses a <strong>PageRank-style algorithm</strong> with damping factor (0.85):
              </p>
              <div className="bg-gray-50 p-3 rounded font-mono text-xs mb-2">
                importance[i] = (1-d)/n + d × (0.6×W.T + 0.4×N.T) @ importance
              </div>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>d = 0.85:</strong> Damping factor prevents zero convergence</li>
                <li><strong>W:</strong> Functional dependency matrix (if A depends on B, B is more important)</li>
                <li><strong>N:</strong> Network topology matrix (connections between subsystems)</li>
                <li><strong>0.6/0.4:</strong> Weights for functional vs. topological importance</li>
              </ul>
              <p className="mt-2 italic">
                Subsystems that others depend on get higher importance scores.
              </p>
            </div>

            {/* Game Theory & Nash Equilibrium */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                🎯 Game-Theoretic Simulation (Nash Equilibrium)
              </h3>
              <p className="mb-2">
                Each round simulates a <strong>two-player zero-sum game</strong> between defenders and attackers:
              </p>
              <div className="space-y-2">
                <div className="bg-blue-50 p-3 rounded">
                  <p className="font-semibold text-blue-900 mb-1">Defender Strategy:</p>
                  <ul className="list-disc list-inside ml-2 text-blue-800">
                    <li>Choose which patch groups to apply (limited by budget)</li>
                    <li>Payoff = -(attack impact) - 0.1×(patch cost)</li>
                    <li>Goal: Minimize attacker's successful impact</li>
                  </ul>
                </div>
                <div className="bg-red-50 p-3 rounded">
                  <p className="font-semibold text-red-900 mb-1">Attacker Strategy:</p>
                  <ul className="list-disc list-inside ml-2 text-red-800">
                    <li>Choose which vulnerabilities to exploit (limited by budget)</li>
                    <li>Exploit cost = 10.0 - CVSS Exploitability (harder = costlier)</li>
                    <li>Payoff = (impact if unpatched) - 0.1×(exploit cost)</li>
                    <li>Goal: Maximize impact on unpatched vulnerabilities</li>
                  </ul>
                </div>
              </div>
              <p className="mt-2">
                The <strong>Nash equilibrium solver</strong> finds optimal strategies where neither player can improve by changing strategy alone.
              </p>
            </div>

            {/* Cost and Impact */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                💰 Cost and Impact Metrics
              </h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-green-50 p-3 rounded">
                  <p className="font-semibold text-green-900 mb-1">Patch Cost:</p>
                  <div className="text-green-800 text-xs">
                    <p>Sum of <code>patch_cost</code> for all vulnerabilities in applied patch groups.</p>
                    <p className="mt-1">Represents resources spent on patching (time, effort, downtime).</p>
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded">
                  <p className="font-semibold text-orange-900 mb-1">Exploit Impact:</p>
                  <div className="text-orange-800 text-xs">
                    <p>For each successful attack:</p>
                    <code className="block mt-1">
                      impact = CVSS Impact × importance × 1.5 (if exploit exists)
                    </code>
                    <p className="mt-1">Represents actual damage from successful exploits.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Patch Grouping */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                📦 Patch Grouping Methods
              </h3>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>Dependencies:</strong> Group patches with same dependency chain</li>
                <li><strong>Subsystem:</strong> Group all vulnerabilities in same subsystem</li>
                <li><strong>Severity:</strong> Group by CVSS severity levels</li>
              </ul>
            </div>

            {/* Why Attackers May Not Attack */}
            <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
              <h3 className="font-semibold text-yellow-900 mb-2">
                ⚠️ Why You Might See "No Attacks"
              </h3>
              <p className="text-yellow-800 mb-2">
                This is <strong>correct behavior</strong> when the Nash equilibrium determines "do nothing" is optimal for attackers:
              </p>
              <ul className="list-disc list-inside ml-2 text-yellow-800 space-y-1">
                <li>High-value targets already patched by defender</li>
                <li>Remaining vulnerabilities have low exploitability (high cost, low reward)</li>
                <li>Expected payoff negative (cost exceeds potential impact)</li>
                <li>Rational attacker chooses not to waste resources</li>
              </ul>
              <p className="mt-2 text-yellow-800 italic">
                To see more attacker activity: increase attacker budget, add high-exploitability vulnerabilities, or lower defender budget.
              </p>
            </div>
          </div>
        )}
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
