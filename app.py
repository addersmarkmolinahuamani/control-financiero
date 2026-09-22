import React, { useState, useEffect, useMemo } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Plus, CreditCard, TrendingUp, TrendingDown, Wallet, Calendar, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

// Credenciales directas de Supabase (las mismas de tu Streamlit)
const SUPABASE_URL = "https://uylnumfofwykwjamwtwk.supabase.co";
const SUPABASE_KEY = "sb_publishable_-F-3L3EmsN2DGdQ3xLvKgQ_0_DFq1CY";

// Diccionarios y categorías base
const NOMBRES_MESES = {
  "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
  "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
  "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
};

const base_egresos = ["ana", "casa", "comida", "cuotas", "educación", "gustos", "movilidad", "padres", "salud", "trabajo", "vestimenta", "otros"];
const base_ingresos = ["sunass", "cas", "gratificación", "cobro de deuda", "otros"];
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#f43f5e', '#84cc16', '#0ea5e9', '#d946ef'];

const formatoMesEspanol = (codigo) => {
  if (codigo === "Consolidado Total") return codigo;
  try {
    const [anio, mes] = codigo.split("-");
    return `${NOMBRES_MESES[mes] || mes} ${anio}`;
  } catch {
    return codigo;
  }
};

const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

const formatCurrency = (value) => `S/ ${Number(value).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function ControlFinanciero() {
  const [movimientos, setMovimientos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Estado del formulario
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [tipo, setTipo] = useState('Egreso');
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0]);
  const [categoria, setCategoria] = useState('');
  const [monto, setMonto] = useState('');
  const [detalle, setDetalle] = useState('');

  // Estado del filtro
  const [selectedMonth, setSelectedMonth] = useState('Consolidado Total');

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/movimientos?select=*&order=fecha.desc`, {
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`
        }
      });
      if (!res.ok) throw new Error('Error de conexión con la base de datos');
      const data = await res.json();
      setMovimientos(data);

      // Auto-seleccionar el mes actual si existe en los registros
      const currentMonth = new Date().toISOString().slice(0, 7);
      const uniqueMonths = [...new Set(data.map(d => d.fecha?.slice(0, 7)).filter(Boolean))];
      if (uniqueMonths.includes(currentMonth) && selectedMonth === 'Consolidado Total') {
         setSelectedMonth(currentMonth);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (Number(monto) <= 0) {
      setError('El monto debe ser mayor a 0');
      return;
    }

    const payload = {
      fecha,
      tipo,
      categoria,
      detalle,
      monto: parseFloat(monto)
    };

    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/movimientos`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Error al guardar el registro en la nube');
      
      setSuccessMsg('¡Guardado al instante en la nube!');
      setMonto('');
      setDetalle('');
      setIsFormOpen(false);
      fetchData(); // Refrescar los datos tras guardar
      
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
    }
  };

  const { catsEgreso, catsIngreso } = useMemo(() => {
    const egsDB = movimientos.filter(m => m.tipo?.toLowerCase() === 'egreso').map(m => m.categoria?.toLowerCase());
    const ingsDB = movimientos.filter(m => m.tipo?.toLowerCase() === 'ingreso').map(m => m.categoria?.toLowerCase());
    
    return {
      catsEgreso: [...new Set([...base_egresos, ...egsDB])].filter(Boolean).map(capitalize).sort(),
      catsIngreso: [...new Set([...base_ingresos, ...ingsDB])].filter(Boolean).map(capitalize).sort()
    };
  }, [movimientos]);

  // Actualizar categoría por defecto al cambiar tipo de movimiento
  useEffect(() => {
    if (tipo === 'Egreso') setCategoria(catsEgreso[0] || capitalize(base_egresos[0]));
    else setCategoria(catsIngreso[0] || capitalize(base_ingresos[0]));
  }, [tipo, catsEgreso, catsIngreso]);

  const mesesDisponibles = useMemo(() => {
    const months = movimientos.map(m => m.fecha?.slice(0, 7)).filter(Boolean);
    return ['Consolidado Total', ...Array.from(new Set(months)).sort().reverse()];
  }, [movimientos]);

  const dfFiltrado = useMemo(() => {
    if (selectedMonth === 'Consolidado Total') return movimientos;
    return movimientos.filter(m => m.fecha?.startsWith(selectedMonth));
  }, [movimientos, selectedMonth]);

  const { ingresos, egresos, disponible, pieData } = useMemo(() => {
    let ing = 0;
    let egr = 0;
    const egsCats = {};
    
    dfFiltrado.forEach(m => {
      const val = Number(m.monto) || 0;
      if (m.tipo?.toLowerCase() === 'ingreso') {
        ing += val;
      } else if (m.tipo?.toLowerCase() === 'egreso') {
        egr += val;
        const cat = capitalize(m.categoria);
        egsCats[cat] = (egsCats[cat] || 0) + val;
      }
    });

    const pData = Object.entries(egsCats)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);

    return { ingresos: ing, egresos: egr, disponible: ing - egr, pieData: pData };
  }, [dfFiltrado]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        <header className="flex items-center justify-between bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 text-blue-600 rounded-xl">
              <CreditCard className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-slate-800 tracking-tight">Mi Control Financiero</h1>
              <p className="text-slate-500 text-sm mt-1">Gestión de ingresos y egresos en la nube</p>
            </div>
          </div>
          {loading && <Loader2 className="w-6 h-6 animate-spin text-blue-500" />}
        </header>

        {/* Notificaciones */}
        {error && (
          <div className="flex items-center space-x-2 bg-red-50 text-red-700 p-4 rounded-xl border border-red-100">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="flex items-center space-x-2 bg-emerald-50 text-emerald-700 p-4 rounded-xl border border-emerald-100">
            <CheckCircle2 className="w-5 h-5" />
            <span>{successMsg}</span>
          </div>
        )}

        <section className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden transition-all">
          <button 
            onClick={() => setIsFormOpen(!isFormOpen)}
            className="w-full flex justify-between items-center p-5 bg-slate-50 hover:bg-slate-100 transition-colors"
          >
            <div className="flex items-center space-x-2 text-slate-700 font-semibold">
              <Plus className="w-5 h-5" />
              <span>Ingresar Movimiento</span>
            </div>
            {isFormOpen ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
          </button>
          
          {isFormOpen && (
            <form onSubmit={handleSubmit} className="p-6 border-t border-slate-100">
              <div className="flex space-x-6 mb-6">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="radio" checked={tipo === 'Egreso'} onChange={() => setTipo('Egreso')} className="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                  <span className="font-medium text-slate-700">Egreso</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="radio" checked={tipo === 'Ingreso'} onChange={() => setTipo('Ingreso')} className="w-4 h-4 text-blue-600 focus:ring-blue-500" />
                  <span className="font-medium text-slate-700">Ingreso</span>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Fecha</label>
                  <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required 
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Categoría</label>
                  <select value={categoria} onChange={(e) => setCategoria(e.target.value)} 
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all">
                    {(tipo === 'Egreso' ? catsEgreso : catsIngreso).map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Monto (S/.)</label>
                  <input type="number" step="0.01" min="0" value={monto} onChange={(e) => setMonto(e.target.value)} required placeholder="0.00"
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Detalle</label>
                  <input type="text" value={detalle} onChange={(e) => setDetalle(e.target.value)} placeholder="Ej. Menú, pasaje, cuota..."
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" />
                </div>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button type="submit" className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm shadow-blue-200 transition-all active:scale-95">
                  Guardar en el acto
                </button>
              </div>
            </form>
          )}
        </section>

        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-center bg-white p-5 rounded-2xl shadow-sm border border-slate-100">
            <div className="flex items-center space-x-2 text-slate-700 mb-3 sm:mb-0">
              <Calendar className="w-5 h-5 text-blue-500" />
              <span className="font-semibold">Resumen Financiero</span>
            </div>
            <select 
              value={selectedMonth} 
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-medium min-w-[200px]"
            >
              {mesesDisponibles.map(m => (
                <option key={m} value={m}>{formatoMesEspanol(m)}</option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Ingresos</p>
                <p className="text-2xl font-bold text-emerald-600">{formatCurrency(ingresos)}</p>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-500 rounded-xl"><TrendingUp className="w-6 h-6" /></div>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Egresos</p>
                <p className="text-2xl font-bold text-rose-600">{formatCurrency(egresos)}</p>
              </div>
              <div className="p-3 bg-rose-50 text-rose-500 rounded-xl"><TrendingDown className="w-6 h-6" /></div>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Disponible</p>
                <p className={`text-2xl font-bold ${disponible >= 0 ? 'text-blue-600' : 'text-rose-600'}`}>
                  {formatCurrency(disponible)}
                </p>
              </div>
              <div className="p-3 bg-blue-50 text-blue-500 rounded-xl"><Wallet className="w-6 h-6" /></div>
            </div>
          </div>
        </section>

        {dfFiltrado.length > 0 && egresos > 0 && (
          <>
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Gráfico de Dona */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-bold text-slate-700 mb-6 text-center">Egresos por Categoría</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={4} dataKey="value">
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value)} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Medidor Egresos vs Ingresos (Gauge Alternativo) */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-center">
                <h3 className="text-lg font-bold text-slate-700 mb-8 text-center">Egresos vs Ingresos</h3>
                <div className="w-full max-w-md mx-auto space-y-4">
                  <div className="flex justify-between text-sm font-medium text-slate-600">
                    <span>Egresos: {formatCurrency(egresos)}</span>
                    <span>Ingresos: {formatCurrency(ingresos)}</span>
                  </div>
                  <div className="relative w-full h-5 bg-emerald-100 rounded-full overflow-hidden shadow-inner">
                    <div 
                      className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${egresos > ingresos ? 'bg-rose-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.min((egresos / (ingresos || 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="text-center text-sm font-bold text-slate-500">
                    {ingresos > 0 ? ((egresos / ingresos) * 100).toFixed(1) : (egresos > 0 ? 100 : 0)}% Consumido
                  </div>
                </div>
              </div>
            </section>

            {/* Gráfico de Barras */}
            <section className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h3 className="text-lg font-bold text-slate-700 mb-6">Total de Egresos por Categoría</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={pieData} margin={{ top: 10, right: 10, left: 20, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} angle={-45} textAnchor="end" />
                    <YAxis tickFormatter={(val) => `S/${val}`} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip cursor={{ fill: '#f1f5f9' }} formatter={(value) => formatCurrency(value)} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {pieData.map((entry, index) => (
                        <Cell key={`bar-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </>
        )}

        <section className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-6 border-b border-slate-100">
            <h3 className="text-lg font-bold text-slate-700">Movimientos del Periodo</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4">Fecha</th>
                  <th className="px-6 py-4">Tipo</th>
                  <th className="px-6 py-4">Categoría</th>
                  <th className="px-6 py-4">Detalle</th>
                  <th className="px-6 py-4 text-right">Monto</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {dfFiltrado.slice(0, 15).map((mov, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-slate-600">{mov.fecha?.split('T')[0] || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold tracking-wide ${
                        mov.tipo?.toLowerCase() === 'ingreso' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                      }`}>
                        {capitalize(mov.tipo)}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-700">{capitalize(mov.categoria)}</td>
                    <td className="px-6 py-4 text-slate-500 max-w-[200px] truncate" title={mov.detalle}>{mov.detalle || '-'}</td>
                    <td className="px-6 py-4 text-right font-bold text-slate-800">{formatCurrency(mov.monto)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {dfFiltrado.length === 0 && !loading && (
              <div className="text-center py-12 text-slate-500 flex flex-col items-center">
                <AlertCircle className="w-10 h-10 mb-3 text-slate-300" />
                <p>No hay movimientos registrados para {formatoMesEspanol(selectedMonth)}.</p>
              </div>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}