import { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Edit2, 
  Trash2, 
  X,
  Package,
  ChevronLeft,
  ChevronRight,
  AlertCircle
} from 'lucide-react';

const API = 'http://localhost:8000';

function SpareParts() {
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [currentPart, setCurrentPart] = useState(null);
  const [formData, setFormData] = useState({
    part_name: '', part_number: '', category: 'General',
    stock_quantity: 0, minimum_stock: 5, reorder_level: 3,
    unit_cost: 0, lead_time_days: 0, supplier: '', location: ''
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => { fetchParts(); }, [page, searchTerm, lowStockOnly]);

  const fetchParts = async () => {
    try {
      setLoading(true);
      // Read from procurement spares (has preloaded steel plant parts)
      const res = await fetch(`${API}/api/procurement/spares`);
      const json = await res.json();
      let data = json.parts || [];

      // Apply local filters
      if (searchTerm) {
        data = data.filter(p =>
          p.part_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (p.part_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (p.supplier || '').toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      if (lowStockOnly) {
        data = data.filter(p => p.stock_quantity <= p.minimum_stock || p.status !== 'in_stock');
      }
      setParts(data);
    } catch (error) {
      console.error('Failed to fetch parts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleOpenModal = (mode, part = null) => {
    setModalMode(mode);
    if (mode === 'edit' && part) {
      setCurrentPart(part);
      setFormData({
        part_name: part.part_name,
        part_number: part.part_number || '',
        category: part.category || 'General',
        stock_quantity: part.stock_quantity,
        minimum_stock: part.minimum_stock ?? 5,
        reorder_level: part.reorder_level ?? 3,
        unit_cost: part.unit_cost ?? 0,
        lead_time_days: part.lead_time_days,
        supplier: part.supplier || '',
        location: part.location || ''
      });
    } else {
      setCurrentPart(null);
      setFormData({
        part_name: '', part_number: '', category: 'General',
        stock_quantity: 0, minimum_stock: 5, reorder_level: 3,
        unit_cost: 0, lead_time_days: 0, supplier: '', location: ''
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => { setShowModal(false); setCurrentPart(null); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalMode === 'add') {
        await fetch(`${API}/api/procurement/spares`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            part_name:      formData.part_name,
            part_number:    formData.part_number || formData.part_name.replace(/\s+/g, '-').toUpperCase().slice(0, 10),
            category:       formData.category || 'General',
            stock_quantity: Number(formData.stock_quantity),
            minimum_stock:  Number(formData.minimum_stock),
            reorder_level:  Number(formData.reorder_level),
            unit_cost:      Number(formData.unit_cost),
            lead_time_days: Number(formData.lead_time_days),
            supplier:       formData.supplier,
            location:       formData.location,
          })
        });
      } else {
        await fetch(`${API}/api/procurement/spares/${currentPart.part_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            part_name:      formData.part_name,
            part_number:    formData.part_number,
            category:       formData.category,
            stock_quantity: Number(formData.stock_quantity),
            minimum_stock:  Number(formData.minimum_stock),
            reorder_level:  Number(formData.reorder_level),
            unit_cost:      Number(formData.unit_cost),
            lead_time_days: Number(formData.lead_time_days),
            supplier:       formData.supplier,
            location:       formData.location,
          })
        });
      }
      handleCloseModal();
      fetchParts();
    } catch (error) {
      console.error('Failed to save part:', error);
    }
  };

  const handleDeleteClick = (id) => { setDeleteId(id); setShowDeleteModal(true); };

  const handleDeleteConfirm = async () => {
    try {
      await fetch(`${API}/api/procurement/spares/${deleteId}`, { method: 'DELETE' });
      setShowDeleteModal(false);
      setDeleteId(null);
      fetchParts();
    } catch (error) {
      console.error('Failed to delete part:', error);
    }
  };

  // Status from procurement engine
  const getStockStatus = (part) => {
    const s = part.status || '';
    if (s === 'out_of_stock' || part.stock_quantity === 0)
      return { class: 'bg-red-900/30 text-red-400',    label: 'Out of Stock' };
    if (s === 'reorder_required' || part.stock_quantity <= part.reorder_level)
      return { class: 'bg-orange-900/30 text-orange-400', label: 'Reorder Required' };
    if (s === 'low_stock' || part.stock_quantity <= part.minimum_stock)
      return { class: 'bg-yellow-900/30 text-yellow-400', label: 'Low Stock' };
    return { class: 'bg-green-900/30 text-green-400', label: 'In Stock' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold text-industrial-text">Spare Parts Inventory</h1>
          <p className="text-industrial-text-muted mt-1">Manage equipment spare parts and inventory</p>
        </div>
        <button
          onClick={() => handleOpenModal('add')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Part
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-industrial-text-muted" />
          <input
            type="text"
            placeholder="Search parts..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            className="input-industrial pl-10"
          />
        </div>
        
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={lowStockOnly}
            onChange={(e) => { setLowStockOnly(e.target.checked); setPage(1); }}
            className="w-4 h-4 rounded border-industrial-border bg-industrial-bg text-orange-500 focus:ring-orange-500"
          />
          <span className="text-industrial-text-muted">Low stock only</span>
        </label>
      </div>

      {/* Parts Table */}
      <div className="industrial-card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full"></div>
          </div>
        ) : parts.length === 0 ? (
          <div className="text-center py-12">
            <Package className="w-16 h-16 mx-auto text-industrial-text-muted opacity-50" />
            <p className="text-industrial-text-muted mt-4">No spare parts found</p>
            <button
              onClick={() => handleOpenModal('add')}
              className="btn-primary mt-4"
            >
              Add Your First Part
            </button>
          </div>
        ) : (
          <>
            <table className="industrial-table">
              <thead>
                <tr>
                  <th>Part Name</th>
                  <th>Part Number</th>
                  <th>Category</th>
                  <th>Stock</th>
                  <th>Min Stock</th>
                  <th>Reorder At</th>
                  <th>Unit Cost</th>
                  <th>Lead Time</th>
                  <th>Supplier</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {parts.slice((page - 1) * pageSize, page * pageSize).map((part) => {
                  const stockStatus = getStockStatus(part);
                  return (
                    <tr key={part.part_id}>
                      <td className="font-medium">{part.part_name}</td>
                      <td className="font-mono text-sm text-industrial-text-muted">{part.part_number || '-'}</td>
                      <td className="text-industrial-text-muted">{part.category || '-'}</td>
                      <td className="font-mono text-lg font-bold text-white">{part.stock_quantity}</td>
                      <td className="font-mono text-sm text-yellow-400">{part.minimum_stock ?? '-'}</td>
                      <td className="font-mono text-sm text-orange-400">{part.reorder_level ?? '-'}</td>
                      <td className="font-mono text-sm text-green-400">
                        {part.unit_cost ? `₹${part.unit_cost.toLocaleString('en-IN')}` : '—'}
                      </td>
                      <td className="text-industrial-text-muted">
                        {part.lead_time_days > 0 ? `${part.lead_time_days} days` : '-'}
                      </td>
                      <td className="text-industrial-text-muted">{part.supplier || '-'}</td>
                      <td>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${stockStatus.class}`}>
                          {stockStatus.label}
                        </span>
                      </td>
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button onClick={() => handleOpenModal('edit', part)}
                            className="p-2 text-blue-400 hover:bg-blue-500/20 rounded transition-colors">
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDeleteClick(part.part_id)}
                            className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            
            {/* Pagination */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-industrial-border">
              <span className="text-sm text-industrial-text-muted">
                Showing {parts.length} records
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
                  disabled={parts.length < pageSize}
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
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="industrial-card w-full max-w-lg mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-heading font-semibold">
                {modalMode === 'add' ? 'Add Spare Part' : 'Edit Part'}
              </h2>
              <button onClick={handleCloseModal} className="text-industrial-text-muted hover:text-industrial-text">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Row 1: Part Name + Part Number */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Part Name *</label>
                  <input type="text" name="part_name" value={formData.part_name}
                    onChange={handleInputChange} className="input-industrial" required placeholder="e.g. Deep Groove Ball Bearing" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Part Number</label>
                  <input type="text" name="part_number" value={formData.part_number}
                    onChange={handleInputChange} className="input-industrial" placeholder="e.g. B6205" />
                </div>
              </div>

              {/* Row 2: Category + Unit Cost (₹) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Category</label>
                  <select name="category" value={formData.category} onChange={handleInputChange} className="input-industrial">
                    {['Bearings','Seals','Filters','Electrical','Couplings','Cooling','Consumables','Hydraulics','Belts','General'].map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Unit Cost (₹) *</label>
                  <input type="number" name="unit_cost" value={formData.unit_cost}
                    onChange={handleInputChange} className="input-industrial" min="0" step="0.01"
                    required placeholder="e.g. 4275" />
                </div>
              </div>

              {/* Row 3: Stock Qty + Min Stock + Reorder Level */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Current Stock *</label>
                  <input type="number" name="stock_quantity" value={formData.stock_quantity}
                    onChange={handleInputChange} className="input-industrial" min="0" required />
                  <p className="text-[10px] text-slate-500 mt-0.5">How many in warehouse</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Min Stock *</label>
                  <input type="number" name="minimum_stock" value={formData.minimum_stock}
                    onChange={handleInputChange} className="input-industrial" min="0" required />
                  <p className="text-[10px] text-slate-500 mt-0.5">Low stock alert level</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Reorder Level *</label>
                  <input type="number" name="reorder_level" value={formData.reorder_level}
                    onChange={handleInputChange} className="input-industrial" min="0" required />
                  <p className="text-[10px] text-slate-500 mt-0.5">Trigger reorder at this qty</p>
                </div>
              </div>

              {/* Row 4: Supplier + Lead Time */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Supplier</label>
                  <input type="text" name="supplier" value={formData.supplier}
                    onChange={handleInputChange} className="input-industrial" placeholder="e.g. SKF Bearings" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-industrial-text-muted mb-1">Lead Time (days)</label>
                  <input type="number" name="lead_time_days" value={formData.lead_time_days}
                    onChange={handleInputChange} className="input-industrial" min="0"
                    placeholder="e.g. 7" />
                  <p className="text-[10px] text-slate-500 mt-0.5">Days to receive after ordering</p>
                </div>
              </div>

              {/* Row 5: Storage Location */}
              <div>
                <label className="block text-sm font-medium text-industrial-text-muted mb-1">Storage Location</label>
                <input type="text" name="location" value={formData.location}
                  onChange={handleInputChange} className="input-industrial" placeholder="e.g. Warehouse A, Shelf 3" />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">
                  {modalMode === 'add' ? 'Add Part' : 'Save Changes'}
                </button>
                <button type="button" onClick={handleCloseModal} className="btn-industrial flex-1">Cancel</button>
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
              <h3 className="text-xl font-heading font-semibold mb-2">Delete Part</h3>
              <p className="text-industrial-text-muted mb-6">
                Are you sure you want to delete this spare part? This action cannot be undone.
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

export default SpareParts;