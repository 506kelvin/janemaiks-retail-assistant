import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Package, AlertTriangle, TrendingUp, ShoppingCart, ArrowRight, MessageSquare, Store } from 'lucide-react';
import { analyticsApi, inventoryApi } from '../services/api';
import StatCard from '../components/StatCard';
import Card, { CardHeader } from '../components/Card';
import Badge from '../components/Badge';
import { DashboardSkeleton, TimelineSkeleton } from '../components/LoadingSkeleton';

function ActivityTimeline({ transactions, chats }) {
  const items = [
    ...(transactions || []).map((t) => ({
      id: `txn-${t.id}`,
      type: 'transaction',
      label: t.type === 'add' ? 'Stock Added' : t.type === 'deduct' ? 'Stock Deducted' : 'Stock Adjusted',
      detail: `${t.quantity} units`,
      time: t.created_at,
      color: t.type === 'add' ? 'bg-status-success' : t.type === 'deduct' ? 'bg-status-low' : 'bg-status-warning',
    })),
    ...(chats || []).map((c) => ({
      id: `chat-${c.id}`,
      type: 'chat',
      label: 'AI Query',
      detail: c.query,
      time: c.created_at,
      color: 'bg-primary-500',
    })),
  ].sort((a, b) => new Date(b.time || 0) - new Date(a.time || 0)).slice(0, 8);

  if (items.length === 0) {
    return <p className="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">No recent activity</p>;
  }

  return (
    <div className="timeline">
      {items.map((item) => (
        <div key={item.id} className="timeline-item">
          <div className={`timeline-dot ${item.color}`} />
          <div className="timeline-time">
            {item.time ? new Date(item.time).toLocaleDateString('en-KE', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''}
          </div>
          <div className="timeline-content mt-0.5">
            <span className="font-medium text-gray-900 dark:text-dark-text">{item.label}</span>
            {item.type === 'chat' ? (
              <span className="text-gray-500 ml-1">&mdash; {item.detail}</span>
            ) : (
              <span className="text-gray-500 ml-1">{item.detail}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lowStock, setLowStock] = useState([]);

  useEffect(() => {
    Promise.all([
      analyticsApi.dashboard(),
      inventoryApi.list(true),
    ])
      .then(([dash, inv]) => {
        setData(dash.data);
        setLowStock(inv.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;

  const stockValue = data?.total_stock_value || 0;
  const dailyProfit = data?.daily_profit || 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-dark-text">Welcome back to JaneMaiks</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">JaneMaiks Inventory Overview — real-time shop performance</p>
        </div>
        <Link to="/chatbot" className="btn-primary">
          <MessageSquare size={16} />
          JaneMaiks AI Assistant
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Package}
          label="Total Products"
          value={data?.total_products || 0}
          color="primary"
          trend={`${data?.total_inactive || 0} inactive`}
          subtitle="Registered products"
          onClick={() => navigate('/products')}
        />
        <StatCard
          icon={AlertTriangle}
          label="Low Stock Items"
          value={data?.low_stock_count || 0}
          color="red"
          trend={data?.low_stock_count > 0 ? 'Needs attention' : 'All stocked'}
          trendUp={data?.low_stock_count === 0}
        />
        <StatCard
          icon={TrendingUp}
          label="Est. Daily Profit"
          value={`KSh ${Math.round(dailyProfit).toLocaleString()}`}
          color="green"
          trend={dailyProfit > 0 ? 'Based on actual margins' : 'No profit data'}
          trendUp={dailyProfit > 0}
        />
        <StatCard
          icon={ShoppingCart}
          label="Today's Activity"
          value={data?.today_transactions || 0}
          color="amber"
          trend={data?.today_transactions > 0 ? 'Transactions today' : 'No activity yet'}
          trendUp={data?.today_transactions > 0}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Categories */}
        <Card className="lg:col-span-1">
          <CardHeader title="JaneMaiks Categories" subtitle={`${data?.categories?.length || 0} product categories`} />
          {data?.categories?.length > 0 ? (
            <div className="space-y-3">
              {data.categories.map((cat) => {
                const total = data.categories.reduce((s, c) => s + c.count, 0);
                const pct = ((cat.count / total) * 100).toFixed(0);
                return (
                  <div key={cat.name}>
                    <div className="flex items-center justify-between text-sm mb-1.5">
                      <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">{cat.name}</span>
                      <span className="text-xs text-gray-400">{cat.count} items</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 dark:bg-dark-surface rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary-500 transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-4 text-center">No categories yet</p>
          )}
        </Card>

        {/* Activity Feed */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="JaneMaiks Activity"
            subtitle="Latest stock movements and AI queries"
            action={
              <Link to="/analytics" className="text-xs text-primary-500 hover:text-primary-600 font-medium inline-flex items-center gap-1">
                View All <ArrowRight size={12} />
              </Link>
            }
          />
          {loading ? <TimelineSkeleton /> : (
            <ActivityTimeline
              transactions={data?.recent_transactions}
              chats={data?.recent_chats}
            />
          )}
        </Card>
      </div>

      {/* Low Stock Alerts */}
      {lowStock.length > 0 && (
        <Card>
          <CardHeader
            title="JaneMaiks Low Stock Alerts"
            subtitle={`${lowStock.length} product${lowStock.length > 1 ? 's' : ''} below threshold`}
            action={
              <Link to="/products" className="text-xs text-primary-500 hover:text-primary-600 font-medium inline-flex items-center gap-1">
                Manage Stock <ArrowRight size={12} />
              </Link>
            }
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {lowStock.slice(0, 6).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-xl bg-status-low/5 border border-status-low/10"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-dark-text truncate">{item.product_name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {item.quantity_available} remaining / {item.low_stock_threshold} threshold
                  </p>
                </div>
                <Badge variant="low">Low</Badge>
              </div>
            ))}
          </div>
          {lowStock.length > 6 && (
            <p className="text-xs text-gray-400 mt-3 text-center">
              +{lowStock.length - 6} more low stock items
            </p>
          )}
        </Card>
      )}

      {/* No low stock message */}
      {lowStock.length === 0 && (
        <Card className="text-center">
          <div className="py-4">
            <div className="w-12 h-12 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-3">
              <Store size={24} className="text-status-success" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-dark-text">All Items Well Stocked at JaneMaiks</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">No low stock alerts at this time</p>
          </div>
        </Card>
      )}
    </div>
  );
}
