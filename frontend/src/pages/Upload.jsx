import { useState, useRef, useEffect } from 'react';
import { 
  Upload as UploadIcon,
  FileText,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  X,
  Download,
  Trash2,
  Clock
} from 'lucide-react';
import { uploadAPI } from '../services/api';

const uploadCategories = [
  {
    id: 'manual',
    name: 'Equipment Manuals',
    description: 'Upload PDF manuals for equipment',
    icon: FileText,
    accepts: '.pdf',
    color: 'green',
    endpoint: 'uploadManual'
  },
  {
    id: 'sop',
    name: 'SOP Documents',
    description: 'Upload standard operating procedures (PDF)',
    icon: FileText,
    accepts: '.pdf',
    color: 'purple',
    endpoint: 'uploadSOP'
  },
  {
    id: 'maintenance_log',
    name: 'Maintenance Logs',
    description: 'Upload maintenance log data (CSV)',
    icon: FileSpreadsheet,
    accepts: '.csv',
    color: 'blue',
    endpoint: 'uploadMaintenanceLog'
  },
  {
    id: 'failure_report',
    name: 'Failure Reports',
    description: 'Upload failure report data (CSV)',
    icon: FileSpreadsheet,
    accepts: '.csv',
    color: 'red',
    endpoint: 'uploadFailureReport'
  },
  {
    id: 'sensor_data',
    name: 'Sensor Data',
    description: 'Upload sensor reading data (CSV)',
    icon: FileSpreadsheet,
    accepts: '.csv',
    color: 'cyan',
    endpoint: 'uploadSensorData'
  },
  {
    id: 'spares',
    name: 'Spare Parts',
    description: 'Upload spare parts inventory (CSV)',
    icon: FileSpreadsheet,
    accepts: '.csv',
    color: 'yellow',
    endpoint: 'uploadSpares'
  }
];

const colorMap = {
  green: { bg: 'bg-green-500/20', border: 'border-green-500/30', text: 'text-green-400', hover: 'hover:border-green-500/50' },
  purple: { bg: 'bg-purple-500/20', border: 'border-purple-500/30', text: 'text-purple-400', hover: 'hover:border-purple-500/50' },
  blue: { bg: 'bg-blue-500/20', border: 'border-blue-500/30', text: 'text-blue-400', hover: 'hover:border-blue-500/50' },
  red: { bg: 'bg-red-500/20', border: 'border-red-500/30', text: 'text-red-400', hover: 'hover:border-red-500/50' },
  cyan: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/30', text: 'text-cyan-400', hover: 'hover:border-cyan-500/50' },
  yellow: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/30', text: 'text-yellow-400', hover: 'hover:border-yellow-500/50' },
};

