import { useState, useEffect } from 'react';
import { X, Trash2 } from 'lucide-react';

interface Photo {
  filename: string;
  timestamp: string;
  displayDate: string;
  fileSize: number;
  displaySize: string;
  path: string;
}

interface PhotoGalleryProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PhotoGallery({ isOpen, onClose }: PhotoGalleryProps) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Photo | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch photos when gallery opens
  useEffect(() => {
    if (isOpen) {
      fetchPhotos();
    }
  }, [isOpen]);

  const fetchPhotos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/photos');
      const data = await response.json();
      
      if (data.status === 'success') {
        setPhotos(data.photos);
      } else {
        setError(data.message || 'Failed to load photos');
      }
    } catch (err) {
      console.error('Failed to fetch photos:', err);
      setError('Failed to load photos');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePhoto = async (photo: Photo) => {
    setIsDeleting(true);
    try {
      const response = await fetch(`/api/photos/${photo.filename}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        // Remove photo from list
        setPhotos(prevPhotos => prevPhotos.filter(p => p.filename !== photo.filename));
        // Close modals if needed
        setDeleteConfirm(null);
        if (selectedPhoto?.filename === photo.filename) {
          setSelectedPhoto(null);
        }
      } else {
        alert(`Failed to delete photo: ${data.message}`);
      }
    } catch (err) {
      console.error('Failed to delete photo:', err);
      alert('Failed to delete photo');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, photo: Photo) => {
    e.stopPropagation(); // Prevent opening the photo viewer
    setDeleteConfirm(photo);
  };

  // Handle escape key to close gallery
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (selectedPhoto) {
          setSelectedPhoto(null);
        } else {
          onClose();
        }
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, selectedPhoto, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-900 bg-opacity-80">
        <h2 className="text-xl font-semibold text-white">
          Photos ({photos.length})
        </h2>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
          aria-label="Close gallery"
        >
          <X className="w-6 h-6 text-white" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-300">Loading photos...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={fetchPhotos}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!loading && !error && photos.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400">No photos yet. Take a photo to get started!</p>
          </div>
        )}

        {!loading && !error && photos.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {photos.map((photo) => (
              <div
                key={photo.filename}
                className="relative group cursor-pointer"
                onClick={() => setSelectedPhoto(photo)}
              >
                <img
                  src={photo.path}
                  alt={photo.filename}
                  className="w-full h-32 object-cover rounded-lg group-hover:opacity-90 transition-opacity"
                  loading="lazy"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2 rounded-b-lg">
                  <p className="text-xs text-white truncate">{photo.displayDate}</p>
                  <p className="text-xs text-gray-300">{photo.displaySize}</p>
                </div>
                {/* Delete button */}
                <button
                  onClick={(e) => handleDeleteClick(e, photo)}
                  className="absolute top-2 right-2 p-1.5 bg-red-600 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700"
                  aria-label="Delete photo"
                >
                  <Trash2 className="w-4 h-4 text-white" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Full-size photo viewer */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black bg-opacity-95 z-60 flex items-center justify-center p-4"
          onClick={() => setSelectedPhoto(null)}
        >
          <div className="relative max-w-full max-h-full">
            <img
              src={selectedPhoto.path}
              alt={selectedPhoto.filename}
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="absolute top-4 right-4 flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirm(selectedPhoto);
                }}
                className="p-2 bg-red-600 rounded-full hover:bg-red-700 transition-colors"
                aria-label="Delete photo"
              >
                <Trash2 className="w-5 h-5 text-white" />
              </button>
              <button
                onClick={() => setSelectedPhoto(null)}
                className="p-2 bg-gray-800 rounded-full hover:bg-gray-700 transition-colors"
                aria-label="Close viewer"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
            <div className="absolute bottom-4 left-4 bg-gray-900 bg-opacity-80 p-3 rounded-lg">
              <p className="text-white text-sm">{selectedPhoto.displayDate}</p>
              <p className="text-gray-300 text-xs">{selectedPhoto.filename}</p>
              <p className="text-gray-400 text-xs">{selectedPhoto.displaySize}</p>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation dialog */}
      {deleteConfirm && (
        <div
          className="fixed inset-0 bg-black bg-opacity-80 z-[70] flex items-center justify-center p-4"
          onClick={() => setDeleteConfirm(null)}
        >
          <div
            className="bg-gray-800 rounded-lg p-6 max-w-sm w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-white text-lg font-semibold mb-4">
              Delete Photo?
            </h3>
            <p className="text-gray-300 mb-6">
              Are you sure you want to delete "{deleteConfirm.filename}"? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeletePhoto(deleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}