import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { PlayCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { systemsAPI, simulationsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Button from '../components/Button';
import Card from '../components/Card';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';
import type { SimulationRunCreate } from '../types';

export default function SimulationSetup() {
  const navigate = useNavigate();
  const { systemId } = useParams<{ systemId: string }>();
  const toast = useToast();

  const [selectedSystemId, setSelectedSystemId] = useState<number | null>(
    systemId ? parseInt(systemId) : null
  );
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);

  const [formData, setFormData] = useState<SimulationRunCreate>({
    system_id: selectedSystemId || 0,
    rounds: 10,
    defender_budget: undefined,
    attacker_budget: undefined,
    patch_grouping_method: 'dependencies',
  });

  const {
    data: systems,
    isLoading: systemsLoading,
    error: systemsError,
  } = useQuery({
    queryKey: ['systems'],
    queryFn: systemsAPI.getSystems,
  });

  const {
    data: selectedSystem,
    isLoading: systemLoading,
  } = useQuery({
    queryKey: ['system', selectedSystemId],
    queryFn: () => systemsAPI.getSystem(selectedSystemId!),
    enabled: !!selectedSystemId,
  });

  const runSimulationMutation = useMutation({
    mutationFn: simulationsAPI.runSimulation,
    onSuccess: (data) => {
      setShowProgressModal(false);
      toast.success('Simulation started successfully!');
      navigate(`/simulations/${data.id}`);
    },
    onError: (error: any) => {
      setShowProgressModal(false);
      toast.error(error.response?.data?.detail || 'Failed to start simulation');
    },
  });

  useEffect(() => {
    if (selectedSystemId) {
      setFormData((prev) => ({ ...prev, system_id: selectedSystemId }));
    }
  }, [selectedSystemId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.system_id) {
      toast.error('Please select a system');
      return;
    }

    if (!formData.rounds || formData.rounds < 1 || formData.rounds > 20) {
      toast.error('Rounds must be between 1 and 20');
      return;
    }

    if (formData.defender_budget !== undefined && formData.defender_budget < 0) {
      toast.error('Defender budget must be non-negative');
      return;
    }

    if (formData.attacker_budget !== undefined && formData.attacker_budget < 0) {
      toast.error('Attacker budget must be non-negative');
      return;
    }

    setShowProgressModal(true);
    runSimulationMutation.mutate(formData);
  };

  if (systemsLoading) {
    return <LoadingSpinner size="lg" text="Loading systems..." />;
  }

  if (systemsError) {
    return (
      <ErrorMessage
        title="Failed to load systems"
        message="Unable to load your systems. Please try again."
      />
    );
  }

  if (!systems || systems.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">
            You need to create a system before running simulations
          </p>
          <Button onClick={() => navigate('/systems/create')}>Create System</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Run Simulation</h1>
        <p className="mt-1 text-sm text-gray-600">
          Configure and execute a patch prioritization simulation
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* System Selection */}
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Selection</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select System <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedSystemId || ''}
              onChange={(e) => setSelectedSystemId(parseInt(e.target.value))}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select a system...</option>
              {systems.map((system) => (
                <option key={system.id} value={system.id}>
                  {system.name} ({system.vulnerabilities.length} vulnerabilities)
                </option>
              ))}
            </select>
          </div>

          {systemLoading && <LoadingSpinner size="sm" text="Loading system details..." />}

          {selectedSystem && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <h4 className="text-sm font-medium text-gray-900 mb-2">System Information</h4>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <dt className="text-gray-600">Name:</dt>
                <dd className="text-gray-900">{selectedSystem.name}</dd>
                <dt className="text-gray-600">Vulnerabilities:</dt>
                <dd className="text-gray-900">{selectedSystem.vulnerabilities.length}</dd>
                <dt className="text-gray-600">Created:</dt>
                <dd className="text-gray-900">
                  {new Date(selectedSystem.created_at).toLocaleDateString()}
                </dd>
              </dl>
            </div>
          )}
        </Card>

        {/* Simulation Parameters */}
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Simulation Parameters</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Rounds: {formData.rounds}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={formData.rounds}
                onChange={(e) =>
                  setFormData({ ...formData, rounds: parseInt(e.target.value) })
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1 round</span>
                <span>20 rounds</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Defender Budget
                  <span className="text-gray-500 font-normal ml-1">(optional)</span>
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.defender_budget || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      defender_budget: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  placeholder="e.g., 100.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Total resources available for patching
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Attacker Budget
                  <span className="text-gray-500 font-normal ml-1">(optional)</span>
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.attacker_budget || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      attacker_budget: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  placeholder="e.g., 50.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Resources attacker can use for exploits
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Patch Grouping Strategy
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="strategy"
                    value="dependencies"
                    checked={formData.patch_grouping_method === 'dependencies'}
                    onChange={(e) =>
                      setFormData({ ...formData, patch_grouping_method: e.target.value })
                    }
                    className="mr-2"
                  />
                  <span className="text-sm">
                    <strong>Dependency-based</strong> (Recommended) - Groups patches based on
                    subsystem dependencies
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="strategy"
                    value="subsystem"
                    checked={formData.patch_grouping_method === 'subsystem'}
                    onChange={(e) =>
                      setFormData({ ...formData, patch_grouping_method: e.target.value })
                    }
                    className="mr-2"
                  />
                  <span className="text-sm">
                    <strong>Subsystem-based</strong> - Groups all vulnerabilities in the same
                    subsystem
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="strategy"
                    value="severity"
                    checked={formData.patch_grouping_method === 'severity'}
                    onChange={(e) =>
                      setFormData({ ...formData, patch_grouping_method: e.target.value })
                    }
                    className="mr-2"
                  />
                  <span className="text-sm">
                    <strong>Severity-based</strong> - Groups by CVSS severity levels
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Advanced Options */}
          <div className="mt-6">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
            >
              {showAdvanced ? (
                <ChevronUp className="h-4 w-4 mr-1" />
              ) : (
                <ChevronDown className="h-4 w-4 mr-1" />
              )}
              Advanced Options
            </button>

            {showAdvanced && (
              <div className="mt-4 p-4 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-600">
                  Additional configuration options will be available in future releases.
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button type="submit" size="lg" loading={runSimulationMutation.isPending}>
            <PlayCircle className="h-5 w-5 mr-2" />
            Run Simulation
          </Button>
        </div>
      </form>

      {/* Progress Modal */}
      <Modal
        isOpen={showProgressModal}
        onClose={() => {}}
        title="Running Simulation"
        showCloseButton={false}
      >
        <div className="text-center py-8">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">
            Running simulation... This may take a few moments.
          </p>
          <p className="mt-2 text-sm text-gray-500">Please do not close this window.</p>
        </div>
      </Modal>
    </div>
  );
}
