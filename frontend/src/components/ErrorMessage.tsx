import { AlertCircle, XCircle } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning';
  onRetry?: () => void;
}

export default function ErrorMessage({
  title,
  message,
  type = 'error',
  onRetry,
}: ErrorMessageProps) {
  const isError = type === 'error';

  return (
    <div
      className={`rounded-md p-4 ${
        isError ? 'bg-red-50 border border-red-200' : 'bg-yellow-50 border border-yellow-200'
      }`}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          {isError ? (
            <XCircle className="h-5 w-5 text-red-400" />
          ) : (
            <AlertCircle className="h-5 w-5 text-yellow-400" />
          )}
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3
              className={`text-sm font-medium ${
                isError ? 'text-red-800' : 'text-yellow-800'
              }`}
            >
              {title}
            </h3>
          )}
          <div
            className={`text-sm ${title ? 'mt-2' : ''} ${
              isError ? 'text-red-700' : 'text-yellow-700'
            }`}
          >
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                onClick={onRetry}
                className={`text-sm font-medium ${
                  isError
                    ? 'text-red-600 hover:text-red-500'
                    : 'text-yellow-600 hover:text-yellow-500'
                }`}
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
