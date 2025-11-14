import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Edit, Trash2, PlayCircle, Search } from 'lucide-react';
import { systemsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Button from '../components/Button';
import Card from '../components/Card';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

export default function Systems() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [systemToDelete, setSystemToDelete] = useState<number | null>(null);

  const {
    data: systems,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['systems'],
    queryFn: systemsAPI.getSystems,
  });

  const deleteMutation = useMutation({
    mutationFn: systemsAPI.deleteSystem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systems'] });
      toast.success('System deleted successfully');
      setDeleteDialogOpen(false);
      setSystemToDelete(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete system');
    },
  });

  const handleDeleteClick = (systemId: number) => {
    setSystemToDelete(systemId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (systemToDelete) {
      deleteMutation.mutate(systemToDelete);
    }
  };

  const filteredSystems = systems?.filter((system) =>
    system.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading systems..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load systems"
        message="There was an error loading your systems. Please try again."
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Systems</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your vulnerability systems and configurations
          </p>
        </div>
        <Button onClick={() => navigate('/systems/create')}>
          <Plus className="h-4 w-4 mr-2" />
          Create System
        </Button>
      </div>

      {/* Search */}
      <Card>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search systems by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </Card>

      {/* Systems List */}
      {!filteredSystems || filteredSystems.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">
              {searchTerm ? 'No systems match your search' : 'No systems yet'}
            </p>
            {!searchTerm && (
              <Button
                className="mt-4"
                onClick={() => navigate('/systems/create')}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Your First System
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vulnerabilities
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSystems.map((system) => (
                  <tr key={system.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <div className="text-sm font-medium text-gray-900">{system.name}</div>
                        {system.description && (
                          <div className="text-sm text-gray-500 truncate max-w-md">
                            {system.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(system.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {system.vulnerabilities.length}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => navigate(`/systems/${system.id}`)}
                          className="text-indigo-600 hover:text-indigo-900"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/systems/${system.id}/edit`)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit system"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/simulations/setup/${system.id}`)}
                          className="text-green-600 hover:text-green-900"
                          title="Run simulation"
                        >
                          <PlayCircle className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(system.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete system"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
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
