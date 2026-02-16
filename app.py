# Copula-Risk-Visualizer
import React, { useState, useEffect, useMemo } from 'react';
import { CopulaType, DataPoints, Dimension, MarginalType, SimulationParams } from './types';
import { generateData } from './utils/math';

// Declare Plotly from CDN
declare const Plotly: any;

const App: React.FC = () => {
  // --- State ---
  const [params, setParams] = useState<SimulationParams>({
    n: 1000,
    d: 2,
    marginal: MarginalType.NORMAL,
    copula: CopulaType.GAUSSIAN,
    rho: 0.5,
    theta: 2.0,
  });

  const [data, setData] = useState<DataPoints | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Derived state for 3D mode
  const is3D = params.d >= 3;

  // --- Simulation Effect ---
  useEffect(() => {
    // Debounce slightly to avoid freezing on rapid slider movement
    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);
      // Use setTimeout to allow UI to render loading state
      setTimeout(() => {
        try {
            const result = generateData(params);
            setData(result);
        } catch (e: any) {
            console.error("Simulation error:", e);
            setError(e.message || "An error occurred during simulation.");
        } finally {
            setLoading(false);
        }
      }, 10);
    }, 300);

    return () => clearTimeout(timer);
  }, [params]);

  // --- Plotting Effect ---
  useEffect(() => {
    if (!data) return;
    if (!Plotly) return;

    try {
        const commonLayout = {
          margin: { t: 30, b: 30, l: 30, r: 30 },
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(255,255,255,0.05)',
          font: { color: '#e2e8f0' },
          showlegend: false,
        };

        const markerConfig = {
          size: 3,
          opacity: Math.max(0.1, Math.min(0.8, 1000 / params.n)), // Adjust opacity based on N
          color: '#38bdf8', // Sky 400
          line: { width: 0 }
        };

        // --- 1. Uniform Copula Plot ---
        const uniformTrace = {
          type: is3D ? 'scatter3d' : 'scatter',
          mode: 'markers',
          x: data.uniform.map(row => row[0]),
          y: data.uniform.map(row => row[1]),
          z: is3D ? data.uniform.map(row => row[2]) : undefined,
          marker: markerConfig,
        };

        const uniformLayout: any = {
          ...commonLayout,
          title: `Copula Space (Uniform) ${params.d}D`,
        };

        if (is3D) {
          uniformLayout.scene = {
            xaxis: { title: 'U1', range: [0, 1] },
            yaxis: { title: 'U2', range: [0, 1] },
            zaxis: { title: 'U3', range: [0, 1] },
          };
        } else {
          uniformLayout.xaxis = { title: 'U1', range: [0, 1] };
          uniformLayout.yaxis = { title: 'U2', range: [0, 1] };
        }

        Plotly.react('plot-uniform', [uniformTrace], uniformLayout, { responsive: true, displayModeBar: true });

        // --- 2. Marginal Space Plot ---
        const marginalTrace = {
          type: is3D ? 'scatter3d' : 'scatter',
          mode: 'markers',
          x: data.marginal.map(row => row[0]),
          y: data.marginal.map(row => row[1]),
          z: is3D ? data.marginal.map(row => row[2]) : undefined,
          marker: { ...markerConfig, color: '#f472b6' }, // Pink 400
        };

        // Determine ranges for marginals roughly
        let range: [number, number] | undefined = undefined;
        if (params.marginal === MarginalType.NORMAL) range = [-4, 4];
        if (params.marginal === MarginalType.STUDENT_T) range = [-6, 6];
        if (params.marginal === MarginalType.EXPONENTIAL) range = [-1.5, 5];

        const marginalLayout: any = {
          ...commonLayout,
          title: `Marginal Space (${params.marginal})`,
        };

        if (is3D) {
          marginalLayout.scene = {
            xaxis: { title: 'X1', range },
            yaxis: { title: 'X2', range },
            zaxis: { title: 'X3', range },
          };
        } else {
          marginalLayout.xaxis = { title: 'X1', range };
          marginalLayout.yaxis = { title: 'X2', range };
        }

        Plotly.react('plot-marginal', [marginalTrace], marginalLayout, { responsive: true, displayModeBar: true });
    } catch (e) {
        console.error("Plotting error", e);
    }

  }, [data, params.d, params.marginal, params.n, is3D]); // Added is3D dependency


  // --- Event Handlers ---
  const updateParam = <K extends keyof SimulationParams>(key: K, value: SimulationParams[K]) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="flex h-screen w-full overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-80 flex-shrink-0 bg-slate-800 border-r border-slate-700 overflow-y-auto p-6 flex flex-col gap-6">
        <header>
          <h1 className="text-xl font-bold text-white mb-2">Copula Visualizer</h1>
          <p className="text-xs text-slate-400">Quantitative Risk Management Tool</p>
        </header>

        {/* Input: N */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Simulations (N): {params.n}</label>
          <input 
            type="range" min="100" max="100000" step="100" 
            value={params.n} 
            onChange={(e) => updateParam('n', parseInt(e.target.value))}
            className="w-full accent-blue-500 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Input: D (Number of Marginals) */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Number of Marginals (d): {params.d}</label>
          <input 
            type="range" min="2" max="5" step="1" 
            value={params.d} 
            onChange={(e) => updateParam('d', parseInt(e.target.value))}
            className="w-full accent-blue-500 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Input: Copula Type */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Copula Type</label>
          <select 
            value={params.copula}
            onChange={(e) => updateParam('copula', e.target.value as CopulaType)}
            className="w-full bg-slate-700 text-slate-200 text-sm rounded-md p-2 border border-slate-600 focus:outline-none focus:border-blue-500"
          >
            {Object.values(CopulaType).map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* Input: Marginal Type */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Marginal Distribution</label>
          <select 
            value={params.marginal}
            onChange={(e) => updateParam('marginal', e.target.value as MarginalType)}
            className="w-full bg-slate-700 text-slate-200 text-sm rounded-md p-2 border border-slate-600 focus:outline-none focus:border-blue-500"
          >
            {Object.values(MarginalType).map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* Dependency Params */}
        <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-700 space-y-4">
          {params.copula === CopulaType.GUMBEL ? (
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300 flex justify-between">
                <span>Theta (θ)</span>
                <span>{params.theta.toFixed(1)}</span>
              </label>
              <input 
                type="range" min="1.0" max="10.0" step="0.1" 
                value={params.theta} 
                onChange={(e) => updateParam('theta', parseFloat(e.target.value))}
                className="w-full accent-green-500 h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-[10px] text-slate-400">Controls tail dependence</p>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300 flex justify-between">
                <span>Correlation (ρ)</span>
                <span>{params.rho.toFixed(2)}</span>
              </label>
              <input 
                type="range" min="-0.99" max="0.99" step="0.01" 
                value={params.rho} 
                onChange={(e) => updateParam('rho', parseFloat(e.target.value))}
                className="w-full accent-blue-500 h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-[10px] text-slate-400">Equicorrelated matrix parameter</p>
            </div>
          )}
        </div>

        {error && (
            <div className="p-2 bg-red-900/50 text-red-200 text-xs rounded border border-red-700">
                {error}
            </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col p-4 relative">
        {loading && (
          <div className="absolute inset-0 bg-slate-900/50 z-10 flex items-center justify-center backdrop-blur-sm">
            <div className="text-blue-400 font-semibold animate-pulse">Running Simulation...</div>
          </div>
        )}
        
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
          {/* Plot 1 */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-2 flex flex-col">
            {/* Key forces remount on 2D/3D switch to prevent Plotly WebGL context errors */}
            <div key={is3D ? 'u-3d' : 'u-2d'} id="plot-uniform" className="w-full h-full min-h-[300px]" />
          </div>
          
          {/* Plot 2 */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-2 flex flex-col">
            {/* Key forces remount on 2D/3D switch */}
            <div key={is3D ? 'm-3d' : 'm-2d'} id="plot-marginal" className="w-full h-full min-h-[300px]" />
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