function Upload() {
  const [uploading, setUploading] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [recentFiles, setRecentFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const fileInputRefs = useRef({});

  // Fetch recent files on mount
  useEffect(() => {
    fetchRecentFiles();
  }, []);

  const fetchRecentFiles = async () => {
    try {
      const response = await uploadAPI.getFiles({ limit: 20 });
      setRecentFiles(response.data);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleFileSelect = async (category, file) => {
    if (!file) return;
    
    setUploading(category);
    setUploadResult(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const uploadFn = uploadAPI[category.endpoint];
      const response = await uploadFn(formData);
      
      setUploadResult({
        success: true,
        message: `Successfully uploaded ${file.name}`,
        data: response.data
      });
      
      // Refresh file list
      fetchRecentFiles();
      
      // Clear result after 5 seconds
      setTimeout(() => setUploadResult(null), 5000);
    } catch (error) {
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || 'Upload failed'
      });
      
      // Clear result after 5 seconds
      setTimeout(() => setUploadResult(null), 5000);
    } finally {
      setUploading(null);
    }
  };

  const handleDrop = (category, e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFileSelect(category, file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDeleteFile = async (fileId) => {
    try {
      await uploadAPI.deleteFile(fileId);
      fetchRecentFiles();
    } catch (error) {
      console.error('Failed to delete file:', error);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCategoryLabel = (category) => {
    const labels = {
      manual: 'Manual',
      sop: 'SOP',
      maintenance_log: 'Maint. Log',
      failure_report: 'Failure',
      sensor_data: 'Sensor',
      spares: 'Spares'
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category) => {
    const colors = {
      manual: 'bg-green-500/20 text-green-400',
      sop: 'bg-purple-500/20 text-purple-400',
      maintenance_log: 'bg-blue-500/20 text-blue-400',
      failure_report: 'bg-red-500/20 text-red-400',
      sensor_data: 'bg-cyan-500/20 text-cyan-400',
      spares: 'bg-yellow-500/20 text-yellow-400'
    };
    return colors[category] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-heading font-bold text-industrial-text">Upload Files</h1>
        <p className="text-industrial-text-muted mt-1">Upload documents and import data</p>
      </div>

      {/* Upload Result Toast */}
      {uploadResult && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg border flex items-center gap-3 ${
          uploadResult.success 
            ? 'bg-green-900/90 border-green-500/50' 
            : 'bg-red-900/90 border-red-500/50'
        }`}>
          {uploadResult.success ? (
            <CheckCircle className="w-5 h-5 text-green-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400" />
          )}
          <span className="text-industrial-text">{uploadResult.message}</span>
          <button 
            onClick={() => setUploadResult(null)}
            className="ml-2 text-industrial-text-muted hover:text-industrial-text"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {uploadCategories.map((category) => {
          const Icon = category.icon;
          const colors = colorMap[category.color];
          const isUploading = uploading === category.id;
          
          return (
            <div 
              key={category.id}
              className={`industrial-card border-2 border-dashed ${colors.border} ${colors.hover} transition-colors`}
              onDrop={(e) => handleDrop(category, e)}
              onDragOver={handleDragOver}
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${colors.bg}`}>
                  <Icon className={`w-6 h-6 ${colors.text}`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-heading font-semibold text-industrial-text">{category.name}</h3>
                  <p className="text-sm text-industrial-text-muted mt-1">{category.description}</p>
                </div>
              </div>
              
              <div className="mt-4">
                <input
                  type="file"
                  id={`file-${category.id}`}
                  accept={category.accepts}
                  className="hidden"
                  ref={(el) => fileInputRefs.current[category.id] = el}
                  onChange={(e) => handleFileSelect(category, e.target.files[0])}
                />
                
                <button
                  onClick={() => fileInputRefs.current[category.id]?.click()}
                  disabled={isUploading}
                  className={`w-full btn-industrial flex items-center justify-center gap-2 ${
                    isUploading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {isUploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <UploadIcon className="w-4 h-4" />
                      <span>Choose File</span>
                    </>
                  )}
                </button>
                
                <p className="text-xs text-industrial-text-muted text-center mt-2">
                  Accepted: {category.accepts}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Uploads */}
      <div className="industrial-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-heading font-semibold">Recent Uploads</h2>
          <Clock className="w-5 h-5 text-industrial-text-muted" />
        </div>
        
        {loadingFiles ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          </div>
        ) : recentFiles.length === 0 ? (
          <div className="text-center py-8">
            <UploadIcon className="w-12 h-12 mx-auto text-industrial-text-muted opacity-50" />
            <p className="text-industrial-text-muted mt-3">No files uploaded yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentFiles.map((file) => (
              <div 
                key={file.file_id}
                className="flex items-center justify-between p-4 bg-industrial-bg rounded-lg group"
              >
                <div className="flex items-center gap-4">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(file.file_category)}`}>
                    {getCategoryLabel(file.file_category)}
                  </div>
                  <div>
                    <p className="font-medium text-industrial-text">{file.filename}</p>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-xs text-industrial-text-muted font-mono">
                        {formatFileSize(file.file_size)}
                      </span>
                      <span className="text-xs text-industrial-text-muted">
                        {formatDate(file.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <a
                    href={uploadAPI.downloadFile(file.file_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 text-blue-400 hover:bg-blue-500/20 rounded transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                  <button
                    onClick={() => handleDeleteFile(file.file_id)}
                    className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;