import { useState, useEffect } from 'react';
import { 
  Upload, 
  Search, 
  Trash2, 
  RefreshCw, 
  FileText,
  FileSpreadsheet,
  BookOpen,
  AlertTriangle,
  Wrench,
  Clock,
  Database,
  Plus,
  X,
  CheckCircle,
  XCircle,
  Loader,
  RefreshCw as SyncIcon,
  Filter
} from 'lucide-react';
import { 
  uploadDocument, 
  searchDocuments, 
  deleteDocumentIndex, 
  getIndexStats, 
  importMaintenanceLogs,
  importFailureReports,
  reindexDocuments
} from '../services/ragApi';

const documentTypes = [
  { id: 'manual', label: 'Equipment Manual', icon: BookOpen, color: 'green' },
  { id: 'sop', label: 'SOP Document', icon: FileText, color: 'purple' },
  { id: 'maintenance_log', label: 'Maintenance Log', icon: Wrench, color: 'blue' },
  { id: 'failure_report', label: 'Failure Report', icon: AlertTriangle, color: 'red' },
  { id: 'sensor_data', label: 'Sensor Data', icon: Database, color: 'cyan' },
  { id: 'other', label: 'Other', icon: FileText, color: 'gray' }
];

const colorMap = {
  green: { bg: 'bg-green-500/20', border: 'border-green-500/30', text: 'text-green-400', icon: 'text-green-400' },
  purple: { bg: 'bg-purple-500/20', border: 'border-purple-500/30', text: 'text-purple-400', icon: 'text-purple-400' },
  blue: { bg: 'bg-blue-500/20', border: 'border-blue-500/30', text: 'text-blue-400', icon: 'text-blue-400' },
  red: { bg: 'bg-red-500/20', border: 'border-red-500/30', text: 'text-red-400', icon: 'text-red-400' },
  cyan: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/30', text: 'text-cyan-400', icon: 'text-cyan-400' },
  gray: { bg: 'bg-gray-500/20', border: 'border-gray-500/30', text: 'text-gray-400', icon: 'text-gray-400' }
};

