import { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Edit2, 
  Trash2, 
  X,
  AlertTriangle,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { failureReportsAPI } from '../services/api';

const failureTypes = [
  'Mechanical Failure',
  'Electrical Failure',
  'Hydraulic Failure',
  'Overheating',
  'Bearing Failure',
  'Motor Failure',
  'Sensor Malfunction',
  'Structural Failure',
  'Control System Failure',
  'Other'
];

function FailureReports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [filterEquipment, setFilterEquipment] = useState('');
  const [filterType, setFilterType] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [currentReport, setCurrentReport] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    equipment_name: '',
    failure_type: '',
    root_cause: '',
    downtime_hours: 0,
    report_date: ''
  });
  
  // Delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchReports();
  }, [page, filterEquipment, filterType]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const params = { 
        skip: (page - 1) * pageSize, 
        limit: pageSize 
      };
      if (filterEquipment) params.equipment_name = filterEquipment;
      if (filterType) params.failure_type = filterType;
      
      const response = await failureReportsAPI.getAll(params);
      setReports(response.data);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleOpenModal = (mode, report = null) => {
    setModalMode(mode);
    if (mode === 'edit' && report) {
      setCurrentReport(report);
      setFormData({
        equipment_name: report.equipment_name,
        failure_type: report.failure_type,
        root_cause: report.root_cause || '',
        downtime_hours: report.downtime_hours,
        report_date: report.report_date
      });
    } else {
      setCurrentReport(null);
      setFormData({
        equipment_name: '',
        failure_type: '',
        root_cause: '',
        downtime_hours: 0,
        report_date: new Date().toISOString().split('T')[0]
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setCurrentReport(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalMode === 'add') {
        await failureReportsAPI.create(formData);
      } else {
        await failureReportsAPI.update(currentReport.report_id, formData);
      }
      handleCloseModal();
      fetchReports();
    } catch (error) {
      console.error('Failed to save report:', error);
    }
  };

  const handleDeleteClick = (id) => {
    setDeleteId(id);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await failureReportsAPI.delete(deleteId);
      setShowDeleteModal(false);
      setDeleteId(null);
      fetchReports();
    } catch (error) {
      console.error('Failed to delete report:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold text-industrial-text">Failure Reports</h1>
          <p className="text-industrial-text-muted mt-1">Track and analyze equipment failures</p>
        </div>
        <button
          onClick={() => handleOpenModal('add')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Report
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-industrial-text-muted" />
          <input
            type="text"
            placeholder="Filter by equipment..."
            value={filterEquipment}
            onChange={(e) => { setFilterEquipment(e.target.value); setPage(1); }}
            className="input-industrial pl-10"
          />
        </div>
        
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
          className="select-industrial w-48"
        >
          <option value="">All Failure Types</option>
          {failureTypes.map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
      </div>

      {/* Reports Table */}
      <div className="industrial-card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <AlertTriangle className="w-16 h-16 mx-auto text-industrial-text-muted opacity-50" />
            <p className="text-industrial-text-muted mt-4">No failure reports found</p>
            <button
              onClick={() => handleOpenModal('add')}
              className="btn-primary mt-4"
            >
              Add Your First Report
            </button>
          </div>
        ) : (
          <>
            <table className="industrial-table">
              <thead>
                <tr>
                  <th>Report Date</th>
                  <th>Equipment</th>
                  <th>Failure Type</th>
                  <th>Root Cause</th>
                  <th>Downtime</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.report_id}>
                    <td className="text-industrial-text-muted font-mono text-sm">
                      {formatDate(report.report_date)}
                    </td>
                    <td className="font-medium">{report.equipment_name}</td>
                    <td>
                      <span className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs font-medium">
                        {report.failure_type}
                      </span>
                    </td>
                    <td className="text-industrial-text-muted max-w-[250px] truncate">
                      {report.root_cause || '-'}
                    </td>
                    <td className="font-mono text-red-400">
                      {report.downtime_hours}h
                    </td>
                    <td className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenModal('edit', report)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(report.report_id)}
                          className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {/* Pagination */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-industrial-border">
              <span className="text-sm text-industrial-text-muted">
                Showing {reports.length} records
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-industrial p-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="px-4 py-2 font-mono text-sm">Page {page}</span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={reports.length < pageSize}
                  className="btn-industrial p-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 overflow-y-auto py-8">
          <div className="industrial-card w-full max-w-2xl mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-heading font-semibold">
                {modalMode === 'add' ? 'Add Failure Report' : 'Edit Report'}
              </h2>
              <button onClick={handleCloseModal} className="text-industrial-text-muted hover:text-industrial-text">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Equipment Name *
                  </label>
                  <input
                    type="text"
                    name="equipment_name"
                    value={formData.equipment_name}
                    onChange={handleInputChange}
                    className="input-industrial"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Report Date *
                  </label>
                  <input
                    type="date"
                    name="report_date"
                    value={formData.report_date}
                    onChange={handleInputChange}
                    className="input-industrial"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Failure Type *
                  </label>
                  <select
                    name="failure_type"
                    value={formData.failure_type}
                    onChange={handleInputChange}
                    className="select-industrial"
                    required
                  >
                    <option value="">Select type...</option>
                    {failureTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Downtime (hours)
                  </label>
                  <input
                    type="number"
                    name="downtime_hours"
                    value={formData.downtime_hours}
                    onChange={handleInputChange}
                    className="input-industrial"
                    min="0"
                    step="0.5"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                  Root Cause Analysis
                </label>
                <textarea
                  name="root_cause"
                  value={formData.root_cause}
                  onChange={handleInputChange}
                  className="input-industrial min-h-[120px]"
                  placeholder="Describe the root cause of the failure..."
                />
              </div>
              
              <div className="flex items-center gap-3 pt-4">
                <button type="submit" className="btn-primary flex-1">
                  {modalMode === 'add' ? 'Add Report' : 'Save Changes'}
                </button>
                <button type="button" onClick={handleCloseModal} className="btn-industrial flex-1">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="industrial-card w-full max-w-md mx-4">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-xl font-heading font-semibold mb-2">Delete Report</h3>
              <p className="text-industrial-text-muted mb-6">
                Are you sure you want to delete this failure report? This action cannot be undone.
              </p>
              <div className="flex items-center gap-3">
                <button onClick={handleDeleteConfirm} className="btn-primary flex-1 bg-red-600 hover:bg-red-500">
                  Delete
                </button>
                <button onClick={() => setShowDeleteModal(false)} className="btn-industrial flex-1">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FailureReports;