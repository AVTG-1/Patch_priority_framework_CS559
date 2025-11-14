import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import SystemForm from '../components/SystemForm';

export default function SystemCreate() {
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
        <span className="text-gray-900">Create</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create New System</h1>
        <p className="mt-1 text-sm text-gray-600">
          Configure a new vulnerability system for patch prioritization
        </p>
      </div>

      {/* Form */}
      <SystemForm mode="create" />
    </div>
  );
}
