import { useState, useEffect } from 'react';
import { Plus, Trash2, Search, SortAsc, Package, MessageSquare, X } from 'lucide-react';
import { requestedItemsApi } from '../services/api';
import Card, { CardHeader } from '../components/Card';
import EmptyState from '../components/EmptyState';
import { DashboardSkeleton } from '../components/LoadingSkeleton';

export default function RequestedItems() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('request_count');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemNotes, setNewItemNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetchItems = () => {
    setLoading(true);
    requestedItemsApi.list(search, sortBy)
      .then((res) => setItems(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchItems();
  }, [search, sortBy]);

  const handleAdd = async () => {
    const name = newItemName.trim();
    if (!name) return;

    setSaving(true);
    setError(null);
    try {
      await requestedItemsApi.create({ product_name: name, notes: newItemNotes.trim() || undefined });
      setNewItemName('');
      setNewItemNotes('');
      setShowAddForm(false);
      fetchItems();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add item');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await requestedItemsApi.delete(id);
      fetchItems();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateNotes = async (id, notes) => {
    try {
      await requestedItemsApi.update(id, { notes });
      fetchItems();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && items.length === 0) return <DashboardSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-dark-text">Requested Items</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Track products customers ask for that we don't currently stock
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary"
        >
          <Plus size={16} />
          {showAddForm ? 'Cancel' : 'New Request'}
        </button>
      </div>

      {/* Quick Add Form */}
      {showAddForm && (
        <Card>
          <CardHeader title="Record Requested Item" subtitle="Log a product a customer asked for" />
          <div className="space-y-3">
            <div>
              <label className="input-label">Product Name *</label>
              <input
                className="input-field"
                placeholder="e.g. Casio fx82ES"
                value={newItemName}
                onChange={(e) => setNewItemName(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="input-label">Notes (optional)</label>
              <textarea
                className="input-field min-h-[60px] resize-none"
                placeholder="Customer said, price, reason..."
                value={newItemNotes}
                onChange={(e) => setNewItemNotes(e.target.value)}
              />
            </div>
            {error && <p className="input-error-text">{error}</p>}
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowAddForm(false)} className="btn-ghost">Cancel</button>
              <button
                onClick={handleAdd}
                disabled={saving || !newItemName.trim()}
                className="btn-primary"
              >
                {saving ? <div className="spinner !w-4 !h-4" /> : <><Plus size={16} /> Record Request</>}
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Search & Sort */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input-field pl-9"
            placeholder="Search requested items..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('request_count')}
            className={`btn-sm ${sortBy === 'request_count' ? 'btn-primary' : 'btn-ghost'}`}
          >
            <SortAsc size={14} />
            Most Requested
          </button>
          <button
            onClick={() => setSortBy('name')}
            className={`btn-sm ${sortBy === 'name' ? 'btn-primary' : 'btn-ghost'}`}
          >
            <Package size={14} />
            Name
          </button>
        </div>
      </div>

      {/* Items List */}
      {loading ? (
        <DashboardSkeleton />
      ) : items.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No Requested Items"
          description="Products customers ask for that are not in stock will appear here."
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="card p-4 space-y-3 hover:shadow-card-hover transition-shadow"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-dark-text truncate">
                    {item.product_name}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800/30">
                      <Package size={10} />
                      {item.request_count} {item.request_count === 1 ? 'request' : 'requests'}
                    </span>
                    {item.last_requested_at && (
                      <span className="text-xs text-gray-400">
                        {new Date(item.last_requested_at).toLocaleDateString('en-KE', { month: 'short', day: 'numeric' })}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="btn-icon btn-ghost text-gray-400 hover:text-status-low flex-shrink-0"
                  title="Remove"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {item.notes && (
                <p className="text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-dark-surface rounded-lg p-2">
                  {item.notes}
                </p>
              )}

              <div className="pt-1">
                <textarea
                  className="w-full text-xs input-field min-h-[36px] resize-none"
                  placeholder="Add notes..."
                  defaultValue={item.notes || ''}
                  onBlur={(e) => {
                    const val = e.target.value.trim();
                    if (val !== (item.notes || '')) {
                      handleUpdateNotes(item.id, val || null);
                    }
                  }}
                  rows={1}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {items.length > 0 && (
        <p className="text-xs text-gray-400 text-center">
          {items.length} requested item{items.length !== 1 ? 's' : ''} tracked
        </p>
      )}
    </div>
  );
}
