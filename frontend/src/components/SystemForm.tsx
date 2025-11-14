import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2 } from 'lucide-react';
import type { SystemConfig, SystemConfigCreate, SystemConfigUpdate, Vulnerability } from '../types';
import Button from './Button';
import { useToast } from './Toast';
import { systemsAPI } from '../services/api';

interface SystemFormProps {
  mode: 'create' | 'edit';
  initialData?: SystemConfig;
  onSuccess?: (system: SystemConfig) => void;
}

type ConfigMode = 'json' | 'structured';

export default function SystemForm({ mode, initialData, onSuccess }: SystemFormProps) {
  const navigate = useNavigate();
  const toast = useToast();

  const [configMode, setConfigMode] = useState<ConfigMode>('structured');
  const [loading, setLoading] = useState(false);

  // Form fields
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>(
    initialData?.vulnerabilities || []
  );
  const [subsystems, setSubsystems] = useState<Array<{ name: string; importance: number }>>(
    initialData?.subsystems || []
  );
  const [dependencies, setDependencies] = useState<Record<string, string[]>>(
    initialData?.dependencies || {}
  );

  // JSON mode
  const [jsonConfig, setJsonConfig] = useState('');
  const [jsonError, setJsonError] = useState('');

  useEffect(() => {
    if (initialData && configMode === 'json') {
      setJsonConfig(JSON.stringify(initialData.vulnerabilities, null, 2));
    }
  }, [initialData, configMode]);

  const validateForm = (): boolean => {
    if (!name.trim()) {
      toast.error('System name is required');
      return false;
    }

    if (configMode === 'json') {
      try {
        const parsed = JSON.parse(jsonConfig);
        // Accept both array format or config object format
        if (!Array.isArray(parsed) && (!parsed.vulnerabilities || !Array.isArray(parsed.vulnerabilities))) {
          toast.error('JSON must be an array of vulnerabilities or an object with vulnerabilities array');
          return false;
        }
      } catch (e) {
        toast.error('Invalid JSON format');
        return false;
      }
    } else {
      if (vulnerabilities.length === 0) {
        toast.error('At least one vulnerability is required');
        return false;
      }

      for (const vuln of vulnerabilities) {
        if (!vuln.vuln_id || !vuln.affected_component) {
          toast.error('All vulnerabilities must have ID and affected component');
          return false;
        }
        if (vuln.cvss_score < 0 || vuln.cvss_score > 10) {
          toast.error('CVSS scores must be between 0 and 10');
          return false;
        }
      }
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      let vulnsToSubmit = vulnerabilities;

      if (configMode === 'json') {
        const parsed = JSON.parse(jsonConfig);
        // Handle both formats: array or config object
        if (Array.isArray(parsed)) {
          vulnsToSubmit = parsed;
        } else if (parsed.vulnerabilities) {
          vulnsToSubmit = parsed.vulnerabilities;
        }
      }

      // Create config_json string as expected by backend
      const configData: any = {
        vulnerabilities: vulnsToSubmit,
      };

      // Add subsystems if they exist
      if (subsystems.length > 0) {
        configData.subsystems = subsystems;
      }

      // Add dependencies if they exist
      if (Object.keys(dependencies).length > 0) {
        configData.dependencies = dependencies;
      }

      const config_json = JSON.stringify(configData);

      const systemData = {
        name: name.trim(),
        config_json: config_json,
      };

      let result: SystemConfig;

      if (mode === 'create') {
        result = await systemsAPI.createSystem(systemData as SystemConfigCreate);
        toast.success('System created successfully!');
      } else {
        result = await systemsAPI.updateSystem(
          initialData!.id,
          systemData as SystemConfigUpdate
        );
        toast.success('System updated successfully!');
      }

      if (onSuccess) {
        onSuccess(result);
      }

      navigate(`/systems/${result.id}`);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || `Failed to ${mode} system. Please try again.`;
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const addVulnerability = () => {
    setVulnerabilities([
      ...vulnerabilities,
      {
        vuln_id: '',
        cvss_score: 5.0,
        affected_component: '',
        description: '',
        dependencies: [],
      },
    ]);
  };

  const removeVulnerability = (index: number) => {
    setVulnerabilities(vulnerabilities.filter((_, i) => i !== index));
  };

  const updateVulnerability = (index: number, field: keyof Vulnerability, value: any) => {
    const updated = [...vulnerabilities];
    updated[index] = { ...updated[index], [field]: value };
    setVulnerabilities(updated);
  };

  const addSubsystem = () => {
    setSubsystems([...subsystems, { name: '', importance: 0.5 }]);
  };

  const removeSubsystem = (index: number) => {
    const subsystemName = subsystems[index].name;
    setSubsystems(subsystems.filter((_, i) => i !== index));

    // Remove dependencies related to this subsystem
    if (subsystemName) {
      const newDeps = { ...dependencies };
      delete newDeps[subsystemName];
      Object.keys(newDeps).forEach((key) => {
        newDeps[key] = newDeps[key].filter((dep) => dep !== subsystemName);
      });
      setDependencies(newDeps);
    }
  };

  const updateSubsystem = (index: number, field: 'name' | 'importance', value: any) => {
    const updated = [...subsystems];
    updated[index] = { ...updated[index], [field]: value };
    setSubsystems(updated);
  };

  const addDependency = (subsystemName: string, dependency: string) => {
    const currentDeps = dependencies[subsystemName] || [];
    if (!currentDeps.includes(dependency)) {
      setDependencies({
        ...dependencies,
        [subsystemName]: [...currentDeps, dependency],
      });
    }
  };

  const removeDependency = (subsystemName: string, dependency: string) => {
    const currentDeps = dependencies[subsystemName] || [];
    setDependencies({
      ...dependencies,
      [subsystemName]: currentDeps.filter((dep) => dep !== dependency),
    });
  };

  const validateJson = () => {
    try {
      const parsed = JSON.parse(jsonConfig);
      // Accept both array of vulnerabilities or config object
      if (Array.isArray(parsed)) {
        // It's a vulnerabilities array - valid
        setJsonError('');
        toast.success('JSON is valid!');
      } else if (parsed.vulnerabilities && Array.isArray(parsed.vulnerabilities)) {
        // It's a config object with vulnerabilities - valid
        setJsonError('');
        toast.success('JSON is valid!');
      } else {
        setJsonError('JSON must be either an array of vulnerabilities or an object with a vulnerabilities array');
      }
    } catch (e: any) {
      setJsonError(e.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>

        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              System Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g., Production Web Server"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Optional description of the system"
            />
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Vulnerability Configuration</h3>

        {/* Mode Toggle */}
        <div className="flex gap-4 mb-6">
          <button
            type="button"
            onClick={() => setConfigMode('structured')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              configMode === 'structured'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Structured Form
          </button>
          <button
            type="button"
            onClick={() => setConfigMode('json')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              configMode === 'json'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            JSON Editor
          </button>
        </div>

        {/* JSON Editor Mode */}
        {configMode === 'json' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vulnerabilities JSON
              </label>
              <textarea
                value={jsonConfig}
                onChange={(e) => {
                  setJsonConfig(e.target.value);
                  setJsonError('');
                }}
                rows={15}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder={`[\n  {\n    "vuln_id": "CVE-2024-1234",\n    "cvss_score": 7.5,\n    "affected_component": "web-server",\n    "description": "SQL Injection vulnerability"\n  }\n]`}
              />
              {jsonError && <p className="mt-2 text-sm text-red-600">{jsonError}</p>}
            </div>
            <Button type="button" variant="secondary" onClick={validateJson}>
              Validate JSON
            </Button>
          </div>
        )}

        {/* Structured Form Mode */}
        {configMode === 'structured' && (
          <div className="space-y-4">
            {vulnerabilities.map((vuln, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4 relative">
                <button
                  type="button"
                  onClick={() => removeVulnerability(index)}
                  className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                  aria-label="Remove vulnerability"
                >
                  <Trash2 className="h-4 w-4" />
                </button>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Vulnerability ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={vuln.vuln_id}
                      onChange={(e) => updateVulnerability(index, 'vuln_id', e.target.value)}
                      required
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="CVE-2024-1234 or COMM-2024-0001"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      CVSS Score <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.1"
                      value={vuln.cvss_score}
                      onChange={(e) =>
                        updateVulnerability(index, 'cvss_score', parseFloat(e.target.value))
                      }
                      required
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Affected Component <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={vuln.affected_component}
                      onChange={(e) =>
                        updateVulnerability(index, 'affected_component', e.target.value)
                      }
                      required
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="e.g., web-server, database"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <input
                      type="text"
                      value={vuln.description || ''}
                      onChange={(e) => updateVulnerability(index, 'description', e.target.value)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Brief description"
                    />
                  </div>
                </div>
              </div>
            ))}

            <Button type="button" variant="outline" onClick={addVulnerability}>
              <Plus className="h-4 w-4 mr-2" />
              Add Vulnerability
            </Button>

            {/* Subsystems Section */}
            <div className="mt-8 pt-8 border-t border-gray-200">
              <h4 className="text-md font-medium text-gray-900 mb-4">
                Subsystems (Optional)
              </h4>
              <p className="text-sm text-gray-600 mb-4">
                Define system components with their importance scores for game-theoretic simulation
              </p>

              {subsystems.map((subsystem, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-4 relative mb-3">
                  <button
                    type="button"
                    onClick={() => removeSubsystem(index)}
                    className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                    aria-label="Remove subsystem"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Subsystem Name
                      </label>
                      <input
                        type="text"
                        value={subsystem.name}
                        onChange={(e) => updateSubsystem(index, 'name', e.target.value)}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="e.g., web-server, database"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Importance (0.0 - 1.0)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={subsystem.importance}
                        onChange={(e) =>
                          updateSubsystem(index, 'importance', parseFloat(e.target.value))
                        }
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>
                </div>
              ))}

              <Button type="button" variant="outline" onClick={addSubsystem}>
                <Plus className="h-4 w-4 mr-2" />
                Add Subsystem
              </Button>
            </div>

            {/* Dependencies Section */}
            {subsystems.length > 1 && (
              <div className="mt-8 pt-8 border-t border-gray-200">
                <h4 className="text-md font-medium text-gray-900 mb-4">
                  Subsystem Dependencies (Optional)
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  Define which subsystems depend on others (e.g., web-server depends on database)
                </p>

                {subsystems.map((subsystem) => {
                  if (!subsystem.name) return null;
                  const currentDeps = dependencies[subsystem.name] || [];
                  const availableDeps = subsystems.filter(
                    (s) => s.name && s.name !== subsystem.name
                  );

                  return (
                    <div key={subsystem.name} className="mb-4 p-4 bg-gray-50 rounded-md">
                      <label className="block text-sm font-medium text-gray-900 mb-2">
                        {subsystem.name} depends on:
                      </label>

                      <div className="flex flex-wrap gap-2 mb-2">
                        {currentDeps.map((dep) => (
                          <span
                            key={dep}
                            className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-indigo-100 text-indigo-800"
                          >
                            {dep}
                            <button
                              type="button"
                              onClick={() => removeDependency(subsystem.name, dep)}
                              className="ml-2 text-indigo-600 hover:text-indigo-800"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>

                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            addDependency(subsystem.name, e.target.value);
                            e.target.value = '';
                          }
                        }}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        defaultValue=""
                      >
                        <option value="">Add dependency...</option>
                        {availableDeps.map((dep) => (
                          <option
                            key={dep.name}
                            value={dep.name}
                            disabled={currentDeps.includes(dep.name)}
                          >
                            {dep.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={() => navigate(-1)}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {mode === 'create' ? 'Create System' : 'Update System'}
        </Button>
      </div>
    </form>
  );
}
