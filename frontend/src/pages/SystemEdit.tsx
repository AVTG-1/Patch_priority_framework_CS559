import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronRight } from 'lucide-react';
import { systemsAPI } from '../services/api';
import SystemForm from '../components/SystemForm';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function SystemEdit() {
  const { id } = useParams<{ id: string }>();
  const systemId = parseInt(id!);

  const {
    data: system,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['system', systemId],
    queryFn: () => systemsAPI.getSystem(systemId),
  });

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading system..." />;
  }

  if (error || !system) {
    return (
      <ErrorMessage
        title="Failed to load system"
        message="The system could not be loaded. Please try again."
        onRetry={refetch}
      />
    );
  }

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
        <Link to={`/systems/${systemId}`} className="hover:text-gray-700">
          {system.name}
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <span className="text-gray-900">Edit</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Edit System: {system.name}</h1>
        <p className="mt-1 text-sm text-gray-600">Update your system configuration</p>
      </div>

      {/* Form */}
      <SystemForm mode="edit" initialData={system} />
    </div>
  );
}
