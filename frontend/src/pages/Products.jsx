import { useState, useEffect, useCallback } from 'react';
import { Plus, Edit2, Trash2, ChevronDown, ChevronUp, Package, AlertTriangle, DollarSign, Layers, TrendingUp, Filter, X, Save } from 'lucide-react';
import { productApi, inventoryApi, pricingApi } from '../services/api';
import Card, { CardHeader } from '../components/Card';
import Badge, { StockBadge, MarginBadge, PriceSourceBadge } from '../components/Badge';
import { Table, TableRow, TableCell, TableSkeleton } from '../components/Table';
import SearchBar from '../components/SearchBar';
import Modal from '../components/Modal';
import EmptyState from '../components/EmptyState';

const ROUNDING_OPTIONS = [
  { value: 'none', label: 'None' },
  { value: 'nearest_5', label: 'Nearest 5 (42.5 → 45)' },
  { value: 'nearest_10', label: 'Nearest 10 (42.5 → 40)' },
];

function ProductForm({ product, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: '', category: '', supplier: '',
    wholesale_price: '', quantity_in_package: 1, unit_type: 'piece',
    retail_price: '', profit_per_item: '', profit_margin_percent: '',
    package_cost_price: '', package_quantity: 1, package_unit_type: 'piece',
    wholesale_selling_price: '', actual_retail_price: '',
    profit_margin_per_unit: '', rounding_strategy: 'none',
    allow_manual_override: false,
    ...(product || {}),
  });

  const pkgCost = parseFloat(form.package_cost_price || form.wholesale_price || 0);
  const pkgQty = parseInt(form.package_quantity || form.quantity_in_package || 1);
  const unitCost = pkgQty > 0 ? (pkgCost / pkgQty) : 0;
  const margin = parseFloat(form.profit_margin_per_unit || form.profit_per_item || 0);
  const suggestedRetail = margin > 0 ? (unitCost + margin) : null;
  const roundingStrategy = form.rounding_strategy || 'none';
  const roundedPrice = suggestedRetail !== null
    ? (roundingStrategy === 'nearest_5' ? Math.round(suggestedRetail / 5) * 5
      : roundingStrategy === 'nearest_10' ? Math.round(suggestedRetail / 10) * 10
      : suggestedRetail)
    : null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      ...form,
      wholesale_price: parseFloat(form.wholesale_price || form.package_cost_price) || 0,
      quantity_in_package: parseInt(form.quantity_in_package || form.package_quantity) || 1,
      unit_type: form.unit_type || form.package_unit_type || 'piece',
      retail_price: form.allow_manual_override && form.actual_retail_price ? parseFloat(form.actual_retail_price) : null,
      profit_per_item: parseFloat(form.profit_margin_per_unit || form.profit_per_item) || null,
      profit_margin_percent: form.profit_margin_percent ? parseFloat(form.profit_margin_percent) : null,
      package_cost_price: parseFloat(form.package_cost_price || form.wholesale_price) || 0,
      package_quantity: parseInt(form.package_quantity || form.quantity_in_package) || 1,
      package_unit_type: form.package_unit_type || form.unit_type || 'piece',
      wholesale_selling_price: form.wholesale_selling_price ? parseFloat(form.wholesale_selling_price) : null,
      actual_retail_price: form.allow_manual_override && form.actual_retail_price ? parseFloat(form.actual_retail_price) : null,
      profit_margin_per_unit: parseFloat(form.profit_margin_per_unit || form.profit_per_item) || null,
      rounding_strategy: form.rounding_strategy || 'none',
      allow_manual_override: form.allow_manual_override || false,
    };
    onSave(data);
  };

  const handleChange = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm({ ...form, [key]: value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <Package size={16} /> Product Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="input-label">Product Name <span className="text-status-low">*</span></label>
            <input className="input-field" value={form.name} onChange={handleChange('name')} required />
          </div>
          <div>
            <label className="input-label">Category</label>
            <input className="input-field" value={form.category || ''} onChange={handleChange('category')} placeholder="e.g. Foodstuff" />
          </div>
          <div>
            <label className="input-label">Supplier</label>
            <input className="input-field" value={form.supplier || ''} onChange={handleChange('supplier')} placeholder="e.g. Bidco Africa" />
          </div>
          <div>
            <label className="input-label">Package Unit Type</label>
            <select className="input-field" value={form.package_unit_type || form.unit_type || 'piece'} onChange={handleChange('package_unit_type')}>
              {['piece','packet','bottle','box','kg','litre','bar','tin','tub','pair','loaf','tube','jar'].map(u => (
                <option key={u} value={u}>{u.charAt(0).toUpperCase() + u.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="divider" />

      {/* Package Buying Info */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <Layers size={16} /> Package Buying Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="input-label">Package Cost (KSh) <span className="text-status-low">*</span></label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.package_cost_price || form.wholesale_price || ''} onChange={handleChange('package_cost_price')} required />
          </div>
          <div>
            <label className="input-label">Qty per Package <span className="text-status-low">*</span></label>
            <input type="number" min="1" className="input-field" value={form.package_quantity || form.quantity_in_package || 1} onChange={handleChange('package_quantity')} />
          </div>
          <div>
            <label className="input-label">Wholesale Sell Price (KSh)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.wholesale_selling_price || ''} onChange={handleChange('wholesale_selling_price')} placeholder="B2B whole package price" />
            <p className="input-helper">Price to sell whole package to other shopkeepers</p>
          </div>
        </div>
      </div>

      {/* Real-time Calculation */}
      {pkgCost > 0 && pkgQty > 0 && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-500/5 dark:to-blue-500/5 rounded-xl border border-primary-100 dark:border-primary-500/10 p-4">
          <p className="text-xs font-semibold text-primary-600 dark:text-primary-400 mb-3 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
            JaneMaiks Live Pricing Preview
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-400">Unit Cost</p>
              <p className="text-sm font-bold text-gray-900 dark:text-dark-text">KSh {unitCost.toFixed(2)}</p>
            </div>
            {suggestedRetail !== null && (
              <>
                <div>
                  <p className="text-xs text-gray-400">Suggested Retail</p>
                  <p className="text-sm font-bold text-gray-900 dark:text-dark-text">KSh {suggestedRetail.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Rounded Price</p>
                  <p className="text-sm font-bold text-accent-500">KSh {roundedPrice.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Est. Profit / Unit</p>
                  <p className="text-sm font-bold text-status-success">KSh {margin.toFixed(2)}</p>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <div className="divider" />

      {/* Retail Pricing */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <TrendingUp size={16} /> Retail Pricing Configuration
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="input-label">Profit Margin per Unit (KSh)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.profit_margin_per_unit || form.profit_per_item || ''} onChange={handleChange('profit_margin_per_unit')} placeholder="e.g. 10" />
          </div>
          <div>
            <label className="input-label">Rounding Strategy</label>
            <select className="input-field" value={form.rounding_strategy || 'none'} onChange={handleChange('rounding_strategy')}>
              {ROUNDING_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex items-center gap-3 mt-4">
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={form.allow_manual_override || false} onChange={handleChange('allow_manual_override')} className="sr-only peer" />
            <div className="w-9 h-5 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-500" />
          </label>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Enable Manual Price Override</span>
        </div>
        {form.allow_manual_override && (
          <div className="mt-3">
            <label className="input-label">Actual Retail Price (KSh)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.actual_retail_price || form.retail_price || ''} onChange={handleChange('actual_retail_price')} placeholder="Set a fixed retail price" />
          </div>
        )}
      </div>

      <div className="divider" />

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
        <button type="submit" className="btn-primary">
          <Save size={16} />
          {product ? 'Update Product' : 'Add Product'}
        </button>
      </div>
    </form>
  );
}

export default function Products() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [inventory, setInventory] = useState({});
  const [prices, setPrices] = useState({});
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);
  const perPage = 10;

  const loadProducts = useCallback(async () => {
    try {
      const res = await productApi.list({ search: search || undefined });
      const prods = res.data;
      setProducts(prods);
      const invRes = await inventoryApi.list();
      const invMap = {};
      invRes.data.forEach((i) => { invMap[i.product_id] = i; });
      setInventory(invMap);
      if (prods.length > 0) {
        const ids = prods.map((p) => p.id).join(',');
        const priceRes = await pricingApi.batch(ids);
        const priceMap = {};
        priceRes.data.products.forEach((p) => { priceMap[p.product_id] = p; });
        setPrices(priceMap);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  const handleSave = async (data) => {
    try {
      if (editing) await productApi.update(editing.id, data);
      else await productApi.create(data);
      setShowForm(false);
      setEditing(null);
      loadProducts();
    } catch (err) {
      alert('Failed to save product');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this product?')) return;
    try { await productApi.delete(id); loadProducts(); } catch (err) { alert('Failed to delete'); }
  };

  const handleStockAction = async (productId, type) => {
    const qty = prompt(`Enter quantity to ${type}:`);
    if (!qty || isNaN(qty) || parseFloat(qty) <= 0) return;
    try {
      await inventoryApi.addTransaction({ product_id: productId, transaction_type: type, quantity: parseFloat(qty) });
      loadProducts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Transaction failed');
    }
  };

  const handleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sorted = [...products].sort((a, b) => {
    if (!sortKey) return 0;
    const av = a[sortKey] ?? 0; const bv = b[sortKey] ?? 0;
    if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  const paginated = sorted.slice((page - 1) * perPage, page * perPage);
  const totalPages = Math.ceil(sorted.length / perPage);

  const tableHeaders = [
    { label: 'Product', key: 'name', sortable: true, currentSort: { key: sortKey, dir: sortDir }, onSort: handleSort },
    { label: 'Category', key: 'category', sortable: true, currentSort: { key: sortKey, dir: sortDir }, onSort: handleSort },
    { label: 'Unit Cost', key: null },
    { label: 'Retail Price', key: null },
    { label: 'Profit', key: null },
    { label: 'Stock', key: null },
    { label: '', key: null },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-dark-text">JaneMaiks Products</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{products.length} products registered in the system</p>
        </div>
        <button onClick={() => { setEditing(null); setShowForm(true); }} className="btn-primary">
          <Plus size={16} />
          Add Product
        </button>
      </div>

      {/* Product Form Modal */}
      <Modal open={showForm} onClose={() => { setShowForm(false); setEditing(null); }} title={editing ? 'Edit Product' : 'New Product'} size="lg">
        <ProductForm product={editing} onSave={handleSave} onCancel={() => { setShowForm(false); setEditing(null); }} />
      </Modal>

      {/* Search */}
      <SearchBar
        value={search}
        onChange={(v) => { setSearch(v); setPage(1); }}
        placeholder="Search JaneMaiks products by name, category, or supplier..."
        className="max-w-md"
      />

      {/* Products Table */}
      {loading ? (
        <TableSkeleton rows={8} cols={7} />
      ) : products.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No products found"
          description="Add your first product to start managing pricing and inventory."
          action={<button onClick={() => { setEditing(null); setShowForm(true); }} className="btn-primary"><Plus size={16} /> Add Your First Product</button>}
        />
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden md:block">
            <Table headers={tableHeaders}>
              {paginated.map((p) => {
                const inv = inventory[p.id];
                const price = prices[p.id];
                const isLow = inv && inv.low_stock_threshold && inv.quantity_available <= inv.low_stock_threshold;
                const marginWarn = price?.margin_warning;
                const retailPrice = price?.effective_retail_price ?? price?.retail_price_per_unit;

                return (
                  <TableRow key={p.id} onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-500/10 dark:to-blue-500/10 flex items-center justify-center flex-shrink-0">
                          <Package size={16} className="text-primary-500" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 dark:text-dark-text truncate max-w-[200px]">{p.name}</p>
                          {p.supplier && <p className="text-xs text-gray-400 truncate">{p.supplier}</p>}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {p.category ? <Badge variant="secondary">{p.category}</Badge> : <span className="text-gray-300">—</span>}
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">KSh {price?.unit_cost_price?.toFixed(2) ?? (p.wholesale_price / p.quantity_in_package).toFixed(2)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900 dark:text-dark-text">KSh {retailPrice?.toFixed(2)}</span>
                        <PriceSourceBadge source={price?.price_source} />
                      </div>
                    </TableCell>
                    <TableCell>
                      {price?.profit_per_unit != null ? (
                        <div className="flex items-center gap-2">
                          <span className={`font-medium ${marginWarn ? 'text-status-low' : 'text-status-success'}`}>
                            KSh {price.profit_per_unit.toFixed(2)}
                          </span>
                          {marginWarn && <AlertTriangle size={14} className="text-status-low" />}
                        </div>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <StockBadge available={inv?.quantity_available ?? 0} threshold={inv?.low_stock_threshold} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <button onClick={() => handleStockAction(p.id, 'add')} className="btn-ghost btn-icon btn-sm" title="Add Stock">+</button>
                        <button onClick={() => { setEditing(p); setShowForm(true); }} className="btn-ghost btn-icon btn-sm" title="Edit"><Edit2 size={14} /></button>
                        <button onClick={() => handleDelete(p.id)} className="btn-ghost btn-icon btn-sm text-status-low hover:bg-status-low/10" title="Delete"><Trash2 size={14} /></button>
                        <button className="btn-ghost btn-icon btn-sm">
                          {expandedId === p.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </Table>
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4 px-4 pb-4">
                <p className="text-sm text-gray-400">Page {page} of {totalPages}</p>
                <div className="flex gap-1">
                  {Array.from({ length: totalPages }).map((_, i) => (
                    <button key={i} onClick={() => setPage(i + 1)}
                      className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${page === i + 1 ? 'bg-primary-500 text-white' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-dark-surface'}`}>
                      {i + 1}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {paginated.map((p) => {
              const inv = inventory[p.id];
              const price = prices[p.id];
              const isLow = inv && inv.low_stock_threshold && inv.quantity_available <= inv.low_stock_threshold;
              const marginWarn = price?.margin_warning;
              const retailPrice = price?.effective_retail_price ?? price?.retail_price_per_unit;

              return (
                <Card key={p.id} className="!p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 dark:text-dark-text text-sm truncate">{p.name}</h3>
                        {isLow && <Badge variant="low" dot>Low</Badge>}
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{p.category || '—'} {p.supplier ? `• ${p.supplier}` : ''}</p>
                    </div>
                    <div className="text-right flex-shrink-0 ml-2">
                      <p className="text-base font-bold text-primary-500">KSh {retailPrice?.toFixed(2)}</p>
                      <PriceSourceBadge source={price?.price_source} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                    <div>
                      <span className="text-gray-400">Unit Cost:</span>
                      <span className="font-medium ml-1">KSh {price?.unit_cost_price?.toFixed(2) ?? (p.wholesale_price / p.quantity_in_package).toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Profit:</span>
                      <span className={`font-medium ml-1 ${marginWarn ? 'text-status-low' : 'text-status-success'}`}>KSh {price?.profit_per_unit?.toFixed(2) || '—'}</span>
                    </div>
                    <div>
                      <StockBadge available={inv?.quantity_available ?? 0} threshold={inv?.low_stock_threshold} />
                    </div>
                  </div>

                  <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-dark-border">
                    <button onClick={() => handleStockAction(p.id, 'add')} className="btn-secondary btn-sm flex-1">+ Stock</button>
                    <button onClick={() => { setEditing(p); setShowForm(true); }} className="btn-secondary btn-sm flex-1"><Edit2 size={12} /> Edit</button>
                    <button onClick={() => handleDelete(p.id)} className="btn-danger btn-sm flex-1"><Trash2 size={12} /></button>
                  </div>
                </Card>
              );
            })}
            {totalPages > 1 && (
              <div className="flex justify-center gap-1 pt-2">
                {Array.from({ length: totalPages }).map((_, i) => (
                  <button key={i} onClick={() => setPage(i + 1)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${page === i + 1 ? 'bg-primary-500 text-white' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-dark-surface'}`}>
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
