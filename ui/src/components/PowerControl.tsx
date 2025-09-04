import { useState } from 'react';
import { Power, RotateCw, X } from 'lucide-react';
import { toast } from 'react-toastify';

interface PowerControlProps {
  className?: string;
}

export function PowerControl({ className = "" }: PowerControlProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'shutdown' | 'restart' | null>(null);

  const handlePowerClick = () => {
    setModalOpen(true);
    setConfirmAction(null);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setConfirmAction(null);
  };

  const handleActionSelect = (action: 'shutdown' | 'restart') => {
    setConfirmAction(action);
  };

  const handleConfirm = async () => {
    if (!confirmAction) return;

    try {
      const endpoint = confirmAction === 'shutdown' 
        ? '/api/system/shutdown' 
        : '/api/system/restart';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ confirm: true })
      });

      if (!response.ok) {
        throw new Error(`Failed to ${confirmAction} system`);
      }

      const result = await response.json();
      
      // Show success message
      toast.success(result.message || `System ${confirmAction} initiated`);
      
      // Close modal
      handleCloseModal();
      
      // Show countdown warning
      if (result.message?.includes('Mock')) {
        toast.info('Running in mock mode - no actual system action taken');
      } else {
        toast.warning(`System will ${confirmAction} shortly...`, {
          autoClose: false,
          closeButton: false
        });
      }
    } catch (error) {
      toast.error(`Failed to ${confirmAction} system`);
      console.error(`${confirmAction} error:`, error);
    }
  };

  return (
    <>
      {/* Power button */}
      <button
        onClick={handlePowerClick}
        className={`p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors text-gray-400 hover:text-white ${className}`}
        title="System power control"
        aria-label="Power control"
      >
        <Power className="w-5 h-5" />
      </button>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black bg-opacity-75"
            onClick={handleCloseModal}
          />
          
          {/* Modal content */}
          <div className="relative bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl border border-gray-700">
            {/* Close button */}
            <button
              onClick={handleCloseModal}
              className="absolute top-3 right-3 text-gray-400 hover:text-white transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Modal body */}
            <div className="space-y-4">
              {!confirmAction ? (
                <>
                  <h2 className="text-xl font-semibold text-white">System Control</h2>
                  <p className="text-gray-300 text-sm">
                    Select an action for the Raspberry Pi system
                  </p>
                  
                  {/* Action buttons */}
                  <div className="space-y-3">
                    <button
                      onClick={() => handleActionSelect('restart')}
                      className="w-full flex items-center justify-center space-x-3 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                      <RotateCw className="w-5 h-5" />
                      <span>Restart System</span>
                    </button>
                    
                    <button
                      onClick={() => handleActionSelect('shutdown')}
                      className="w-full flex items-center justify-center space-x-3 p-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    >
                      <Power className="w-5 h-5" />
                      <span>Shutdown System</span>
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {/* Confirmation */}
                  <h2 className="text-xl font-semibold text-white">
                    Confirm {confirmAction === 'shutdown' ? 'Shutdown' : 'Restart'}
                  </h2>
                  <div className="space-y-3">
                    <p className="text-gray-300 text-sm">
                      {confirmAction === 'shutdown' 
                        ? 'This will completely power off the Raspberry Pi. You will need physical access to turn it back on.'
                        : 'This will restart the Raspberry Pi. The camera feed will be temporarily unavailable.'}
                    </p>
                    
                    <div className="p-3 bg-yellow-900 bg-opacity-50 border border-yellow-600 rounded-lg">
                      <p className="text-yellow-300 text-sm font-medium">
                        ⚠️ Warning: {confirmAction === 'shutdown' 
                          ? 'System will shut down immediately'
                          : 'System will restart immediately'}
                      </p>
                    </div>
                  </div>
                  
                  {/* Confirmation buttons */}
                  <div className="flex space-x-3">
                    <button
                      onClick={handleCloseModal}
                      className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirm}
                      className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors ${
                        confirmAction === 'shutdown'
                          ? 'bg-red-600 hover:bg-red-700'
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      Confirm {confirmAction === 'shutdown' ? 'Shutdown' : 'Restart'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}