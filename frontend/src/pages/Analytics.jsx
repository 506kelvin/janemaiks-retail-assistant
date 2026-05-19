import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Package, Activity, RefreshCw, AlertTriangle, ArrowUpDown, Store, BarChart3, PieChart } from 'lucide-react';
import { analyticsApi, pricingApi, productApi } from '../services/api';
import StatCard from '../components/StatCard';
import Card, { CardHeader, Divider } from '../components/Card';
import Badge from '../components/Badge';
import { DashboardSkeleton } from '../components/LoadingSkeleton';

function CategoryBar({ name, count, total, color = 'bg-primary-500' }) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700 dark:text-gray-300 capitalize flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${color}`} />
          {name}
        </span>
        <span className="text-xs text-gray-400">{count} items ({pct}%)</span>
      </div>
      <div className="w-full h-2 bg-gray-100 dark:bg-dark-surface rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

const categoryColors = [
  'bg-primary-500',
  'bg-secondary-500',
  'bg-accent-500',
  'bg-purple-500',
  'bg-pink-500',
  'bg-cyan-500',
  'bg-amber-500',
  'bg-indigo-500',
];

export default function Analytics() {
  const [data, setData] = useState(null);
  const [priceInsights, setPriceInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.dashboard(),
      loadPriceInsights(),
    ])
      .then(([dash]) => setData(dash.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadPriceInsights = async () => {
    try {
      const res = await productApi.list({ limit: 500 });
      const products = res.data;
      if (products.length === 0) return;

      const ids = products.map((p) => p.id).join(',');
      const priceRes = await pricingApi.batch(ids);
      const pricingData = priceRes.data.products;

      const lowMargin = pricingData.filter((p) => p.margin_warning);
      const manualOverride = pricingData.filter((p) => p.price_source === 'manual');
      const hasWholesale = pricingData.filter((p) => p.wholesale_selling_price);

      const totalProfitPerDay = pricingData.reduce((sum, p) => {
        if (p.profit_per_unit) {
          const stock = products.find((pr) => pr.id === p.product_id);
          return sum + (p.profit_per_unit * (stock?.quantity_available || 0));
        }
        return sum;
      }, 0);

      const priceDiff = pricingData.filter((p) => {
        if (p.suggested_retail_price && p.effective_retail_price) {
          return Math.abs(p.suggested_retail_price - p.effective_retail_price) > 0.01;
        }
        return false;
      });

      setPriceInsights({
        lowMargin, manualOverride, hasWholesale,
        totalProfitPerDay: Math.round(totalProfitPerDay),
        priceDiff,
      });
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <DashboardSkeleton />;

  const stockValue = data?.total_stock_value || 0;
  const accurateDailyProfit = priceInsights?.totalProfitPerDay || 0;
  const totalItems = data?.categories?.reduce((s, c) => s + c.count, 0) || 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-dark-text">JaneMaiks Analytics</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Profit analysis, pricing intelligence, and JaneMaiks business insights</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Package} label="JaneMaiks Products" value={data?.total_products || 0} color="primary"
          subtitle={`${priceInsights?.manualOverride?.length || 0} with manual pricing`} />
        <StatCard icon={DollarSign} label="JaneMaiks Daily Profit" value={`KSh ${accurateDailyProfit.toLocaleString()}`} color="green"
          trend="Based on actual profit margins" />
        <StatCard icon={TrendingUp} label="JaneMaiks Monthly Profit" value={`KSh ${(accurateDailyProfit * 30).toLocaleString()}`} color="purple"
          trend="30-day projection" />
        <StatCard icon={Activity} label="Today's Activity" value={data?.today_transactions || 0} color="amber"
          subtitle={`${priceInsights?.hasWholesale?.length || 0} products with wholesale`} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Categories Breakdown */}
        <Card>
          <CardHeader title="JaneMaiks Categories" subtitle={`${data?.categories?.length || 0} categories · ${totalItems} total items`} />
          {data?.categories?.length > 0 ? (
            <div className="space-y-4">
              {data.categories.map((cat, i) => (
                <CategoryBar
                  key={cat.name}
                  name={cat.name}
                  count={cat.count}
                  total={totalItems}
                  color={categoryColors[i % categoryColors.length]}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-gray-400">No categories data available</div>
          )}
        </Card>

        {/* Pricing Intelligence */}
        <Card>
          <CardHeader title="JaneMaiks Pricing Intelligence" subtitle="Margin analysis and pricing insights" />

          <div className="space-y-5">
            {/* Low Margin */}
            <div>
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <AlertTriangle size={14} className="text-status-low" />
                Low Margin Products ({priceInsights?.lowMargin?.length || 0})
              </h3>
              {priceInsights?.lowMargin?.length > 0 ? (
                <div className="space-y-1.5">
                  {priceInsights.lowMargin.slice(0, 5).map((p) => (
                    <div key={p.product_id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-status-low/5 border border-status-low/10 text-sm">
                      <span className="text-gray-700 dark:text-gray-300 truncate mr-2">{p.product_name}</span>
                      <span className="text-status-low font-medium whitespace-nowrap">KSh {p.profit_per_unit}/unit</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No low-margin products found</p>
              )}
            </div>

            <Divider />

            {/* Manual vs Suggested */}
            <div>
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ArrowUpDown size={14} className="text-primary-500" />
                Manual vs Suggested ({priceInsights?.priceDiff?.length || 0})
              </h3>
              {priceInsights?.priceDiff?.length > 0 ? (
                <div className="space-y-1.5">
                  {priceInsights.priceDiff.slice(0, 5).map((p) => (
                    <div key={p.product_id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-primary-50 dark:bg-primary-500/5 text-sm">
                      <span className="text-gray-700 dark:text-gray-300 truncate mr-2 flex-1">{p.product_name}</span>
                      <div className="flex gap-3 text-xs whitespace-nowrap">
                        <span className="text-gray-400">Suggested: <strong className="text-gray-700 dark:text-gray-300">KSh {p.suggested_retail_price?.toFixed(2)}</strong></span>
                        <span className="text-primary-600 dark:text-primary-400">Actual: <strong>KSh {p.effective_retail_price?.toFixed(2)}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">All prices match suggested values</p>
              )}
            </div>

            <Divider />

            {/* Wholesale Summary */}
            <div>
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Package size={14} className="text-secondary-500" />
                Wholesale Pricing ({priceInsights?.hasWholesale?.length || 0} products)
              </h3>
              {priceInsights?.hasWholesale?.length > 0 ? (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {priceInsights.hasWholesale.length} products have wholesale selling prices configured for B2B sales.
                </p>
              ) : (
                <p className="text-sm text-gray-400">No wholesale selling prices configured yet.</p>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <CardHeader title="JaneMaiks Activity" subtitle="Latest stock movements" />
          {data?.recent_transactions?.length > 0 ? (
            <div className="space-y-2">
              {data.recent_transactions.map((t) => (
                <div key={t.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 dark:border-dark-border/50 last:border-0">
                  <div className="flex items-center gap-3">
                    <Badge variant={t.type === 'add' ? 'success' : t.type === 'deduct' ? 'low' : 'warning'}>
                      {t.type}
                    </Badge>
                    <span className="text-sm text-gray-700 dark:text-gray-300">{t.quantity} units</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {t.created_at ? new Date(t.created_at).toLocaleDateString('en-KE', { month: 'short', day: 'numeric' }) : ''}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-gray-400">No recent transactions</div>
          )}
        </Card>

        {/* Stock Value Summary */}
        <Card>
          <CardHeader title="JaneMaiks Stock Value Summary" subtitle="At wholesale cost" />
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-gray-50 to-blue-50 dark:from-dark-surface dark:to-primary-500/5 border border-gray-100 dark:border-dark-border">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">JaneMaiks Total Inventory Value</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-dark-text mt-1">KSh {stockValue.toLocaleString()}</p>
              </div>
              <div className="w-14 h-14 rounded-2xl bg-primary-50 dark:bg-primary-500/10 flex items-center justify-center">
                <Store size={28} className="text-primary-500" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-status-low/5 border border-status-low/10">
                <p className="text-xs text-gray-500 dark:text-gray-400">Low Stock Items</p>
                <p className="text-xl font-bold text-status-low mt-1">{data?.low_stock_count || 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-gray-50 dark:bg-dark-surface border border-gray-100 dark:border-dark-border">
                <p className="text-xs text-gray-500 dark:text-gray-400">Inactive Products</p>
                <p className="text-xl font-bold text-gray-900 dark:text-dark-text mt-1">{data?.total_inactive || 0}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-green-50 dark:bg-green-500/5 border border-green-100 dark:border-green-500/10">
                <p className="text-xs text-gray-500 dark:text-gray-400">JaneMaiks Daily Profit</p>
                <p className="text-xl font-bold text-status-success mt-1">KSh {accurateDailyProfit.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-500/5 border border-purple-100 dark:border-purple-500/10">
                <p className="text-xs text-gray-500 dark:text-gray-400">JaneMaiks Monthly Profit</p>
                <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">KSh {(accurateDailyProfit * 30).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
