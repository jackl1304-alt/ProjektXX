import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number | string;
  trend?: number;
  icon?: string;
  loading?: boolean;
  onClick?: () => void;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  trend = 0,
  icon = '📊',
  loading = false,
  onClick,
}) => {
  const isPositive = trend >= 0;
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
    return val.toString();
  };

  return (
    <div
      onClick={onClick}
      className={`glass-card relative group cursor-pointer animate-slide-up ${
        onClick ? 'hover:scale-105' : ''
      }`}
      style={{ animationDelay: '0.1s' }}
    >
      {/* Gradient Glow Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-transparent to-secondary/0 group-hover:from-primary/5 group-hover:to-secondary/5 rounded-xl transition-all duration-300" />

      <div className="relative z-10 flex justify-between items-start">
        <div className="flex-1">
          <p className="text-sm font-medium text-text-tertiary uppercase tracking-wider mb-2">
            {title}
          </p>

          {loading ? (
            <div className="mb-3">
              <div className="skeleton h-10 w-24 mb-2" />
            </div>
          ) : (
            <div className="flex items-baseline gap-2">
              <h3 className="text-4xl font-bold text-text-primary">
                {formatValue(value)}
              </h3>
              {trend !== 0 && (
                <div
                  className={`flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-lg ${
                    isPositive
                      ? 'text-success bg-success/10'
                      : 'text-error bg-error/10'
                  }`}
                >
                  {isPositive ? (
                    <TrendingUp size={16} />
                  ) : (
                    <TrendingDown size={16} />
                  )}
                  {Math.abs(trend)}%
                </div>
              )}
            </div>
          )}

          {!loading && (
            <p className="text-xs text-text-tertiary mt-3">
              {isPositive ? '↑' : '↓'} {Math.abs(trend)}% from last period
            </p>
          )}
        </div>

        {/* Icon */}
        <div className="text-5xl opacity-50 group-hover:opacity-75 transition-opacity duration-300">
          {icon}
        </div>
      </div>

      {/* Bottom Accent */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-secondary to-accent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-b-xl" />
    </div>
  );
};

export default StatsCard;