const DocumentCard = ({ doc, onDelete, onReindex }) => {
  const typeInfo = documentTypes.find(t => t.id === doc.document_type) || documentTypes[5];
  const TypeIcon = typeInfo.icon;
  const colors = colorMap[typeInfo.color] || colorMap.gray;
  
  return (
    <div className={`industrial-card border ${colors.border}`}>
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${colors.bg}`}>
          <TypeIcon className={`w-6 h-6 ${colors.icon}`} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-heading font-semibold text-industrial-text truncate">
            {doc.document_name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
              {typeInfo.label}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-industrial-text-muted">
            <span className="flex items-center gap-1">
              <Database className="w-3 h-3" />
              {doc.total_chunks || doc.total_chunks || 0} chunks
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onReindex(doc)}
            className="p-2 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
            title="Re-index document"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(doc)}
            className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors"
            title="Delete document"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

const UploadModal = ({ isOpen, onClose, onUpload }) => {
  const [file, setFile] = useState(null);
  const [documentName, setDocumentName] = useState('');
  const [documentType, setDocumentType] = useState('manual');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState(null);
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setDocumentName(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }
  };
  
  const handleUpload = async () => {
    if (!file || !documentName) return;
    
    setUploading(true);
    setStatus(null);
    
    try {
      // Step 1: Upload via doc-intelligence pipeline
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResp = await fetch('http://localhost:8000/api/doc-intelligence/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadResp.ok) {
        const err = await uploadResp.json();
        throw new Error(err.detail || 'Upload failed');
      }
      
      const uploadResult = await uploadResp.json();
      const docId = uploadResult.doc_id;
      
      setStatus({ type: 'info', message: 'Uploaded. AI is analysing document...' });
      
      // Step 2: Process (AI analysis + chunking + vector store indexing)
      const processResp = await fetch(`http://localhost:8000/api/doc-intelligence/process/${docId}`, {
        method: 'POST',
      });
      
      if (!processResp.ok) {
        const err = await processResp.json();
        throw new Error(err.detail || 'Processing failed');
      }
      
      const processResult = await processResp.json();
      
      setStatus({
        type: 'success',
        message: `✅ Indexed! ${processResult.chunk_count} chunks · ${processResult.equipment_name || 'Equipment detected'}`
      });
      
      if (onUpload) onUpload(processResult);
      
      setTimeout(() => { onClose(); resetForm(); }, 2000);
      
    } catch (error) {
      setStatus({ type: 'error', message: error.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };
  
  const resetForm = () => {
    setFile(null);
    setDocumentName('');
    setDocumentType('manual');
    setDescription('');
    setStatus(null);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="industrial-card w-full max-w-lg mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-heading font-semibold">Upload Document</h2>
          <button onClick={onClose} className="text-industrial-text-muted hover:text-industrial-text">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {status && (
          <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
            status.type === 'success' ? 'bg-green-900/30 border border-green-500/30' :
            status.type === 'info'    ? 'bg-blue-900/30 border border-blue-500/30' :
            'bg-red-900/30 border border-red-500/30'
          }`}>
            {status.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
            ) : status.type === 'info' ? (
              <Loader className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            )}
            <span className="text-sm">{status.message}</span>
          </div>
        )}
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-industrial-text-muted mb-1">
              Select File (PDF, TXT, CSV)
            </label>
            <input
              type="file"
              accept=".pdf,.txt,.csv"
              onChange={handleFileChange}
              className="input-industrial"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-industrial-text-muted mb-1">
              Document Name *
            </label>
            <input
              type="text"
              value={documentName}
              onChange={(e) => setDocumentName(e.target.value)}
              className="input-industrial"
              placeholder="Enter document name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-industrial-text-muted mb-1">
              Document Type *
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="select-industrial"
            >
              {documentTypes.map((type) => (
                <option key={type.id} value={type.id}>{type.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-industrial-text-muted mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-industrial min-h-[80px]"
              placeholder="Optional description"
            />
          </div>
          
          <div className="flex items-center gap-3 pt-4">
            <button
              onClick={handleUpload}
              disabled={!file || !documentName || uploading}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Index</span>
                </>
              )}
            </button>
            <button onClick={onClose} className="btn-industrial flex-1">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [indexStats, setIndexStats] = useState(null);
  const [importing, setImporting] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  
  useEffect(() => {
    loadIndexStats();
    loadDocuments();
  }, []);
  
  const loadIndexStats = async () => {
    try {
      const stats = await getIndexStats();
      setIndexStats(stats);
    } catch (error) {
      console.error('Failed to load index stats:', error);
    }
  };
  
  const loadDocuments = async () => {
    setLoading(true);
    try {
      // Search for documents
      const results = await searchDocuments(
        searchQuery || 'document',
        filterType || 'all',
        50
      );
      
      // Transform results to document format
      const docs = results.results.map(r => ({
        document_name: r.source_document,
        document_type: r.document_type,
        total_chunks: 1,
        chunk_id: r.chunk_id,
        metadata: r.metadata
      }));
      
      // Remove duplicates
      const uniqueDocs = docs.reduce((acc, doc) => {
        const exists = acc.find(d => d.document_name === doc.document_name);
        if (!exists) {
          acc.push(doc);
        }
        return acc;
      }, []);
      
      setDocuments(uniqueDocs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearch = () => {
    loadDocuments();
  };
  
  const handleDelete = async (doc) => {
    if (!confirm(`Delete all chunks from "${doc.document_name}"?`)) return;
    
    try {
      await deleteDocumentIndex(doc.document_name);
      loadDocuments();
      loadIndexStats();
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };
  
  const handleReindex = async (doc) => {
    setReindexing(true);
    try {
      await reindexDocuments(doc.chunk_id);
      loadDocuments();
      loadIndexStats();
    } catch (error) {
      console.error('Failed to reindex document:', error);
    } finally {
      setReindexing(false);
    }
  };
  
  const handleImportLogs = async () => {
    setImporting(true);
    try {
      const result = await importMaintenanceLogs(100);
      console.log('Imported maintenance logs:', result);
      loadDocuments();
      loadIndexStats();
    } catch (error) {
      console.error('Failed to import maintenance logs:', error);
    } finally {
      setImporting(false);
    }
  };
  
  const handleImportReports = async () => {
    setImporting(true);
    try {
      const result = await importFailureReports(100);
      console.log('Imported failure reports:', result);
      loadDocuments();
      loadIndexStats();
    } catch (error) {
      console.error('Failed to import failure reports:', error);
    } finally {
      setImporting(false);
    }
  };
  
  const handleUploadComplete = (result) => {
    loadDocuments();
    loadIndexStats();
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold text-industrial-text">Document Library</h1>
          <p className="text-industrial-text-muted mt-1">Manage and search maintenance documents</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Upload Document
        </button>
      </div>

      {/* Index Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="industrial-card">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-orange-500/20">
              <Database className="w-6 h-6 text-orange-500" />
            </div>
            <div>
              <p className="text-xs text-industrial-text-muted">Total Documents</p>
              <p className="text-2xl font-heading font-bold">{indexStats?.total_documents || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="industrial-card">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-blue-500/20">
              <FileText className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-industrial-text-muted">Total Chunks</p>
              <p className="text-2xl font-heading font-bold">{indexStats?.total_chunks || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="industrial-card">
          <button
            onClick={handleImportLogs}
            disabled={importing}
            className="w-full flex items-center gap-3 hover:bg-industrial-bg rounded-lg p-3 transition-colors"
          >
            <div className="p-3 rounded-lg bg-green-500/20">
              <Wrench className="w-6 h-6 text-green-400" />
            </div>
            <div className="text-left">
              <p className="text-xs text-industrial-text-muted">Import Maintenance Logs</p>
              <p className="text-sm text-industrial-text">
                {importing ? 'Importing...' : 'From Database'}
              </p>
            </div>
          </button>
        </div>
        
        <div className="industrial-card">
          <button
            onClick={handleImportReports}
            disabled={importing}
            className="w-full flex items-center gap-3 hover:bg-industrial-bg rounded-lg p-3 transition-colors"
          >
            <div className="p-3 rounded-lg bg-red-500/20">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <div className="text-left">
              <p className="text-xs text-industrial-text-muted">Import Failure Reports</p>
              <p className="text-sm text-industrial-text">
                {importing ? 'Importing...' : 'From Database'}
              </p>
            </div>
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-industrial-text-muted" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="input-industrial pl-10"
          />
        </div>
        
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); loadDocuments(); }}
          className="select-industrial w-48"
        >
          <option value="">All Types</option>
          {documentTypes.map((type) => (
            <option key={type.id} value={type.id}>{type.label}</option>
          ))}
        </select>
        
        <button onClick={handleSearch} className="btn-industrial">
          Search
        </button>
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {loading ? (
          <div className="col-span-2 flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="col-span-2 text-center py-12">
            <FileText className="w-16 h-16 mx-auto text-industrial-text-muted opacity-50" />
            <p className="text-industrial-text-muted mt-4">No documents found</p>
            <p className="text-sm text-industrial-text-muted mt-2">
              Upload documents or import from database to get started
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn-primary mt-4"
            >
              Upload Your First Document
            </button>
          </div>
        ) : (
          documents.map((doc, i) => (
            <DocumentCard
              key={i}
              doc={doc}
              onDelete={handleDelete}
              onReindex={handleReindex}
            />
          ))
        )}
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUploadComplete}
      />
    </div>
  );
}

export default DocumentLibrary;