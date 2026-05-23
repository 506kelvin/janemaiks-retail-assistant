import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, ShoppingCart, DollarSign, Calendar, Check, X, Package, Search } from 'lucide-react';
import { salesApi, productApi } from '../services/api';
import Card, { CardHeader } from '../components/Card';
import StatCard from '../components/StatCard';
import { DashboardSkeleton } from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

function SaleRow({ item, index, products, onUpdate, onRemove }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const isManual = item.isManual;

  const filteredProducts = products.filter(
    (p) => p.name.toLowerCase().includes(searchTerm.toLowerCase()) && p.is_active !== false
  );

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleProductSelect = (product) => {
    onUpdate(index, {
      product_id: product.id,
      product_name: product.name,
      selling_price: product.retail_price || product.suggested_retail_price || 0,
      quantity: item.quantity || 1,
      isManual: false,
    });
    setSearchTerm(product.name);
    setShowDropdown(false);
  };

  const handleManualToggle = () => {
    onUpdate(index, {
      product_id: null,
      product_name: '',
      selling_price: 0,
      quantity: 1,
      isManual: !isManual,
    });
    setSearchTerm('');
  };

  const subtotal = (item.quantity || 0) * (item.selling_price || 0);

  return (
    <div className="card p-3 sm:p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1">
          {!isManual ? (
            <div className="relative" ref={dropdownRef}>
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  className="input-field pl-8 text-sm"
                  placeholder="Search product..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                />
              </div>
              {showDropdown && (
                <div className="absolute z-10 left-0 right-0 mt-1 bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-xl shadow-elevated max-h-48 overflow-y-auto">
                  {filteredProducts.length === 0 ? (
                    <p className="text-xs text-gray-400 p-3">No products found</p>
                  ) : (
                    filteredProducts.map((p) => (
                      <button
                        key={p.id}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-dark-surface transition-colors flex items-center justify-between"
                        onClick={() => handleProductSelect(p)}
                      >
                        <span className="font-medium text-gray-700 dark:text-gray-300">{p.name}</span>
                        <span className="text-xs text-gray-400">KSh {p.retail_price || p.suggested_retail_price || '—'}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          ) : (
            <input
              className="input-field text-sm"
              placeholder="Enter product name..."
              value={item.product_name}
              onChange={(e) => onUpdate(index, { product_name: e.target.value })}
            />
          )}
        </div>
        <button
          onClick={handleManualToggle}
          className="btn-ghost btn-sm text-xs whitespace-nowrap"
          title={isManual ? 'Select from products' : 'Type manually'}
        >
          {isManual ? <Package size={14} /> : <X size={14} />}
        </button>
        <button
          onClick={() => onRemove(index)}
          className="btn-ghost btn-sm text-status-low hover:bg-status-low/5"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className="input-label">Qty</label>
          <input
            type="number"
            className="input-field text-sm"
            min="1"
            step="1"
            value={item.quantity}
            onChange={(e) => {
              const val = Math.max(1, parseInt(e.target.value) || 1);
              onUpdate(index, { quantity: val });
            }}
          />
        </div>
        <div>
          <label className="input-label">Price (KSh)</label>
          <input
            type="number"
            className="input-field text-sm"
            min="0"
            step="0.5"
            value={item.selling_price}
            onChange={(e) => {
              const val = parseFloat(e.target.value) || 0;
              onUpdate(index, { selling_price: val });
            }}
          />
        </div>
        <div>
          <label className="input-label">Subtotal</label>
          <div className="h-10 flex items-center px-3 rounded-xl bg-gray-50 dark:bg-dark-surface border border-gray-200 dark:border-dark-border text-sm font-semibold text-gray-900 dark:text-dark-text">
            KSh {subtotal.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Sales() {
  const [items, setItems] = useState([
    { product_id: null, product_name: '', quantity: 1, selling_price: 0, isManual: false },
  ]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [todaySummary, setTodaySummary] = useState(null);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      productApi.list({ per_page: 100 }),
      salesApi.today(),
    ])
      .then(([prodRes, todayRes]) => {
        setProducts(prodRes.data || []);
        setTodaySummary(todayRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const refreshToday = () => {
    salesApi.today().then((res) => setTodaySummary(res.data)).catch(console.error);
  };

  const grandTotal = items.reduce((sum, item) => sum + (item.quantity || 0) * (item.selling_price || 0), 0);

  const handleUpdate = (index, updates) => {
    setItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, ...updates } : item))
    );
  };

  const handleRemove = (index) => {
    if (items.length === 1) return;
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAdd = () => {
    setItems((prev) => [
      ...prev,
      { product_id: null, product_name: '', quantity: 1, selling_price: 0, isManual: false },
    ]);
  };

  const handleSubmit = async () => {
    const validItems = items.filter(
      (item) => item.product_name.trim() && item.quantity > 0 && item.selling_price > 0
    );
    if (validItems.length === 0) {
      setError('Add at least one item with product name, quantity, and price.');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        items: validItems.map((item) => ({
          product_id: item.product_id || null,
          product_name: item.product_name.trim(),
          quantity: item.quantity,
          selling_price: item.selling_price,
        })),
      };
      const res = await salesApi.create(payload);
      setSuccess(`Sale recorded! Total: KSh ${res.data.total_amount.toLocaleString()}`);
      setItems([{ product_id: null, product_name: '', quantity: 1, selling_price: 0, isManual: false }]);
      refreshToday();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record sale. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <DashboardSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-dark-text">Daily Sales</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Record items sold and track daily revenue</p>
      </div>

      {/* Today's Summary */}
      {todaySummary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            icon={DollarSign}
            label="Today's Sales Total"
            value={`KSh ${(todaySummary.total_sales || 0).toLocaleString()}`}
            color="green"
            trend={todaySummary.total_sales > 0 ? 'Includes all transactions' : 'No sales yet'}
            trendUp={todaySummary.total_sales > 0}
          />
          <StatCard
            icon={ShoppingCart}
            label="Transactions"
            value={todaySummary.transaction_count || 0}
            color="primary"
            trend={`${todaySummary.item_count || 0} items sold`}
            trendUp={todaySummary.transaction_count > 0}
          />
          <StatCard
            icon={Calendar}
            label="Today's Date"
            value={new Date().toLocaleDateString('en-KE', { day: 'numeric', month: 'long', year: 'numeric' })}
            color="amber"
          />
        </div>
      )}

      {/* Success / Error Messages */}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-status-success/10 border border-status-success/20 text-status-success text-sm">
          <Check size={16} />
          {success}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-status-low/10 border border-status-low/20 text-status-low text-sm">
          <X size={16} />
          {error}
        </div>
      )}

      {/* Sales Entry */}
      <Card>
        <CardHeader
          title="New Sale"
          subtitle="Add items sold to record a new transaction"
        />
        <div className="space-y-3">
          {items.map((item, index) => (
            <SaleRow
              key={index}
              item={item}
              index={index}
              products={products}
              onUpdate={handleUpdate}
              onRemove={handleRemove}
            />
          ))}

          <button onClick={handleAdd} className="btn-ghost w-full py-3 border-2 border-dashed border-gray-200 dark:border-dark-border rounded-xl text-sm">
            <Plus size={16} />
            Add Another Item
          </button>
        </div>
      </Card>

      {/* Grand Total & Submit */}
      <div className="card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Grand Total</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-dark-text">
              KSh {grandTotal.toLocaleString()}
            </p>
          </div>
          <button
            onClick={handleSubmit}
            disabled={saving || grandTotal <= 0}
            className="btn-primary btn-lg w-full sm:w-auto"
          >
            {saving ? (
              <div className="spinner !w-5 !h-5" />
            ) : (
              <>
                <Check size={18} />
                Complete Sale
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
