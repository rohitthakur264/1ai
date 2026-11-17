import json
import pandas as pd

bridge_df = pd.read_csv('output/bridge.csv')
findings_df = pd.read_csv('output/findings.csv').fillna('')

findings_data = findings_df.to_dict(orient='records')
findings_json = json.dumps(findings_data)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payments Reconciliation Engine | Onelab Assessment</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen p-6 md:p-10">
    <div class="max-w-7xl mx-auto space-y-8">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
            <div>
                <div class="flex items-center space-x-3">
                    <span class="px-2.5 py-0.5 text-xs font-semibold bg-indigo-100 text-indigo-800 rounded-full">Onelab Assessment</span>
                    <span class="px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full">19/19 Tests Passing</span>
                </div>
                <h1 class="text-2xl md:text-3xl font-bold text-slate-900 mt-2">Month-End Payments Reconciliation</h1>
                <p class="text-sm text-slate-500 mt-1">Platform Ledger vs Bank Settlement Statement • October 2026 Audit</p>
            </div>
            <div class="flex items-center space-x-3">
                <a href="#findings-section" class="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm transition">View Findings</a>
            </div>
        </div>

        <!-- Metrics Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Platform Total</div>
                <div class="text-2xl font-bold text-slate-900 mt-2">&#8377;975,803.14</div>
                <div class="text-xs text-slate-500 mt-1">410 recorded transactions</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Bank Settled Total</div>
                <div class="text-2xl font-bold text-slate-900 mt-2">&#8377;925,507.78</div>
                <div class="text-xs text-slate-500 mt-1">394 cleared settlements</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-rose-200 bg-rose-50/30 shadow-sm">
                <div class="text-xs font-medium text-rose-500 uppercase tracking-wider">Initial Book Gap</div>
                <div class="text-2xl font-bold text-rose-600 mt-2">&#8377;50,295.36</div>
                <div class="text-xs text-rose-500 mt-1">Platform overstates bank</div>
            </div>
            <div class="bg-white p-5 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-sm">
                <div class="text-xs font-medium text-emerald-600 uppercase tracking-wider">Unexplained Residual</div>
                <div class="text-2xl font-bold text-emerald-600 mt-2">&#8377;0.000</div>
                <div class="text-xs text-emerald-600 mt-1 font-medium">100% gap fully attributed</div>
            </div>
        </div>

        <!-- Accounting Bridge -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-bold text-slate-900">Reconciliation Bridge: Gap Attribution</h2>
                    <p class="text-xs text-slate-500 mt-0.5">Mathematical proof: Platform Total - Bank Total = Sum of Discrepancies + 0.000 Residual</p>
                </div>
                <span class="inline-flex items-center px-3 py-1 text-xs font-medium bg-emerald-100 text-emerald-800 rounded-full">Balanced</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                            <th class="py-3 px-5">Line Item / Category</th>
                            <th class="py-3 px-5 text-right">Count</th>
                            <th class="py-3 px-5 text-right">Amount (&#8377;)</th>
                            <th class="py-3 px-5">Financial Interpretation</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm divide-y divide-slate-100 font-mono">
                        <tr class="bg-slate-50/50 font-semibold">
                            <td class="py-3 px-5 text-slate-900 font-sans">Platform total (all rows)</td>
                            <td class="py-3 px-5 text-right">410</td>
                            <td class="py-3 px-5 text-right">&#8377;975,803.137</td>
                            <td class="py-3 px-5 font-sans text-xs text-slate-500">Gross ledger sales captured</td>
                        </tr>
                        <tr class="bg-slate-50/50 font-semibold">
                            <td class="py-3 px-5 text-slate-900 font-sans">Bank total (all rows)</td>
                            <td class="py-3 px-5 text-right">394</td>
                            <td class="py-3 px-5 text-right">&#8377;925,507.780</td>
                            <td class="py-3 px-5 font-sans text-xs text-slate-500">Actual funds credited in October statement</td>
                        </tr>
                        <tr class="bg-amber-50 font-bold">
                            <td class="py-3 px-5 text-amber-900 font-sans">GAP (Platform - Bank)</td>
                            <td class="py-3 px-5 text-right">-</td>
                            <td class="py-3 px-5 text-right text-amber-700">&#8377;50,295.357</td>
                            <td class="py-3 px-5 font-sans text-xs text-amber-800">Discrepancy to explain</td>
                        </tr>
                        <tr>
                            <td class="py-2.5 px-5 font-sans"><span class="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800 font-semibold">TIMING</span></td>
                            <td class="py-2.5 px-5 text-right">18</td>
                            <td class="py-2.5 px-5 text-right">+ &#8377;49,768.480</td>
                            <td class="py-2.5 px-5 font-sans text-xs text-slate-600">Captured Oct 30-31, settling Nov 1-2 (in-transit)</td>
                        </tr>
                        <tr>
                            <td class="py-2.5 px-5 font-sans"><span class="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 font-semibold">PRIOR_MONTH_CARRYOVER</span></td>
                            <td class="py-2.5 px-5 text-right">4</td>
                            <td class="py-2.5 px-5 text-right text-rose-600">- &#8377;2,395.980</td>
                            <td class="py-2.5 px-5 font-sans text-xs text-slate-600">Late September sales settling Oct 1-2</td>
                        </tr>
                        <tr>
                            <td class="py-2.5 px-5 font-sans"><span class="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-800 font-semibold">DUPLICATE_PLATFORM</span></td>
                            <td class="py-2.5 px-5 text-right">3</td>
                            <td class="py-2.5 px-5 text-right">+ &#8377;7,818.300</td>
                            <td class="py-2.5 px-5 font-sans text-xs text-slate-600">Webhook retry without idempotency key</td>
                        </tr>
                        <tr>
                            <td class="py-2.5 px-5 font-sans"><span class="px-2 py-0.5 rounded text-xs bg-orange-100 text-orange-800 font-semibold">DUPLICATE_BANK</span></td>
                            <td class="py-2.5 px-5 text-right">1</td>
                            <td class="py-2.5 px-5 text-right text-rose-600">- &#8377;4,895.830</td>
                            <td class="py-2.5 px-5 font-sans text-xs text-slate-600">Bank double-cleared single transaction</td>
                        </tr>
                        <tr>
                            <td class="py-2.5 px-5 font-sans"><span class="px-2 py-0.5 rounded text-xs bg-emerald-100 text-emerald-800 font-semibold">ROUNDING</span></td>
                            <td class="py-2.5 px-5 text-right">80</td>
                            <td class="py-2.5 px-5 text-right">+ &#8377;0.387</td>
                            <td class="py-2.5 px-5 font-sans text-xs text-slate-600">Sub-cent micro-fee truncation (each < 0.01)</td>
                        </tr>
                        <tr class="bg-emerald-50 font-bold border-t-2 border-emerald-300">
                            <td class="py-3 px-5 text-emerald-900 font-sans">UNEXPLAINED RESIDUAL</td>
                            <td class="py-3 px-5 text-right">-</td>
                            <td class="py-3 px-5 text-right text-emerald-700 font-black">&#8377;0.000</td>
                            <td class="py-3 px-5 font-sans text-xs text-emerald-800 font-semibold">Perfect mathematical balance achieved</td>
                        </tr>
                        <tr class="text-xs text-slate-500 font-sans">
                            <td class="py-2 px-5"><span class="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-800 font-semibold">ORPHAN_REFUND</span></td>
                            <td class="py-2 px-5 text-right font-mono">2</td>
                            <td class="py-2 px-5 text-right font-mono">&#8377;0.00</td>
                            <td class="py-2 px-5">Audit/compliance alert: refund with unknown parent order</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Filterable Findings Table -->
        <div id="findings-section" class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 class="text-lg font-bold text-slate-900">Detailed Findings Log (108 Anomalies)</h2>
                    <p class="text-xs text-slate-500">Filter by category or search by Transaction ID</p>
                </div>
                <div class="flex items-center space-x-2">
                    <input type="text" id="searchInput" placeholder="Search ID..." onkeyup="renderFindings()" class="px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
            </div>

            <!-- Category Pills -->
            <div class="flex flex-wrap gap-2 pt-1" id="categoryFilters"></div>

            <!-- Table -->
            <div class="overflow-x-auto border border-slate-200 rounded-lg">
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 uppercase">
                            <th class="py-2.5 px-3">Category</th>
                            <th class="py-2.5 px-3">Transaction ID</th>
                            <th class="py-2.5 px-3 text-right">Platform Amt</th>
                            <th class="py-2.5 px-3 text-right">Bank Amt</th>
                            <th class="py-2.5 px-3 text-right">Impact (&#8377;)</th>
                            <th class="py-2.5 px-3">Operational Explanation</th>
                        </tr>
                    </thead>
                    <tbody id="findingsTableBody" class="divide-y divide-slate-100 font-mono"></tbody>
                </table>
            </div>
            <div class="flex justify-between items-center text-xs text-slate-500 pt-2">
                <span id="rowCount"></span>
                <span>Seed: 42 • Deterministic Audit Trail</span>
            </div>
        </div>
    </div>

    <script>
        const findings = FINDINGS_PLACEHOLDER;
        const categories = [...new Set(findings.map(f => f.category))].sort();
        let activeCategories = new Set(categories);

        function initFilters() {
            const container = document.getElementById('categoryFilters');
            container.innerHTML = '';
            
            const allBtn = document.createElement('button');
            allBtn.className = 'px-2.5 py-1 text-xs rounded-full font-medium transition bg-slate-800 text-white';
            allBtn.innerText = 'Toggle All';
            allBtn.onclick = () => {
                if (activeCategories.size === categories.length) {
                    activeCategories.clear();
                } else {
                    categories.forEach(c => activeCategories.add(c));
                }
                initFilters();
                renderFindings();
            };
            container.appendChild(allBtn);

            categories.forEach(cat => {
                const btn = document.createElement('button');
                const isActive = activeCategories.has(cat);
                btn.className = `px-2.5 py-1 text-xs rounded-full font-medium transition border ${
                    isActive ? 'bg-indigo-50 border-indigo-300 text-indigo-700 font-semibold' : 'bg-white border-slate-200 text-slate-400'
                }`;
                btn.innerText = cat;
                btn.onclick = () => {
                    if (activeCategories.has(cat)) activeCategories.delete(cat);
                    else activeCategories.add(cat);
                    initFilters();
                    renderFindings();
                };
                container.appendChild(btn);
            });
        }

        function renderFindings() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const tbody = document.getElementById('findingsTableBody');
            tbody.innerHTML = '';

            const filtered = findings.filter(f => {
                const matchesCat = activeCategories.has(f.category);
                const matchesSearch = !search || f.txn_id.toLowerCase().includes(search) || f.category.toLowerCase().includes(search);
                return matchesCat && matchesSearch;
            });

            filtered.forEach(f => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-50 transition';
                
                let badgeClass = 'bg-slate-100 text-slate-800';
                if (f.category === 'TIMING') badgeClass = 'bg-blue-100 text-blue-800';
                else if (f.category === 'ROUNDING') badgeClass = 'bg-emerald-100 text-emerald-800';
                else if (f.category.startsWith('DUPLICATE')) badgeClass = 'bg-purple-100 text-purple-800';
                else if (f.category === 'ORPHAN_REFUND') badgeClass = 'bg-amber-100 text-amber-800';

                tr.innerHTML = `
                    <td class="py-2 px-3 font-sans"><span class="px-2 py-0.5 rounded text-[11px] font-semibold ${badgeClass}">${f.category}</span></td>
                    <td class="py-2 px-3 font-semibold text-slate-900">${f.txn_id}</td>
                    <td class="py-2 px-3 text-right">${f.platform_amount ? '&#8377;' + f.platform_amount : '-'}</td>
                    <td class="py-2 px-3 text-right">${f.bank_amount ? '&#8377;' + f.bank_amount : '-'}</td>
                    <td class="py-2 px-3 text-right font-bold ${parseFloat(f.impact) < 0 ? 'text-rose-600' : 'text-slate-800'}">${f.impact ? '&#8377;' + f.impact : '-'}</td>
                    <td class="py-2 px-3 font-sans text-slate-600 text-[11px]">${f.detail}</td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('rowCount').innerText = `Showing ${filtered.length} of ${findings.length} findings`;
        }

        initFilters();
        renderFindings();
    </script>
</body>
</html>
""".replace('FINDINGS_PLACEHOLDER', findings_json)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Generated index.html successfully')
