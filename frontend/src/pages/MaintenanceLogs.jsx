import { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Edit2, 
  Trash2, 
  X,
  Wrench,
  ChevronLeft,
  ChevronRight,
  Filter,
  Calendar
} from 'lucide-react';
import { maintenanceLogsAPI, equipmentAPI } from '../services/api';

const severityOptions = ['low', 'medium', 'high', 'critical'];

function MaintenanceLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [equipmentNames, setEquipmentNames] = useState([]);
  
  // Filters
  const [filterEquipment, setFilterEquipment] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [currentLog, setCurrentLog] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    equipment_name: '',
    issue: '',
    action_taken: '',
    downtime_hours: 0,
    severity: 'medium',
    technician: '',
    maintenance_date: ''
  });
  
  // Delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchLogs();
    fetchEquipmentNames();
  }, [page, filterEquipment, filterSeverity]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = { 
        skip: (page - 1) * pageSize, 
        limit: pageSize 
      };
      if (filterEquipment) params.equipment_name = filterEquipment;
      if (filterSeverity) params.severity = filterSeverity;
      
      const response = await maintenanceLogsAPI.getAll(params);
      setLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEquipmentNames = async () => {
    try {
      const response = await equipmentAPI.getAll({ limit: 1000 });
      const names = [...new Set(response.data.map(e => e.equipment_name))];
      setEquipmentNames(names);
    } catch (error) {
      console.error('Failed to fetch equipment names:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleOpenModal = (mode, log = null) => {
    setModalMode(mode);
    if (mode === 'edit' && log) {
      setCurrentLog(log);
      setFormData({
        equipment_name: log.equipment_name,
        issue: log.issue,
        action_taken: log.action_taken || '',
        downtime_hours: log.downtime_hours,
        severity: log.severity,
        technician: log.technician || '',
        maintenance_date: log.maintenance_date
      });
    } else {
      setCurrentLog(null);
      setFormData({
        equipment_name: '',
        issue: '',
        action_taken: '',
        downtime_hours: 0,
        severity: 'medium',
        technician: '',
        maintenance_date: new Date().toISOString().split('T')[0]
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setCurrentLog(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalMode === 'add') {
        await maintenanceLogsAPI.create(formData);
      } else {
        await maintenanceLogsAPI.update(currentLog.log_id, formData);
      }
      handleCloseModal();
      fetchLogs();
    } catch (error) {
      console.error('Failed to save log:', error);
    }
  };

  const handleDeleteClick = (id) => {
    setDeleteId(id);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await maintenanceLogsAPI.delete(deleteId);
      setShowDeleteModal(false);
      setDeleteId(null);
      fetchLogs();
    } catch (error) {
      console.error('Failed to delete log:', error);
    }
  };

  const getSeverityBadge = (severity) => {
    const badges = {
      low: 'severity-low',
      medium: 'severity-medium',
      high: 'severity-high',
      critical: 'severity-critical'
    };
    return badges[severity] || 'severity-low';
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
          <h1 className="text-3xl font-heading font-bold text-industrial-text">Maintenance Logs</h1>
          <p className="text-industrial-text-muted mt-1">Track and manage maintenance activities</p>
        </div>
        <button
          onClick={() => handleOpenModal('add')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Log
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
          value={filterSeverity}
          onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
          className="select-industrial w-40"
        >
          <option value="">All Severity</option>
          {severityOptions.map((severity) => (
            <option key={severity} value={severity}>
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Logs Table */}
      <div className="industrial-card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <Wrench className="w-16 h-16 mx-auto text-industrial-text-muted opacity-50" />
            <p className="text-industrial-text-muted mt-4">No maintenance logs found</p>
            <button
              onClick={() => handleOpenModal('add')}
              className="btn-primary mt-4"
            >
              Add Your First Log
            </button>
          </div>
        ) : (
          <>
            <table className="industrial-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Equipment</th>
                  <th>Issue</th>
                  <th>Action Taken</th>
                  <th>Downtime</th>
                  <th>Severity</th>
                  <th>Technician</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.log_id}>
                    <td className="text-industrial-text-muted font-mono text-sm">
                      {formatDate(log.maintenance_date)}
                    </td>
                    <td className="font-medium">{log.equipment_name}</td>
                    <td className="text-industrial-text-muted max-w-[200px] truncate">
                      {log.issue}
                    </td>
                    <td className="text-industrial-text-muted max-w-[200px] truncate">
                      {log.action_taken || '-'}
                    </td>
                    <td className="font-mono text-sm">
                      {log.downtime_hours}h
                    </td>
                    <td>
                      <span className={`severity-badge ${getSeverityBadge(log.severity)}`}>
                        {log.severity}
                      </span>
                    </td>
                    <td className="text-industrial-text-muted">{log.technician || '-'}</td>
                    <td className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenModal('edit', log)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(log.log_id)}
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
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, logs.length)} of {logs.length} results
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-industrial p-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="px-4 py-2 font-mono text-sm">
                  Page {page} of {totalPages || 1}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= totalPages}
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
                {modalMode === 'add' ? 'Add Maintenance Log' : 'Edit Log'}
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
                    list="equipment-suggestions"
                  />
                  <datalist id="equipment-suggestions">
                    {equipmentNames.map((name) => (
                      <option key={name} value={name} />
                    ))}
                  </datalist>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Maintenance Date *
                  </label>
                  <input
                    type="date"
                    name="maintenance_date"
                    value={formData.maintenance_date}
                    onChange={handleInputChange}
                    className="input-industrial"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                  Issue *
                </label>
                <textarea
                  name="issue"
                  value={formData.issue}
                  onChange={handleInputChange}
                  className="input-industrial min-h-[80px]"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                  Action Taken
                </label>
                <textarea
                  name="action_taken"
                  value={formData.action_taken}
                  onChange={handleInputChange}
                  className="input-industrial min-h-[80px]"
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Severity *
                  </label>
                  <select
                    name="severity"
                    value={formData.severity}
                    onChange={handleInputChange}
                    className="select-industrial"
                    required
                  >
                    {severityOptions.map((severity) => (
                      <option key={severity} value={severity}>
                        {severity.charAt(0).toUpperCase() + severity.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">
                    Technician
                  </label>
                  <input
                    type="text"
                    name="technician"
                    value={formData.technician}
                    onChange={handleInputChange}
                    className="input-industrial"
                  />
                </div>
              </div>
              
              <div className="flex items-center gap-3 pt-4">
                <button type="submit" className="btn-primary flex-1">
                  {modalMode === 'add' ? 'Add Log' : 'Save Changes'}
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
              <h3 className="text-xl font-heading font-semibold mb-2">Delete Log</h3>
              <p className="text-industrial-text-muted mb-6">
                Are you sure you want to delete this maintenance log? This action cannot be undone.
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

export default MaintenanceLogs;